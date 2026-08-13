# Collateral-policy pilot — Bybit BTCUSDT

Period: 2026-05-12 00:00 UTC through 2026-08-13 00:00 UTC. This is the same three-month, Bybit-only BTCUSDT pilot as the baseline; it is not annualized.

## Policy and interpretation

The trade has equal spot-long and perp-short BTC quantities, normalized to US$100 of initial matched notional. The US$100 spot purchase and the USDT collateral buffer are separate accounts. The short is marked each hour at the Bybit mark close; spot P&L cannot replenish collateral. The model uses a deliberately conservative 5% maintenance requirement of current marked short notional. It is a **simulated policy**, not historic Bybit liquidation reconstruction.

At a mark-close breach, the policy records a violation and closes both legs at the next hourly executable open. The closure cost is already included through the normal half-turn accounting. Full details and every strategy/cost/buffer combination are in `margin_summary.csv`.

## Always-on result

All three buffers survived this particular pilot with zero simulated violations. This is now explicitly bounded: the worst adverse short excursion was below +0.4%, whereas the simplified policy needs approximately +19.05%, +42.86%, and +90.48% from entry to breach the 25%, 50%, and 100% buffers. It therefore does **not** validate collateral survival.

The separate [2023-24 rally stress report](rally_margin_findings.md) addresses that missing direction of risk: all three buffers trigger one simulated policy violation under the same 5% rule. This confirms the layer responds to the risk it is intended to guard, but it remains a simplified policy rather than historical Bybit liquidation.

| Buffer per US$100 spot | Capital employed | Base net / notional | Base return / employed capital | Worst margin balance | Worst maintenance / equity | Violations |
|---|---:|---:|---:|---:|---:|---:|
| 25% | US$125 | 0.4040% | 0.3232% | US$24.60 | 20.41% | 0 |
| 50% | US$150 | 0.4040% | 0.2693% | US$49.60 | 10.12% | 0 |
| 100% | US$200 | 0.4040% | 0.2020% | US$99.60 | 5.04% | 0 |

For every buffer, the base result consists of 0.8164% funding received, 0.0013% execution hedge P&L, 0.2756% actual Bybit fees, and a 0.1378% explicit spread/slippage proxy (0.4134% total costs). Effective exposure was 99.96% and turnover was exactly two half-turns (entry and final exit). The result is positive at documented fees only (0.5427% on notional), but negative under the 3×-fee stress (-0.0116%). Increasing buffer lowers capital efficiency but did not change this path's simulated survival result.

The original reactive baseline rules also had zero policy violations in this short sample, but remain economically unattractive after their extra turnover. The complete rows are preserved in `margin_summary.csv`; no good result is inferred from the absence of a breach.

## Remaining limitations

- Historical bid/ask spread, slippage and order-book depth remain unavailable; the 1.5×/3× scenarios are explicit fee multipliers, not observed fills.
- The model does not reproduce historical Bybit risk tiers, maintenance/initial margin, liquidation fees, insurance-fund handling, or exact liquidation price rules.
- Capacity, borrow/custody/spot financing, outages, transfer latency and venue operational risk are outside the pilot.
- The 2026 pilot and 2023-24 rally stress are separate windows, not a continuous long-history or out-of-sample validation.
