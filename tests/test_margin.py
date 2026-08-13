import pandas as pd

from src.margin import short_mark_pnl, simulate_margin_policy
from src.run_baselines import PERP_TAKER_FEE_RATE, make_ledger_from_position, position_from_signal
from src.dead_zone import dead_zone_signal


def margin_frame(closes):
    return pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2026-01-01", periods=len(closes), freq="h", tz="UTC"),
            "perp_mark_open": [100.0] * len(closes),
            "perp_mark_close": closes,
            "spot_open": [100.0] * len(closes),
            "perp_last_open": [100.0] * len(closes),
            "funding_settled": [float("nan")] * len(closes),
            "hedge_execution_return_last": [0.0] * len(closes),
        }
    )


def test_short_mark_pnl_has_the_correct_sign():
    assert short_mark_pnl(1.0, 100.0, 120.0) == -20.0
    assert short_mark_pnl(1.0, 100.0, 80.0) == 20.0


def test_buffer_is_consumed_when_btc_rises_and_grows_when_it_falls():
    target = pd.Series([0, 1, 1])
    rising = simulate_margin_policy(margin_frame([100, 100, 120]), target, 0.50)
    falling = simulate_margin_policy(margin_frame([100, 100, 80]), target, 0.50)
    entry_fee = 100 * PERP_TAKER_FEE_RATE
    assert abs(rising.margin_balance_usdt.iloc[2] - (30.0 - entry_fee)) < 1e-12
    assert abs(falling.margin_balance_usdt.iloc[2] - (70.0 - entry_fee)) < 1e-12


def test_margin_uses_spot_defined_quantity_and_deducts_perp_entry_fee():
    frame = margin_frame([101, 101])
    frame["spot_open"] = [100.0, 100.0]
    frame["perp_last_open"] = [101.0, 101.0]
    frame["perp_mark_open"] = [101.0, 101.0]
    margin = simulate_margin_policy(frame, pd.Series([1, 1]), 0.50)
    assert margin.trade_quantity_btc.iloc[0] == 1.0
    assert abs(margin.perp_entry_fee_usdt.iloc[0] - 101 * PERP_TAKER_FEE_RATE) < 1e-12
    assert abs(margin.margin_balance_usdt.iloc[0] - (50 - 101 * PERP_TAKER_FEE_RATE)) < 1e-12
    expected_maintenance = 0.05 * 101 + 101 * PERP_TAKER_FEE_RATE
    assert abs(margin.maintenance_requirement_usdt.iloc[0] - expected_maintenance) < 1e-12


def test_violation_schedules_close_of_both_legs_at_next_open():
    target = pd.Series([0, 1, 1, 1])
    result = simulate_margin_policy(margin_frame([100, 100, 120, 120]), target, 0.25)
    assert result.margin_violation.tolist() == [False, False, True, False]
    assert result.effective_position.tolist() == [0, 1, 1, 0]
    assert result.policy_liquidated.tolist() == [False, False, False, True]


def test_no_violation_preserves_the_baseline_position_and_pnl():
    frame = margin_frame([100, 100, 95, 95])
    target = pd.Series([0, 1, 1, 0])
    margin = simulate_margin_policy(frame, target, 1.00)
    base = make_ledger_from_position(frame, target)
    protected = make_ledger_from_position(frame, margin.effective_position)
    assert not margin.margin_violation.any()
    assert margin.effective_position.tolist() == target.tolist()
    pd.testing.assert_series_equal(base.gross_return, protected.gross_return, check_names=False)


def test_margin_funding_is_paid_only_to_the_position_carried_into_settlement():
    frame = margin_frame([100, 100, 100])
    frame.loc[1, "funding_settled"] = 0.001
    # The t=1 position exits at that open but was open in [t=0, t=1].
    margin = simulate_margin_policy(frame, pd.Series([1, 0, 0]), 0.50)
    assert margin.margin_funding_cashflow_usdt.tolist() == [0.0, 0.1, 0.0]


def test_margin_and_performance_ledger_use_the_same_quantity_funding_and_entry_fee():
    frame = margin_frame([100, 50])
    frame["spot_open"] = [100.0, 50.0]
    frame["perp_last_open"] = [100.0, 50.0]
    frame["perp_mark_open"] = [100.0, 50.0]
    frame.loc[1, "funding_settled"] = 0.001
    margin = simulate_margin_policy(frame, pd.Series([1, 1]), 1.00)
    ledger = make_ledger_from_position(frame, margin.effective_position)
    assert (margin.trade_quantity_btc - ledger.trade_quantity_btc * 100).abs().max() == 0
    assert abs(margin.margin_funding_cashflow_usdt.sum() - ledger.funding_cashflow.sum() * 100) < 1e-12
    assert abs(
        margin.perp_entry_fee_usdt.iloc[0] - ledger.perp_entry_fee_return.sum() * 100
    ) < 1e-12


def test_dead_zone_honors_hysteresis_and_minimum_holding_time():
    frame = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2026-01-01", periods=5, freq="8h", tz="UTC"),
            "funding_settled": [0.0] * 5,
            "last_settled_funding": [0.00010, 0.0, 0.0, 0.0, 0.0],
        }
    )
    signal = dead_zone_signal(frame, entry_threshold=0.00005, exit_threshold=0.00001, min_hold_hours=24)
    assert signal.tolist() == [True, True, True, False, False]


def test_dead_zone_decision_enters_only_on_the_next_open():
    decision = pd.Series([True, False, False])
    assert position_from_signal(decision).tolist() == [0, 1, 0]
