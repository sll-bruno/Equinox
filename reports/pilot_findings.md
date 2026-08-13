# Bybit BTCUSDT pilot — revised baseline

Period: 2026-05-12 00:00 UTC through 2026-08-13 00:00 UTC; 2,233 hourly timestamps and 280 settled funding observations; Bybit only.

## Method corrections applied

1. Every entry fixes `q = 1 / spot_open` BTC and uses exactly that quantity for spot P&L, perp P&L, funding and fees until exit.
2. Funding at settlement `t` is `q × mark_open[t] × fundingRate[t]` and is credited only to the quantity carried into `t`.
3. A rate settled at `t` can inform a decision executed at the next hourly open; the signal no longer uses an unnecessarily eight-hour-old settlement.
4. Execution P&L uses fixed-quantity USDT cash moves between spot and perpetual **opening last-trade prices**. It no longer subtracts percentage returns with different denominators.
5. All strategies pay a terminal exit for both legs.

## Funding sign check

Bybit specifies that positive funding makes long holders pay short holders. The raw API record in `data/raw/bybit/funding/4954d6dde7105727e65c95a6a18836284673db674fc359c5337632174f954139.json` reports BTCUSDT funding of `+0.000016` at 2026-05-12 00:00 UTC. For a short, the signed cash receipt is `q × mark × 0.000016`; it is therefore added, not subtracted. The sign in the motor is confirmed.

## Fixed-quantity cash-ledger results

V1 applies 0.10% spot and 0.055% perpetual taker fees to the value actually traded at every entry and exit; the approximate 31 bp round trip is not used directly. Because historical bid/ask and fill data are unavailable, the cost sensitivity retains those actual fees and applies a multiplier: 1.0× (`fee_only`), 1.5× (`base`) and 3.0× (`stress`). The excess is an explicit spread/slippage proxy, not measured execution data.

| Strategy | Gross return | Actual fees | Net fee-only | Net base (1.5×) | Net stress (3×) |
|---|---:|---:|---:|---:|---:|
| always-on | 0.6620% | 0.2756% | 0.3864% | 0.2486% | -0.1648% |
| positive last settled funding | 0.8719% | 11.1413% | -10.2694% | -15.8401% | -32.5521% |
| funding above threshold | 0.5861% | 11.4551% | -10.8690% | -16.5965% | -33.7792% |
| positive funding with volatility/basis filter | 0.3998% | 10.5241% | -10.1243% | -15.3863% | -31.1725% |

The always-on gross return is 0.6620%, consisting of 0.6675% mark-notional funding and -0.0055% fixed-quantity hedge/basis P&L. The prior return-based motor reported 0.8203% gross and overstated dollar funding on this falling-BTC path by holding perp notional artificially constant.

The reactive rules remain negative because their repeated entries and exits generate high fees. The adverse-cost test reverses even always-on's small pilot profit, so this is not evidence that the strategy reliably survives costs. Exact results and fee components are in `baseline_summary.csv`.

## Mark versus last-price comparator

For a fixed quantity held across the comparison window, hedge P&L is -0.00905% using last-traded perp opens and -0.00799% using mark opens, a difference of +0.1064 bp. Mark remains non-executable; it is used for funding notional, basis and margin.

## What this establishes

This remains a three-month descriptive pilot, not a robust strategy result. A separate 2023-24 rally margin stress is now reported in `rally_margin_findings.md`; it does not make the samples a continuous backtest. It supports no HMM decision yet.
