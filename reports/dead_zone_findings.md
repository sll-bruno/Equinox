# Dead-zone pilot — margin-aware, no HMM

This is a deliberately small, pre-declared check after the collateral-policy layer. It does not add features, expand history, fit parameters, or introduce an HMM.

## Fixed grid and candidate rule

At funding settlements the policy observes only the already-lagged `last_settled_funding`; it executes at the next hourly open. The six rules are the two entry/exit pairs below crossed with 24h, 48h and 72h minimum holds:

| Entry threshold | Exit threshold |
|---:|---:|
| 0.5 bp per settlement | 0 bp |
| 1.0 bp per settlement | 0.25 bp |

Each rule is run through every cost scenario and 25%/50%/100% collateral buffer, including final close and the simulated margin-violation policy. The OOS check is the fixed second half of the pilot, beginning 2026-06-27 12:00 UTC. A policy is a candidate only if, versus margin-aware always-on in that OOS half, it improves at least one risk metric (drawdown, violation count, or worst margin use) **and** does not lower net return.

## Result

There are zero candidates out of 54 rule × buffer × cost combinations. No combination had a simulated margin violation, so the zone did not gain a violation advantage. In the base-cost, 25%-buffer comparison, always-on produced +0.2867% OOS net return with -0.2518% OOS drawdown; every zone rule had negative OOS return and materially worse drawdown.

The least-bad base-cost rule was entry 1 bp / exit 0.25 bp with a 48h hold. It still produced -3.9625% total return on notional (-3.1700% on US$125 employed capital), 18 half-turns, and -2.6291% OOS return. It is not a candidate.

The useful conclusion is negative: on this pilot, the simple dead zones destroy the funding carry through turnover and do not improve the selected risk metrics. No further parameter search or HMM is warranted from this evidence.

See `dead_zone_summary.csv` for every retained combination and the per-row candidate-rule fields. The same spread, order-book, historic-Bybit-margin, capacity, and long-history/out-of-sample limitations listed in `margin_findings.md` remain.
