# Bybit BTCUSDT pilot — revised baseline

Period: 2026-05-12 00:00 UTC through 2026-08-13 00:00 UTC; 2,233 hourly timestamps and 280 settled funding observations; Bybit only.

## Method corrections applied

1. All strategies now pay a terminal exit for both legs. A full open-and-close cycle has two half-turns; `always_on` therefore has turnover of exactly 2, not 1.
2. Funding at settlement `t` is credited to the position carried into `t`, never to the position opening at `t`.
3. Execution P&L uses BTCUSDT spot and perpetual **opening last-trade prices** between `t` and `t+1`. Mark price is used only for basis and as a non-executable comparator.

## Funding sign check

Bybit specifies that positive funding makes long holders pay short holders. The raw API record in `data/raw/bybit/funding/4954d6dde7105727e65c95a6a18836284673db674fc359c5337632174f954139.json` reports BTCUSDT funding of `+0.000016` at 2026-05-12 00:00 UTC. For a one-USDT equivalent short notional this is a receipt of 0.000016 USDT; for the baseline short-perp leg it is therefore added, not subtracted. The sign in the motor is confirmed.

## Old versus revised results

The old published results omitted the terminal exit. They also silently dropped the final settlement because an unavailable `t→t+1` return produced `NaN`. `legacy_published_*` in `baseline_summary.csv` reproduces that behavior only for comparison. `net_return_without_terminal_exit` uses the corrected funding timing; `net_return_with_terminal_exit` is the current result.

| Strategy | Cost cycle | Old published net | Revised net, no terminal exit | Revised net, terminal exit |
|---|---:|---:|---:|---:|
| always-on | 31 bp | 0.6621% | 0.6641% | 0.5081% |
| always-on | 50 bp | 0.5664% | 0.5683% | 0.3169% |
| always-on | 100 bp | 0.3143% | 0.3163% | -0.1853% |

The terminal exit changes only net P&L. The revised always-on gross return is 0.8203%, consisting of 0.8164% funding and 0.0013% execution hedge return; it is unchanged between revised-without-exit and revised-with-exit. It differs from the old reported gross by 0.00194 percentage points solely because the corrected ledger recognizes the final settled funding.

The reactive rules remain negative at all cost levels after the timing correction and final exit. The exact revised results, including old-versus-new columns and turnover, are in `baseline_summary.csv`.

## Mark versus last-price comparator

Over the same hourly intervals, the compounded execution hedge return is -0.00285% with last-traded perp opens and -0.00313% with mark-price opens. The mark-minus-last difference is -0.000274 percentage points (-0.0274 bp). This small sample difference does not justify treating mark as executable; it remains an input for basis and a future margin/liquidation model.

## What this establishes

This is still a three-month descriptive pilot, not a robust strategy result. It supports no HMM decision yet. The next valid research step is longer history and a margin/collateral model; neither is included in this change.
