"""Conservative, simplified collateral policy for the BTC spot/perp hedge."""
from __future__ import annotations

import pandas as pd

UNIT_NOTIONAL_USDT = 100.0
MAINTENANCE_RATE = 0.05


def short_mark_pnl(quantity_btc, entry_mark, current_mark):
    """USDT P&L for a short marked from entry to the current mark price."""
    return quantity_btc * (entry_mark - current_mark)


def simulate_margin_policy(
    frame,
    target_position,
    buffer_fraction,
    maintenance_rate=MAINTENANCE_RATE,
    unit_notional_usdt=UNIT_NOTIONAL_USDT,
):
    """Apply a segregated-margin policy without claiming historical Bybit liquidation fidelity.

    A position entered at an hourly open has matched spot and short-perp quantities,
    sized to `unit_notional_usdt` at that entry. Margin is checked at each hourly
    mark close. A violation observed at close t schedules both-leg closure at the
    next executable open; the policy then remains inactive for the sample.
    """
    result = frame[["timestamp_utc", "perp_mark_open", "perp_mark_close", "funding_settled"]].copy()
    target = target_position.astype(int).reset_index(drop=True)
    result = result.reset_index(drop=True)
    initial_buffer = unit_notional_usdt * buffer_fraction

    effective, liquidated, violations = [], [], []
    funding_cash, short_pnl, balance, maintenance, usage = [], [], [], [], []
    active = False
    permanently_closed = False
    close_next_open = False
    quantity = entry_mark = None
    accrued_funding = 0.0
    prior_effective = 0

    for i, row in result.iterrows():
        if close_next_open:
            active = False
            permanently_closed = True
            close_next_open = False
        # Funding at t belongs to the position carried into t, even if the target
        # exits at this row's open. It is not due to a new position entered at t.
        settlement_cash = 0.0
        if prior_effective and pd.notna(row.funding_settled):
            settlement_cash = unit_notional_usdt * float(row.funding_settled)

        desired = target.iloc[i]
        if permanently_closed:
            current_effective = 0
        elif desired and not active:
            active = True
            quantity = unit_notional_usdt / float(row.perp_mark_open)
            entry_mark = float(row.perp_mark_open)
            accrued_funding = 0.0
            current_effective = 1
        elif desired and active:
            current_effective = 1
        else:
            active = False
            current_effective = 0

        violation = False
        current_short_pnl = current_balance = current_maintenance = current_usage = float("nan")
        if current_effective:
            # Funding is settled in the separately collateralized perp account.
            if settlement_cash:
                accrued_funding += settlement_cash
            current_short_pnl = short_mark_pnl(quantity, entry_mark, float(row.perp_mark_close))
            current_balance = initial_buffer + current_short_pnl + accrued_funding
            current_maintenance = maintenance_rate * quantity * float(row.perp_mark_close)
            current_usage = float("inf") if current_balance <= 0 else current_maintenance / current_balance
            if current_balance < current_maintenance:
                violation = True
                close_next_open = True

        effective.append(current_effective)
        liquidated.append(permanently_closed)
        violations.append(violation)
        funding_cash.append(settlement_cash)
        short_pnl.append(current_short_pnl)
        balance.append(current_balance)
        maintenance.append(current_maintenance)
        usage.append(current_usage)
        prior_effective = current_effective

    result["target_position"] = target
    result["effective_position"] = effective
    result["policy_liquidated"] = liquidated
    result["margin_violation"] = violations
    result["margin_funding_cashflow_usdt"] = funding_cash
    result["short_mark_pnl_usdt"] = short_pnl
    result["margin_balance_usdt"] = balance
    result["maintenance_requirement_usdt"] = maintenance
    result["maintenance_to_equity"] = usage
    result["buffer_fraction"] = buffer_fraction
    result["initial_margin_usdt_per_100_notional"] = initial_buffer
    return result
