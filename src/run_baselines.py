"""Point-in-time, no-HMM funding-carry baselines for the Bybit BTCUSDT pilot."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/normalized/bybit"
OUT = ROOT / "reports"

# Basis points per complete cycle: open and close both spot and perp legs.
COSTS_BPS = {"fee_only": 31, "base": 50, "stress": 100}


def read(name):
    return pd.read_parquet(DATA / f"{name}.parquet").sort_values("timestamp_utc")


def compounded_return(returns):
    return (1 + returns.fillna(0)).prod() - 1


def max_drawdown(equity):
    return (equity / equity.cummax() - 1).min()


def build():
    spot = read("spot_candles")[["timestamp_utc", "open", "close"]].rename(
        columns={"open": "spot_open", "close": "spot_close"}
    )
    perp = read("perp_candles")[["timestamp_utc", "open", "close"]].rename(
        columns={"open": "perp_last_open", "close": "perp_last_close"}
    )
    mark = read("mark_price")[["timestamp_utc", "open", "close"]].rename(
        columns={"open": "perp_mark_open", "close": "perp_mark_close"}
    )
    x = spot.merge(perp, on="timestamp_utc").merge(mark, on="timestamp_utc")
    for column in x.columns[1:]:
        x[column] = pd.to_numeric(x[column])

    # Mark is deliberately not used for execution P&L. It is a basis and future-margin input.
    x["basis_mark_vs_spot"] = (x.perp_mark_close - x.spot_close) / x.spot_close
    x["spot_execution_return"] = x.spot_open.pct_change().shift(-1)
    x["perp_last_execution_return"] = x.perp_last_open.pct_change().shift(-1)
    x["perp_mark_return_comparator"] = x.perp_mark_open.pct_change().shift(-1)
    x["hedge_execution_return_last"] = x.spot_execution_return - x.perp_last_execution_return
    x["hedge_return_mark_comparator"] = x.spot_execution_return - x.perp_mark_return_comparator

    funding = read("funding")[["timestamp_utc", "fundingRate"]].rename(
        columns={"fundingRate": "funding_settled"}
    )
    funding["funding_settled"] = pd.to_numeric(funding["funding_settled"])
    x = x.merge(funding, on="timestamp_utc", how="left")

    # Every feature is lagged. A settlement is an outcome, never a same-timestamp signal.
    x["last_settled_funding"] = x.funding_settled.ffill().shift(1)
    x["vol_24h"] = x.spot_execution_return.rolling(24).std().shift(1)
    x["basis_lag"] = x.basis_mark_vs_spot.shift(1)
    return x


def funding_rebalance_signal(x, rule):
    """Update only after a settlement; the evaluator executes its decision at t+1."""
    updates = pd.Series(float("nan"), index=x.index, dtype="float64")
    at_settlement = x.funding_settled.notna()
    updates.loc[at_settlement] = rule.loc[at_settlement].astype(int)
    return updates.ffill().fillna(0).astype(bool)


def strategies(x):
    threshold = 0.00005  # 0.5 bp/settlement; fixed candidate rule, not optimized.
    return {
        "always_on": pd.Series(True, index=x.index),
        "positive_last_settled_funding": funding_rebalance_signal(x, x.last_settled_funding > 0),
        "funding_above_threshold": funding_rebalance_signal(x, x.last_settled_funding > threshold),
        "positive_funding_low_vol_or_basis": funding_rebalance_signal(
            x,
            (x.last_settled_funding > 0)
            & ((x.vol_24h < x.vol_24h.expanding().median()) | (x.basis_lag > 0)),
        ),
    }


def turnover(position):
    """Half-turn units: entry/exit or a 0↔1 change each count as one half cycle."""
    trading = position.diff().abs().fillna(position.abs())
    terminal_exit = pd.Series(0.0, index=position.index)
    terminal_exit.iloc[-1] = position.iloc[-1]
    return trading, terminal_exit, trading + terminal_exit


def make_ledger(x, signal):
    ledger = x.copy()
    # signal t -> trade at open t+1 -> position[t] earns t→t+1 execution P&L.
    ledger["position"] = signal.fillna(False).astype(int).shift(1).fillna(0)
    ledger["trading_turnover"], ledger["terminal_exit_turnover"], ledger["turnover"] = turnover(ledger.position)
    # A t-settlement belongs to the position carried into t, i.e. the preceding interval [t-8h, t].
    ledger["funding_position_prior_interval"] = ledger.position.shift(1).fillna(0)
    ledger["funding_cashflow"] = (
        ledger.funding_settled.fillna(0) * ledger.funding_position_prior_interval
    )
    # There is no t→t+1 price move after the final timestamp, but an open position still pays exit cost.
    ledger["execution_hedge_return"] = (
        ledger.position * ledger.hedge_execution_return_last
    ).fillna(0)
    ledger["gross_return"] = ledger.execution_hedge_return + ledger.funding_cashflow

    # Reproduces the published pilot for transparent old-versus-new comparison only.
    ledger["legacy_funding_cashflow"] = ledger.position * ledger.funding_settled.fillna(0)
    # The old output's terminal NaN discarded both its terminal price P&L and a same-row settlement.
    legacy_execution = ledger.position * ledger.hedge_execution_return_last
    ledger["legacy_gross_return"] = legacy_execution + ledger.legacy_funding_cashflow
    return ledger


def evaluate(x, name, signal):
    ledger = make_ledger(x, signal)
    rows = []
    for scenario, cycle_bps in COSTS_BPS.items():
        half_turn_cost = cycle_bps / 20_000
        ledger["cost_return"] = ledger.turnover * half_turn_cost
        ledger["net_return"] = ledger.gross_return - ledger.cost_return
        ledger["legacy_net_return"] = ledger.legacy_gross_return - ledger.trading_turnover * half_turn_cost
        ledger["net_return_without_terminal_exit"] = ledger.gross_return - ledger.trading_turnover * half_turn_cost
        ledger["equity"] = (1 + ledger.net_return.fillna(0)).cumprod()
        net = ledger.net_return.dropna()
        rows.append(
            {
                "strategy": name,
                "cost_scenario": scenario,
                "cycle_cost_bps": cycle_bps,
                "legacy_published_net_return_no_terminal_exit": compounded_return(ledger.legacy_net_return),
                "net_return_without_terminal_exit": compounded_return(ledger.net_return_without_terminal_exit),
                "net_return_with_terminal_exit": compounded_return(ledger.net_return),
                "terminal_exit_impact": compounded_return(ledger.net_return)
                - compounded_return(ledger.net_return_without_terminal_exit),
                "legacy_published_gross_return": compounded_return(ledger.legacy_gross_return),
                "gross_return": compounded_return(ledger.gross_return),
                "funding_return": ledger.funding_cashflow.sum(),
                "execution_hedge_return": ledger.execution_hedge_return.sum(),
                "max_drawdown": max_drawdown(ledger.equity),
                "annualized_volatility": net.std() * (24 * 365) ** 0.5,
                "turnover_without_terminal_exit": ledger.trading_turnover.sum(),
                "terminal_exit_turnover": ledger.terminal_exit_turnover.sum(),
                "turnover_events": ledger.turnover.sum(),
                "exposure": ledger.position.mean(),
            }
        )
        ledger.to_parquet(OUT / f"pilot_{name}_{scenario}.parquet", index=False)
    return rows


def hedge_mark_vs_last(x):
    last = compounded_return(x.hedge_execution_return_last)
    mark = compounded_return(x.hedge_return_mark_comparator)
    return {"last_return": last, "mark_return": mark, "mark_minus_last": mark - last}


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("pilot_*.parquet"):
        old.unlink()
    x = build()
    result = []
    for name, signal in strategies(x).items():
        result += evaluate(x, name, signal)
    summary = pd.DataFrame(result)
    summary.to_csv(OUT / "baseline_summary.csv", index=False)
    pd.DataFrame([hedge_mark_vs_last(x)]).to_csv(OUT / "hedge_mark_vs_last.csv", index=False)
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.4%}"))


if __name__ == "__main__":
    main()
