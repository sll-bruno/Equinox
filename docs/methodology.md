# Pilot methodology

Universe: Bybit only, BTCUSDT spot and BTCUSDT linear perpetual. Decision features are observed at a closed one-hour candle; execution is the next candle open (`t+1`, UTC). All timestamps are UTC.

## Point-in-time and funding convention

The execution return on row `t` is `spot_open[t+1] / spot_open[t] - 1` minus the analogous **last-traded perp open** return. Thus, it represents a tradable open-to-open hedge return for a position initiated at `t` from a signal formed on the prior closed candle. All model features are lagged with `.shift(1)`.

A funding history observation at timestamp `t` is a settled outcome, not a same-time input. Bybit documents that a positive funding rate makes longs pay shorts and that a trader must hold a position at funding time to receive or pay it. The engine therefore credits `fundingRate[t]` only to the position carried into `t` (the position over `[t-8h, t]` for BTCUSDT's 8-hour interval), not to a position first opened at `t`. A positive rate is added to the short-perp carry P&L.

Mark price is used for the basis feature (`mark_close - spot_close`) and for the separate collateral policy below. It is not an executable fill in the baseline P&L. `reports/hedge_mark_vs_last.csv` quantifies the alternate mark-price hedge return only as a comparator.

## Costs and terminal close

Every strategy is closed at the final timestamp. A complete cycle means opening **and** closing both legs: buy then sell spot, and sell then buy the linear perpetual. The full-cycle assumptions are:

- `fee_only`: 31 bp = two half-turns, each with VIP-0 taker spot fee of 10 bp plus linear-perp taker fee of 5.5 bp.
- `base`: 50 bp = documented 31 bp fees plus a 19 bp non-historical aggregate buffer for spread/slippage.
- `stress`: 100 bp = documented 31 bp fees plus a 69 bp adverse-execution buffer.

One isolated entry or exit is half a cycle and costs half the stated number. These are assumptions, not observed historical spreads. No performance claim is valid until the collector, validations and analysis run successfully.

The unavailable `Auditoria_Dados_Bybit_BTCUSDT.md` was not used; this fact must remain in the research log until the source is recovered.

## Conservative collateral policy

`src.margin` adds a deliberately simplified, segregated-account policy. It is **not** a reconstruction of historic Bybit liquidation rules. The pilot does not contain the historical risk-limit tier, exact initial/maintenance-margin schedule, fee-on-liquidation, insurance-fund process, or any transfer mechanics needed to make that claim.

Each simulated trade has equal spot and perp quantities (`q` BTC long spot and `q` BTC short linear perp), normalized so that the initial matched notional is US$100. Results scale linearly with that normalisation for a given return path. The spot account contains the US$100 spot purchase; the perp account starts with a separate USDT buffer of 25%, 50%, or 100% of that notional (US$25, US$50, or US$100). Spot profit is never transferred to this margin account, even if BTC rises while the hedge is economically close to flat.

The short is marked hourly using `perp_mark_close`:

`short_mark_pnl = q * (entry_mark - current_mark)`.

The initial buffer plus accumulated funding and this marked P&L form margin equity. The policy uses a 5% maintenance requirement of current marked short notional. This is intentionally conservative and rounded: it is a stress guardrail in the absence of historical, tier-specific Bybit margin data, not an asserted Bybit maintenance rate. We report `maintenance / margin_equity` as margin use. If equity is below the requirement at mark close `t`, this is recorded as a **simulated policy violation**; both legs are closed at the next executable open (`t+1`) and the policy remains inactive for the rest of the sample. This is not called a Bybit liquidation.

Funding is put in the separately collateralized perp account only when the short was already open over the preceding funding interval. A target exit at `t` still receives/pays the settlement due for `[t-8h, t]`; a position newly entered at `t` does not. Execution P&L and all trade costs remain calculated from tradable last-price opens. Mark remains non-executable and is used only for the margin check and basis.

`return_on_capital_employed` uses the reported US$100-notional return divided by a static capital denominator of `100 + buffer`. It is a simple pilot capital-efficiency normalization, not an annualized return, IRR, or claim that capital can be continuously reallocated.

## Pre-declared dead-zone check

After applying the margin policy, `src.dead_zone` evaluates a small, fixed grid without fitting: entry/exit funding thresholds of (0.5 bp, 0 bp) and (1 bp, 0.25 bp) per settlement, each with a 24h, 48h, or 72h minimum holding time. At a settlement it uses only `last_settled_funding`, which is lagged one row; the decision is executed at the next hourly open by `position_from_signal`.

The second half of this three-month pilot is labelled an out-of-sample *check*, with the split fixed before inspecting the grid results. A policy is a candidate only if it has at least one OOS risk improvement versus always-on (smaller drawdown, fewer policy violations, or lower worst margin use) **and** does not have lower OOS net return. All 54 policy × buffer × cost combinations are retained in `reports/dead_zone_summary.csv`; no parameter is selected from this pilot and no HMM is introduced.
