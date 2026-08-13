"""Evaluate the small, pre-declared funding hysteresis grid through the margin policy."""
from pathlib import Path

import pandas as pd

from src.dead_zone import DEAD_ZONE_GRID, MIN_HOLD_HOURS, dead_zone_signal
from src.run_baselines import build, strategies
from src.run_margin import run_scenarios

OUT = Path(__file__).resolve().parents[1] / "reports"


def oos_metrics(ledger, start):
    sample = ledger[ledger.timestamp_utc >= start]
    equity = 1 + sample.net_return.fillna(0).cumsum()
    return {
        "oos_net_return": equity.iloc[-1] - 1,
        "oos_max_drawdown": (equity / equity.cummax() - 1).min(),
        "oos_margin_violation_count": int(sample.margin_violation.sum()),
        "oos_worst_maintenance_to_equity": sample.maintenance_to_equity.max(),
    }


def main():
    for old in OUT.glob("dead_zone_*.parquet"):
        old.unlink()
    x = build()
    signals = {}
    for policy in DEAD_ZONE_GRID:
        for hold_hours in MIN_HOLD_HOURS:
            name = f"{policy['name']}_hold_{hold_hours}h"
            signals[name] = dead_zone_signal(
                x, policy["entry_threshold"], policy["exit_threshold"], hold_hours
            )
    summary, ledgers = run_scenarios(signals, output_prefix="dead_zone")
    oos_start = x.timestamp_utc.iloc[len(x) // 2]
    records = []
    baseline_signals = {"always_on": strategies(x)["always_on"]}
    _, baseline_ledgers = run_scenarios(baseline_signals, output_prefix="dead_zone_baseline")
    for row in summary.to_dict("records"):
        key = (row["strategy"], row["buffer_scenario"], row["cost_scenario"])
        base_key = ("always_on", row["buffer_scenario"], row["cost_scenario"])
        metrics = oos_metrics(ledgers[key], oos_start)
        baseline = oos_metrics(baseline_ledgers[base_key], oos_start)
        risk_improved = (
            metrics["oos_max_drawdown"] > baseline["oos_max_drawdown"]
            or metrics["oos_margin_violation_count"] < baseline["oos_margin_violation_count"]
            or metrics["oos_worst_maintenance_to_equity"] < baseline["oos_worst_maintenance_to_equity"]
        )
        records.append(
            {
                **row,
                "oos_start_utc": oos_start,
                **metrics,
                "always_on_oos_net_return": baseline["oos_net_return"],
                "always_on_oos_max_drawdown": baseline["oos_max_drawdown"],
                "risk_improved_vs_always_on_oos": risk_improved,
                "net_not_destroyed_vs_always_on_oos": metrics["oos_net_return"]
                >= baseline["oos_net_return"],
            }
        )
    result = pd.DataFrame(records)
    result["candidate_by_predeclared_oos_rule"] = (
        result.risk_improved_vs_always_on_oos & result.net_not_destroyed_vs_always_on_oos
    )
    result.to_csv(OUT / "dead_zone_summary.csv", index=False)
    print(f"wrote {len(result)} dead-zone scenarios to {OUT / 'dead_zone_summary.csv'}")
    print(f"oos_start_utc={oos_start.isoformat()}")


if __name__ == "__main__":
    main()
