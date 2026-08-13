# Pilot methodology

Universe: Bybit only, BTCUSDT spot and BTCUSDT linear perpetual. Decision features are observed at a closed one-hour candle; execution is the next candle open (`t+1`, UTC). All timestamps are UTC.

## Point-in-time and funding convention

The execution return on row `t` is `spot_open[t+1] / spot_open[t] - 1` minus the analogous **last-traded perp open** return. Thus, it represents a tradable open-to-open hedge return for a position initiated at `t` from a signal formed on the prior closed candle. All model features are lagged with `.shift(1)`.

A funding history observation at timestamp `t` is a settled outcome, not a same-time input. Bybit documents that a positive funding rate makes longs pay shorts and that a trader must hold a position at funding time to receive or pay it. The engine therefore credits `fundingRate[t]` only to the position carried into `t` (the position over `[t-8h, t]` for BTCUSDT's 8-hour interval), not to a position first opened at `t`. A positive rate is added to the short-perp carry P&L.

Mark price is used for the basis feature (`mark_close - spot_close`) and is reserved for a future margin/liquidation model. It is not an executable fill in the baseline P&L. `reports/hedge_mark_vs_last.csv` quantifies the alternate mark-price hedge return only as a comparator.

## Costs and terminal close

Every strategy is closed at the final timestamp. A complete cycle means opening **and** closing both legs: buy then sell spot, and sell then buy the linear perpetual. The full-cycle assumptions are:

- `fee_only`: 31 bp = two half-turns, each with VIP-0 taker spot fee of 10 bp plus linear-perp taker fee of 5.5 bp.
- `base`: 50 bp = documented 31 bp fees plus a 19 bp non-historical aggregate buffer for spread/slippage.
- `stress`: 100 bp = documented 31 bp fees plus a 69 bp adverse-execution buffer.

One isolated entry or exit is half a cycle and costs half the stated number. These are assumptions, not observed historical spreads. No performance claim is valid until the collector, validations and analysis run successfully.

The unavailable `Auditoria_Dados_Bybit_BTCUSDT.md` was not used; this fact must remain in the research log until the source is recovered.
