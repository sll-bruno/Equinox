"""Run conservative margin-buffer scenarios on the existing no-HMM baselines."""
from pathlib import Path

import pandas as pd

from src.margin import MAINTENANCE_RATE, UNIT_NOTIONAL_USDT, simulate_margin_policy
from src.run_baselines import (
    COST_SCENARIOS,
    build,
    compounded_return,
    make_ledger_from_position,
    max_drawdown,
    position_from_signal,
    strategies,
)

OUT = Path(__file__).resolve().parents[1] / "reports"
BUFFERS = {"buffer_25pct": 0.25, "buffer_50pct": 0.50, "buffer_100pct": 1.00}


def apply_costs(ledger, fee_multiplier):
    output = ledger.copy()
    output["fee_multiplier"] = fee_multiplier
    output["spread_slippage_proxy_return"] = output.total_fee_return * (fee_multiplier - 1)
    output["cost_return"] = output.total_fee_return * fee_multiplier
    output["net_return"] = output.gross_return - output.cost_return
    output["equity"] = (1 + output.net_return.fillna(0)).cumprod()
    return output


def summarize(ledger, margin, strategy, buffer_name, buffer_fraction, cost_name, fee_multiplier):
    active_margin = margin.margin_balance_usdt.dropna()
    violations = margin[margin.margin_violation]
    return {
        "strategy": strategy,
        "buffer_scenario": buffer_name,
        "buffer_fraction": buffer_fraction,
        "cost_scenario": cost_name,
        "fee_multiplier": fee_multiplier,
        "return_on_notional": compounded_return(ledger.net_return),
        "return_on_capital_employed": compounded_return(ledger.net_return) / (1 + buffer_fraction),
        "capital_employed_usdt_per_100_notional": UNIT_NOTIONAL_USDT * (1 + buffer_fraction),
        "funding_received_paid_return": ledger.funding_cashflow.sum(),
        "funding_received_paid_usdt_per_100_notional": ledger.funding_cashflow.sum() * UNIT_NOTIONAL_USDT,
        "execution_hedge_return": ledger.execution_hedge_return.sum(),
        "execution_hedge_usdt_per_100_notional": ledger.execution_hedge_return.sum() * UNIT_NOTIONAL_USDT,
        "actual_fee_return": ledger.total_fee_return.sum(),
        "spread_slippage_proxy_return": ledger.spread_slippage_proxy_return.sum(),
        "cost_return": ledger.cost_return.sum(),
        "cost_usdt_per_100_notional": ledger.cost_return.sum() * UNIT_NOTIONAL_USDT,
        "max_drawdown": max_drawdown(ledger.equity),
        "worst_margin_balance_usdt": active_margin.min() if len(active_margin) else float("nan"),
        "worst_maintenance_to_equity": margin.maintenance_to_equity.max(),
        "margin_violation_count": int(margin.margin_violation.sum()),
        "first_violation_observed_at_utc": (
            violations.timestamp_utc.iloc[0] + pd.Timedelta(hours=1) if len(violations) else pd.NaT
        ),
        "effective_exposure": ledger.position.mean(),
        "turnover_events": ledger.turnover.sum(),
    }


def run_scenarios(signal_map=None, output_prefix="margin", frame=None):
    OUT.mkdir(exist_ok=True)
    x = build() if frame is None else frame.copy()
    signal_map = strategies(x) if signal_map is None else signal_map
    rows = []
    ledgers = {}
    for strategy, signal in signal_map.items():
        target = position_from_signal(signal)
        for buffer_name, buffer_fraction in BUFFERS.items():
            margin = simulate_margin_policy(x, target, buffer_fraction)
            ledger = make_ledger_from_position(x, margin.effective_position)
            for cost_name, fee_multiplier in COST_SCENARIOS.items():
                priced = apply_costs(ledger, fee_multiplier)
                margin_only = margin[[column for column in margin if column not in priced.columns]]
                result = pd.concat([priced, margin_only], axis=1)
                key = (strategy, buffer_name, cost_name)
                ledgers[key] = result
                rows.append(
                    summarize(
                        priced, margin, strategy, buffer_name, buffer_fraction, cost_name, fee_multiplier
                    )
                )
                result.to_parquet(OUT / f"{output_prefix}_{strategy}_{buffer_name}_{cost_name}.parquet", index=False)
    return pd.DataFrame(rows), ledgers


def main():
    for old in OUT.glob("margin_*.parquet"):
        old.unlink()
    summary, _ = run_scenarios()
    summary.to_csv(OUT / "margin_summary.csv", index=False)
    print(f"wrote {len(summary)} margin scenarios to {OUT / 'margin_summary.csv'}")
    print(f"maintenance_rate_assumption={MAINTENANCE_RATE:.2%}")


if __name__ == "__main__":
    main()
