"""Stress the segregated margin policy on a pre-declared historical BTC rally window."""
from pathlib import Path

import pandas as pd

from src.margin import MAINTENANCE_RATE, UNIT_NOTIONAL_USDT
from src.run_baselines import build
from src.run_margin import run_scenarios

OUT = Path(__file__).resolve().parents[1] / "reports"
RALLY_START = "2023-10-01T00:00:00Z"
RALLY_END = "2024-09-01T00:00:00Z"  # exclusive; contains the 2023-24 rally and 2024 sell-offs


def breach_return(buffer_fraction):
    """Mark-price rise from entry that reaches the simplified maintenance policy."""
    buffer = UNIT_NOTIONAL_USDT * buffer_fraction
    return (buffer - MAINTENANCE_RATE * UNIT_NOTIONAL_USDT) / (
        UNIT_NOTIONAL_USDT * (1 + MAINTENANCE_RATE)
    )


def main():
    for old in OUT.glob("rally_margin_*.parquet"):
        old.unlink()
    frame = build(start=RALLY_START, end=RALLY_END)
    summary, _ = run_scenarios(output_prefix="rally_margin", frame=frame)
    entry_mark = frame.perp_mark_open.iloc[0]
    worst_adverse_short_excursion = frame.perp_mark_close.max() / entry_mark - 1
    summary["analysis_window_start_utc"] = pd.Timestamp(RALLY_START)
    summary["analysis_window_end_utc_exclusive"] = pd.Timestamp(RALLY_END)
    summary["mark_price_change_over_window"] = frame.perp_mark_close.iloc[-1] / entry_mark - 1
    summary["worst_adverse_short_excursion"] = worst_adverse_short_excursion
    summary["policy_breach_rise_from_entry"] = summary.buffer_fraction.map(breach_return)
    summary.to_csv(OUT / "rally_margin_summary.csv", index=False)
    print(f"wrote {len(summary)} rally-margin scenarios to {OUT / 'rally_margin_summary.csv'}")
    print(f"worst_adverse_short_excursion={worst_adverse_short_excursion:.2%}")


if __name__ == "__main__":
    main()
