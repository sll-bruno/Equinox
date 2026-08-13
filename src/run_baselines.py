"""Point-in-time, no-HMM funding-carry baselines for the Bybit BTCUSDT pilot."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/normalized/bybit"
OUT = ROOT / "reports"

# Bybit non-VIP taker rates used by the V0 fee specification.
SPOT_TAKER_FEE_RATE = 0.001
PERP_TAKER_FEE_RATE = 0.00055


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

    # Fee-only quantity tracking. Gross P&L, funding and basis calculations below
    # intentionally retain their original return-based implementation.
    previous_position = ledger.position.shift(1).fillna(0)
    ledger["entry"] = ((ledger.position == 1) & (previous_position == 0)).astype(int)
    ledger["exit"] = ((ledger.position == 0) & (previous_position == 1)).astype(int)
    entry_quantity = (1 / ledger.spot_open).where(ledger.entry == 1)
    fee_quantity = entry_quantity.ffill().where(ledger.position == 1, 0.0)
    exit_quantity = fee_quantity.shift(1).where(ledger.exit == 1, 0.0).fillna(0)

    ledger["spot_entry_fee_return"] = (
        ledger.entry * fee_quantity * ledger.spot_open * SPOT_TAKER_FEE_RATE
    )
    ledger["perp_entry_fee_return"] = (
        ledger.entry * fee_quantity * ledger.perp_last_open * PERP_TAKER_FEE_RATE
    )
    ledger["spot_exit_fee_return"] = exit_quantity * ledger.spot_open * SPOT_TAKER_FEE_RATE
    ledger["perp_exit_fee_return"] = exit_quantity * ledger.perp_last_open * PERP_TAKER_FEE_RATE
    ledger["terminal_spot_exit_fee_return"] = 0.0
    ledger["terminal_perp_exit_fee_return"] = 0.0
    if ledger.position.iloc[-1] == 1:
        final_quantity = fee_quantity.iloc[-1]
        ledger.loc[ledger.index[-1], "terminal_spot_exit_fee_return"] = (
            final_quantity * ledger.spot_open.iloc[-1] * SPOT_TAKER_FEE_RATE
        )
        ledger.loc[ledger.index[-1], "terminal_perp_exit_fee_return"] = (
            final_quantity * ledger.perp_last_open.iloc[-1] * PERP_TAKER_FEE_RATE
        )
    ledger["spot_fee_return"] = (
        ledger.spot_entry_fee_return
        + ledger.spot_exit_fee_return
        + ledger.terminal_spot_exit_fee_return
    )
    ledger["perp_fee_return"] = (
        ledger.perp_entry_fee_return
        + ledger.perp_exit_fee_return
        + ledger.terminal_perp_exit_fee_return
    )
    ledger["trading_fee_return"] = (
        ledger.spot_entry_fee_return
        + ledger.perp_entry_fee_return
        + ledger.spot_exit_fee_return
        + ledger.perp_exit_fee_return
    )
    ledger["total_fee_return"] = ledger.spot_fee_return + ledger.perp_fee_return

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
    ledger["net_return"] = ledger.gross_return - ledger.total_fee_return
    ledger["legacy_net_return"] = ledger.legacy_gross_return - ledger.trading_fee_return
    ledger["net_return_without_terminal_exit"] = ledger.gross_return - ledger.trading_fee_return
    ledger["equity"] = (1 + ledger.net_return.fillna(0)).cumprod()
    net = ledger.net_return.dropna()
    terminal_fee_return = (
        ledger.terminal_spot_exit_fee_return.sum()
        + ledger.terminal_perp_exit_fee_return.sum()
    )
    row = {
        "strategy": name,
        "fee_model": "bybit_non_vip_taker_actual_traded_value",
        "spot_taker_fee_rate": SPOT_TAKER_FEE_RATE,
        "perp_taker_fee_rate": PERP_TAKER_FEE_RATE,
        "legacy_published_net_return_no_terminal_exit": compounded_return(ledger.legacy_net_return),
        "net_return_without_terminal_exit": compounded_return(ledger.net_return_without_terminal_exit),
        "net_return_with_terminal_exit": compounded_return(ledger.net_return),
        "terminal_exit_impact": compounded_return(ledger.net_return)
        - compounded_return(ledger.net_return_without_terminal_exit),
        "legacy_published_gross_return": compounded_return(ledger.legacy_gross_return),
        "gross_return": compounded_return(ledger.gross_return),
        "funding_return": ledger.funding_cashflow.sum(),
        "execution_hedge_return": ledger.execution_hedge_return.sum(),
        "spot_fee_return": ledger.spot_fee_return.sum(),
        "perp_fee_return": ledger.perp_fee_return.sum(),
        "total_fee_return": ledger.total_fee_return.sum(),
        "terminal_exit_fee_return": terminal_fee_return,
        "max_drawdown": max_drawdown(ledger.equity),
        "annualized_volatility": net.std() * (24 * 365) ** 0.5,
        "turnover_without_terminal_exit": ledger.trading_turnover.sum(),
        "terminal_exit_turnover": ledger.terminal_exit_turnover.sum(),
        "turnover_events": ledger.turnover.sum(),
        "exposure": ledger.position.mean(),
    }
    ledger.to_parquet(OUT / f"pilot_{name}_fee_only.parquet", index=False)
    return [row]


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
