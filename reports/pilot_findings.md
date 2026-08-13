# Bybit BTCUSDT pilot — preliminary findings

Period collected: 2026-05-12 00:00 UTC through 2026-08-13 00:00 UTC; one-hour bars; Bybit only.

## Evidence collected

- 2,233 timestamps for spot/perp candles, mark, index, premium index, OI and account ratio; 280 settled funding records.
- All implemented checks passed: nonempty series, unique UTC timestamps, no gap above two hours, positive prices, nonnegative OI, funding plausibility and a substantial spot-perp timestamp intersection.
- Funding was positive in 76.43% of settlements; mean funding was 0.292 bp per settlement and the sum was 81.80 bp. These are descriptive sample facts, not an investment conclusion.

## Baseline result

The always-on hedge produced gross 0.8184% over the pilot. Under the documented VIP-0 taker-fee-only scenario (31 bp full two-leg round trip), the net result was 0.6621%; under 50 bp and 100 bp round-trip assumptions it was 0.5664% and 0.3143%. Its maximum drawdown was -0.1686%, -0.2636% and -0.5135%, respectively.

The three reactive rules were negative under every cost scenario because their 65-73 half-turnover events outweighed their observed funding capture. This is not evidence that filters cannot work; it rejects these uncalibrated, funding-window rebalance rules in this sample.

## What this does and does not establish

The pilot supports continuing the data/margin investigation: raw funding exceeded the assumed single entry/exit cost over this short period. It does **not** establish robustness, execution feasibility, margin safety, capacity, or an HMM advantage. The cost scenarios do not claim historical spread/slippage observations. The current P&L is a simple marked hedge return plus settled funding and must be extended with a margin model and longer, held-out history before any strategy claim.

Detailed results: `baseline_summary.csv`; hourly ledger outputs: `pilot_*.parquet`.
