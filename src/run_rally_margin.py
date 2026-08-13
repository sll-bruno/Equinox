"""Stress the segregated margin policy on a pre-declared historical BTC rally window."""
from pathlib import Path

import pandas as pd

from src.margin import MAINTENANCE_RATE
from src.run_baselines import PERP_TAKER_FEE_RATE, build, position_from_signal, strategies
from src.run_margin import run_scenarios

OUT = Path(__file__).resolve().parents[1] / "reports"
RALLY_START = "2023-10-01T00:00:00Z"
RALLY_END = "2024-09-01T00:00:00Z"  # exclusive; contains the 2023-24 rally and 2024 sell-offs


def breach_return(buffer_fraction):
    """Approximate rise-to-breach including perp entry and estimated close fees.

    This closed form assumes spot, perp and mark are equal at entry and excludes
    intervening funding. The full simulation uses observed prices and funding.
    """
    return (
        buffer_fraction - MAINTENANCE_RATE - 2 * PERP_TAKER_FEE_RATE
    ) / (
        1 + MAINTENANCE_RATE + PERP_TAKER_FEE_RATE
    )


def main():
    for old in OUT.glob("rally_margin_*.parquet"):
        old.unlink()
    frame = build(start=RALLY_START, end=RALLY_END)
    summary, _ = run_scenarios(output_prefix="rally_margin", frame=frame)
    always_on_position = position_from_signal(strategies(frame)["always_on"])
    entry_index = always_on_position[always_on_position.eq(1)].index[0]
    entry_perp_price = frame.loc[entry_index, "perp_last_open"]
    window_start_mark = frame.perp_mark_open.iloc[0]
    worst_adverse_short_excursion = frame.perp_mark_close.max() / entry_perp_price - 1
    summary["analysis_window_start_utc"] = pd.Timestamp(RALLY_START)
    summary["analysis_window_end_utc_exclusive"] = pd.Timestamp(RALLY_END)
    summary["mark_price_change_over_window"] = (
        frame.perp_mark_close.iloc[-1] / window_start_mark - 1
    )
    summary["worst_adverse_short_excursion"] = worst_adverse_short_excursion
    summary["policy_breach_rise_from_entry"] = summary.buffer_fraction.map(breach_return)
    summary.to_csv(OUT / "rally_margin_summary.csv", index=False)
    print(f"wrote {len(summary)} rally-margin scenarios to {OUT / 'rally_margin_summary.csv'}")
    print(f"worst_adverse_short_excursion={worst_adverse_short_excursion:.2%}")


if __name__ == "__main__":
    main()
