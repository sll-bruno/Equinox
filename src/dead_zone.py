"""Pre-declared hysteresis policies for funding carry; no parameter fitting."""
from __future__ import annotations

import pandas as pd

DEAD_ZONE_GRID = (
    # Funding rates are decimal fractions: 0.00005 = 0.5 bp per settlement.
    {"name": "enter_0_5bp_exit_0bp", "entry_threshold": 0.00005, "exit_threshold": 0.0},
    {"name": "enter_1bp_exit_0_25bp", "entry_threshold": 0.00010, "exit_threshold": 0.000025},
)
MIN_HOLD_HOURS = (24, 48, 72)


def dead_zone_signal(frame, entry_threshold, exit_threshold, min_hold_hours):
    """Use only the prior settled funding and permit exit after the declared holding floor.

    The returned decision is shifted into an execution position by `position_from_signal`,
    preserving the engine's t decision -> t+1 open convention.
    """
    if exit_threshold >= entry_threshold:
        raise ValueError("exit threshold must be strictly below entry threshold")
    state = False
    entry_decision_time = None
    signal = []
    for _, row in frame.iterrows():
        if pd.notna(row.funding_settled):
            previous_funding = row.last_settled_funding
            if not state and pd.notna(previous_funding) and previous_funding >= entry_threshold:
                state = True
                entry_decision_time = row.timestamp_utc
            elif (
                state
                and row.timestamp_utc - entry_decision_time >= pd.Timedelta(hours=min_hold_hours)
                and pd.notna(previous_funding)
                and previous_funding <= exit_threshold
            ):
                state = False
                entry_decision_time = None
        signal.append(state)
    return pd.Series(signal, index=frame.index, dtype=bool)
