# Pilot methodology

Universe: Bybit only, BTCUSDT spot and BTCUSDT linear perpetual. Decision features are observed at a closed one-hour candle; execution is the next candle open (`t+1`, UTC). All timestamps are UTC.

## Point-in-time and funding convention

The execution return on row `t` is `spot_open[t+1] / spot_open[t] - 1` minus the analogous **last-traded perp open** return. Thus, it represents a tradable open-to-open hedge return for a position initiated at `t` from a signal formed on the prior closed candle. All model features are lagged with `.shift(1)`.

A funding history observation at timestamp `t` is a settled outcome, not a same-time input. Bybit documents that a positive funding rate makes longs pay shorts and that a trader must hold a position at funding time to receive or pay it. The engine therefore credits `fundingRate[t]` only to the position carried into `t` (the position over `[t-8h, t]` for BTCUSDT's 8-hour interval), not to a position first opened at `t`. A positive rate is added to the short-perp carry P&L.

Mark price is used for the basis feature (`mark_close - spot_close`) and is reserved for a future margin/liquidation model. It is not an executable fill in the baseline P&L. `reports/hedge_mark_vs_last.csv` quantifies the alternate mark-price hedge return only as a comparator.

## Costs and terminal close

Every strategy is closed at the final timestamp. A complete cycle means opening **and** closing both legs: buy then sell spot, and sell then buy the linear perpetual.

V0 assumes Bybit non-VIP taker execution: 0.10% for spot and 0.055% for the linear perpetual. The engine does **not** subtract a fixed 31 bp cycle cost. For a fixed BTC quantity `q`, it charges every operation on its actual traded value:

`total fees = 0.001 q S0 + 0.001 q ST + 0.00055 q F0 + 0.00055 q FT`

Each entry is normalized to one unit of spot notional, so `q = 1 / S0`, and the same BTC quantity is held on both legs until exit. Funding cashflow is the settled funding rate times the carried BTC quantity and the contemporaneous perpetual mark price. Basis P&L is calculated directly as `q[(F0 - S0) - (FT - ST)]` through the sum of open-to-open price changes.

The V0 deliberately excludes spread, slippage, borrow, network and transfer fees, FX conversion, opportunity cost of capital, sophisticated margin modelling and taxes. No performance claim is valid until the collector, validations and analysis run successfully.

The unavailable `Auditoria_Dados_Bybit_BTCUSDT.md` was not used; this fact must remain in the research log until the source is recovered.
