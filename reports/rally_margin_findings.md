# Historical rally stress — simulated collateral policy

Window: Bybit BTCUSDT, 2023-10-01 00:00 UTC through 2024-09-01 00:00 UTC (exclusive). This is a separately reported historical stress window, not a continuation of the 2026 pilot.

## Why this window

The 2026 pilot was adverse to spot but did not meaningfully test the short-perp margin account. This window begins with mark price US$26,953.50 and reaches US$73,655.72 on 2024-03-14 06:00 UTC: a +173.27% maximum adverse excursion for a continuously held short. It also contains a +13.87% maximum 24-hour mark rise and a -18.40% maximum 24-hour mark fall, plus 95 negative-funding settlements out of 1,008. It is materially different from the original pilot's +0.4% worst short-adverse move.

## Result: the margin policy is breached

Under the explicitly simplified 5% maintenance rule, a mark rise of about 19.05%, 42.86%, or 90.48% from entry breaches the 25%, 50%, or 100% buffer respectively. The historical maximum of +173.27% crossed every threshold. Always-on recorded one simulated violation at each buffer and closed both legs at the following executable hourly open:

| Buffer | First simulated violation observed | Effective exposure before forced closure |
|---|---|---:|
| 25% | 2023-10-23 23:00 UTC | 6.82% |
| 50% | 2023-12-02 20:00 UTC | 18.69% |
| 100% | 2024-02-20 14:00 UTC | 42.42% |

The distinction matters: these are **simulated policy violations**, not claims about actual historical Bybit liquidation. They establish that the implemented guardrail behaves in the short-rally direction it was designed for. They also show that none of the tested static buffers can be called sufficient for a continuously held short in this window.

Cost scenarios use actual-value Bybit taker fees with 1.0× / 1.5× / 3.0× fee multipliers for fee-only/base/stress; all results, strategy variants, funding, costs, exposure, and timestamps are retained in `rally_margin_summary.csv`.
