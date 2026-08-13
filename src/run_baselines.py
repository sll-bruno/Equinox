"""Point-in-time, no-HMM funding-carry baselines for the Bybit BTCUSDT pilot."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/normalized/bybit"
OUT = ROOT / "reports"

# Bybit non-VIP taker fees used by the V0 specification. Fees are applied to
# the value actually traded on each leg, never as a fixed 31 bp cycle charge.
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

    # Each entry deploys one unit of spot notional. The BTC quantity is fixed
    # until exit and is identical on the long-spot and short-perp legs.
    previous_position = ledger.position.shift(1).fillna(0)
    ledger["entry"] = ((ledger.position == 1) & (previous_position == 0)).astype(int)
    ledger["exit"] = ((ledger.position == 0) & (previous_position == 1)).astype(int)
    entry_quantity = (1 / ledger.spot_open).where(ledger.entry == 1)
    ledger["quantity_btc"] = entry_quantity.ffill().where(ledger.position == 1, 0.0)
    exit_quantity = ledger.quantity_btc.shift(1).where(ledger.exit == 1, 0.0).fillna(0)

    ledger["spot_entry_fee"] = (
        ledger.entry * ledger.quantity_btc * ledger.spot_open * SPOT_TAKER_FEE_RATE
    )
    ledger["perp_entry_fee"] = (
        ledger.entry * ledger.quantity_btc * ledger.perp_last_open * PERP_TAKER_FEE_RATE
    )
    ledger["spot_exit_fee"] = exit_quantity * ledger.spot_open * SPOT_TAKER_FEE_RATE
    ledger["perp_exit_fee"] = exit_quantity * ledger.perp_last_open * PERP_TAKER_FEE_RATE

    # An open final position is closed at the last available executable open.
    ledger["terminal_spot_exit_fee"] = 0.0
    ledger["terminal_perp_exit_fee"] = 0.0
    if ledger.position.iloc[-1] == 1:
        final_quantity = ledger.quantity_btc.iloc[-1]
        ledger.loc[ledger.index[-1], "terminal_spot_exit_fee"] = (
            final_quantity * ledger.spot_open.iloc[-1] * SPOT_TAKER_FEE_RATE
        )
        ledger.loc[ledger.index[-1], "terminal_perp_exit_fee"] = (
            final_quantity * ledger.perp_last_open.iloc[-1] * PERP_TAKER_FEE_RATE
        )

    ledger["spot_fees"] = (
        ledger.spot_entry_fee + ledger.spot_exit_fee + ledger.terminal_spot_exit_fee
    )
    ledger["perp_fees"] = (
        ledger.perp_entry_fee + ledger.perp_exit_fee + ledger.terminal_perp_exit_fee
    )
    ledger["total_fees"] = ledger.spot_fees + ledger.perp_fees

    # A t-settlement belongs to the position carried into t, i.e. the preceding interval [t-8h, t].
    ledger["funding_position_prior_interval"] = ledger.position.shift(1).fillna(0)
    funding_quantity = ledger.quantity_btc.shift(1).fillna(0)
    ledger["funding_cashflow"] = (
        ledger.funding_settled.fillna(0)
        * ledger.funding_position_prior_interval
        * funding_quantity
        * ledger.perp_mark_open
    )
    spot_change = ledger.spot_open.shift(-1) - ledger.spot_open
    perp_change = ledger.perp_last_open.shift(-1) - ledger.perp_last_open
    ledger["basis_pnl"] = (
        ledger.position * ledger.quantity_btc * (spot_change - perp_change)
    ).fillna(0)
    ledger["gross_pnl"] = ledger.funding_cashflow + ledger.basis_pnl
    ledger["net_pnl"] = ledger.gross_pnl - ledger.total_fees
    ledger["equity"] = 1 + ledger.net_pnl.cumsum()
    return ledger


def evaluate(x, name, signal):
    ledger = make_ledger(x, signal)
    terminal_fees = (
        ledger.terminal_spot_exit_fee.sum() + ledger.terminal_perp_exit_fee.sum()
    )
    row = {
        "strategy": name,
        "fee_model": "bybit_non_vip_taker_actual_traded_value",
        "spot_taker_fee_rate": SPOT_TAKER_FEE_RATE,
        "perp_taker_fee_rate": PERP_TAKER_FEE_RATE,
        "gross_return": ledger.gross_pnl.sum(),
        "net_return": ledger.net_pnl.sum(),
        "funding_return": ledger.funding_cashflow.sum(),
        "basis_pnl_return": ledger.basis_pnl.sum(),
        "spot_fee_return": ledger.spot_fees.sum(),
        "perp_fee_return": ledger.perp_fees.sum(),
        "total_fee_return": ledger.total_fees.sum(),
        "terminal_exit_fee_return": terminal_fees,
        "max_drawdown": max_drawdown(ledger.equity),
        "annualized_volatility": ledger.net_pnl.std() * (24 * 365) ** 0.5,
        "entries": ledger.entry.sum(),
        "exits_including_terminal": ledger.exit.sum() + ledger.terminal_exit_turnover.sum(),
        "turnover_events": ledger.turnover.sum(),
        "exposure": ledger.position.mean(),
    }
    ledger.to_parquet(OUT / f"pilot_{name}.parquet", index=False)
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
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
