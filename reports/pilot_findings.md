# Bybit BTCUSDT pilot — V0 actual-value fee model

Period: 2026-05-12 00:00 UTC through 2026-08-13 00:00 UTC; 2,233 hourly timestamps and 280 settled funding observations; Bybit only.

## V0 P&L convention

1. Each entry deploys one unit of spot notional, with `q = 1 / spot entry price`. The same BTC quantity is held long in spot and short in the perpetual until exit.
2. Basis P&L is `q[(F0 - S0) - (FT - ST)]`, accumulated from executable open-to-open spot and perpetual last-trade prices.
3. Funding at settlement `t` is credited to the position carried into `t`. Because wallet cashflows are unavailable, the payment is reconstructed as `funding rate × q × contemporaneous perpetual mark price`.
4. Every strategy pays both entry and exit fees, including a terminal close for an open final position.

## Funding sign check

Bybit specifies that positive funding makes long holders pay short holders. The raw API record in `data/raw/bybit/funding/4954d6dde7105727e65c95a6a18836284673db674fc359c5337632174f954139.json` reports BTCUSDT funding of `+0.000016` at 2026-05-12 00:00 UTC. For a one-USDT equivalent short notional this is a receipt of 0.000016 USDT; for the baseline short-perp leg it is therefore added, not subtracted. The sign in the motor is confirmed.

## Trading fees

V0 assumes Bybit non-VIP taker fees: 0.10% on spot and 0.055% on the linear perpetual. The old fixed 31/50/100 bp scenarios were removed. Every fee is now charged on the value actually traded at that operation:

`fees = 0.001 q(S0 + ST) + 0.00055 q(F0 + FT)`

The approximate 31 bp round-trip remains a useful reference only when entry and exit prices are nearly equal. It is not used directly by the engine. Spread, slippage and the former non-historical execution buffers are deliberately excluded from V0.

## V0 results

| Strategy | Gross P&L | Funding | Basis P&L | Spot fees | Perp fees | Net P&L |
|---|---:|---:|---:|---:|---:|---:|
| always-on | 0.6620% | 0.6675% | -0.0055% | 0.1779% | 0.0978% | 0.3864% |
| positive last settled funding | 0.7504% | 0.7642% | -0.0138% | 7.1911% | 3.9533% | -10.3940% |
| funding above threshold | 0.4925% | 0.3826% | 0.1099% | 7.3991% | 4.0677% | -10.9743% |
| positive funding with volatility/basis filter | 0.3538% | 0.4130% | -0.0591% | 6.5938% | 3.6249% | -9.8649% |

The reactive rules remain negative because repeated entry and exit fees overwhelm the funding earned. Exact outputs and separate fee components are in `baseline_summary.csv` and the per-strategy Parquet ledgers.

## Mark versus last-price comparator

Over the same hourly intervals, the compounded execution hedge return is -0.00285% with last-traded perp opens and -0.00313% with mark-price opens. The mark-minus-last difference is -0.000274 percentage points (-0.0274 bp). This small sample difference does not justify treating mark as executable; it remains an input for basis and a future margin/liquidation model.

## What this establishes

This is still a three-month descriptive pilot, not a robust strategy result. It excludes spread, slippage, borrow, network and transfer costs, FX conversion, capital opportunity cost, sophisticated margin modelling and taxes. It supports no HMM decision yet.
