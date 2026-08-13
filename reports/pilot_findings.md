# Bybit BTCUSDT pilot — revised baseline

Period: 2026-05-12 00:00 UTC through 2026-08-13 00:00 UTC; 2,233 hourly timestamps and 280 settled funding observations; Bybit only.

## Method corrections applied

1. All strategies now pay a terminal exit for both legs. A full open-and-close cycle has two half-turns; `always_on` therefore has turnover of exactly 2, not 1.
2. Funding at settlement `t` is credited to the position carried into `t`, never to the position opening at `t`.
3. Execution P&L uses BTCUSDT spot and perpetual **opening last-trade prices** between `t` and `t+1`. Mark price is used only for basis and as a non-executable comparator.

## Funding sign check

Bybit specifies that positive funding makes long holders pay short holders. The raw API record in `data/raw/bybit/funding/4954d6dde7105727e65c95a6a18836284673db674fc359c5337632174f954139.json` reports BTCUSDT funding of `+0.000016` at 2026-05-12 00:00 UTC. For a one-USDT equivalent short notional this is a receipt of 0.000016 USDT; for the baseline short-perp leg it is therefore added, not subtracted. The sign in the motor is confirmed.

## Actual-value fee results

Funding, execution hedge P&L, signals and positions retain the prior implementation. Only trading fees changed: instead of subtracting fixed 31/50/100 bp scenarios, V0 applies 0.10% spot and 0.055% perpetual taker fees to the value actually traded at every entry and exit. The approximate 31 bp round trip is not used directly.

| Strategy | Gross return | Spot fees | Perp fees | Net with terminal exit |
|---|---:|---:|---:|---:|
| always-on | 0.8203% | 0.1779% | 0.0978% | 0.5427% |
| positive last settled funding | 0.7509% | 7.1911% | 3.9533% | -9.8818% |
| funding above threshold | 0.4903% | 7.3991% | 4.0677% | -10.4044% |
| positive funding with volatility/basis filter | 0.3533% | 6.5938% | 3.6249% | -9.4021% |

The always-on gross return remains 0.8203%, consisting of 0.8164% funding and 0.0013% execution hedge return. This confirms that the fee change did not alter either gross-return component.

The reactive rules remain negative because their repeated entries and exits generate high fees. Exact results and fee components are in `baseline_summary.csv`.

## Mark versus last-price comparator

Over the same hourly intervals, the compounded execution hedge return is -0.00285% with last-traded perp opens and -0.00313% with mark-price opens. The mark-minus-last difference is -0.000274 percentage points (-0.0274 bp). This small sample difference does not justify treating mark as executable; it remains an input for basis and a future margin/liquidation model.

## What this establishes

This is still a three-month descriptive pilot, not a robust strategy result. It supports no HMM decision yet. The next valid research step is longer history and a margin/collateral model; neither is included in this change.
