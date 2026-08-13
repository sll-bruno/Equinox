import pandas as pd
from src.run_baselines import (
    COST_SCENARIOS,
    PERP_TAKER_FEE_RATE,
    SPOT_TAKER_FEE_RATE,
    build,
    cash_return,
    make_ledger,
    make_ledger_from_position,
    turnover,
)
from src.run_margin import apply_costs
from src.run_rally_margin import breach_return


def test_complete_cycle_has_two_half_turns():
    position = pd.Series([0, 1, 1])
    trading, terminal, total = turnover(position)
    assert trading.sum() == 1
    assert terminal.sum() == 1
    assert total.sum() == 2


def test_complete_cycle_fees_use_actual_traded_values():
    frame = pd.DataFrame(
        {
            "spot_open": [100.0, 100.0, 110.0],
            "perp_last_open": [101.0, 102.0, 111.0],
            "perp_mark_open": [101.0, 102.0, 111.0],
            "funding_settled": [float("nan"), float("nan"), float("nan")],
            "hedge_execution_return_last": [0.0, 0.0, 0.0],
        }
    )
    ledger = make_ledger(frame, pd.Series([True, True, True]))
    quantity = 1 / 100
    expected_spot = SPOT_TAKER_FEE_RATE * quantity * (100 + 110)
    expected_perp = PERP_TAKER_FEE_RATE * quantity * (102 + 111)
    assert abs(ledger.spot_fee_return.sum() - expected_spot) < 1e-12
    assert abs(ledger.perp_fee_return.sum() - expected_perp) < 1e-12
    assert ledger.total_fee_return.sum() != 0.0031


def test_stress_costs_scale_actual_value_fees_without_changing_gross_return():
    frame = pd.DataFrame(
        {
            "spot_open": [100.0, 100.0, 100.0],
            "perp_last_open": [100.0, 100.0, 100.0],
            "perp_mark_open": [100.0, 100.0, 100.0],
            "funding_settled": [float("nan")] * 3,
            "hedge_execution_return_last": [0.0] * 3,
        }
    )
    ledger = make_ledger(frame, pd.Series([True, True, True]))
    assert COST_SCENARIOS == {"fee_only": 1.0, "base": 1.5, "stress": 3.0}
    assert abs(ledger.total_fee_return.sum() * COST_SCENARIOS["stress"] - 0.0093) < 1e-12


def test_cost_sensitivity_uses_actual_fees_not_flat_turnover_bps():
    ledger = pd.DataFrame({"total_fee_return": [0.001, 0.002], "gross_return": [0.0, 0.0]})
    stressed = apply_costs(ledger, COST_SCENARIOS["stress"])
    assert stressed.cost_return.tolist() == [0.003, 0.006]
    assert stressed.spread_slippage_proxy_return.tolist() == [0.002, 0.004]


def test_rally_margin_breach_thresholds_are_explicit():
    expected = lambda buffer: (buffer - 0.05 - 2 * PERP_TAKER_FEE_RATE) / (
        1 + 0.05 + PERP_TAKER_FEE_RATE
    )
    assert abs(breach_return(0.25) - expected(0.25)) < 1e-12
    assert abs(breach_return(0.50) - expected(0.50)) < 1e-12
    assert abs(breach_return(1.00) - expected(1.00)) < 1e-12


def test_latest_settled_funding_is_available_for_next_open_decision():
    frame = build()
    expected = frame.funding_settled.ffill()
    pd.testing.assert_series_equal(frame.last_settled_funding, expected, check_names=False)


def test_fixed_quantity_hedge_uses_dollar_moves_not_mismatched_percent_returns():
    frame = pd.DataFrame(
        {
            "spot_open": [100.0, 80.0],
            "perp_last_open": [101.0, 81.0],
            "perp_mark_open": [101.0, 81.0],
            "funding_settled": [float("nan"), float("nan")],
            "hedge_execution_return_last": [-0.2 - (-20 / 101), float("nan")],
        }
    )
    ledger = make_ledger_from_position(frame, pd.Series([1, 1]))
    assert ledger.trade_quantity_btc.tolist() == [0.01, 0.01]
    assert abs(ledger.spot_pnl_return.sum() + 0.20) < 1e-12
    assert abs(ledger.perp_pnl_return.sum() - 0.20) < 1e-12
    assert abs(ledger.execution_hedge_return.sum()) < 1e-12


def test_funding_uses_fixed_quantity_times_current_mark_not_constant_notional():
    frame = pd.DataFrame(
        {
            "spot_open": [100.0, 50.0],
            "perp_last_open": [100.0, 50.0],
            "perp_mark_open": [100.0, 50.0],
            "funding_settled": [float("nan"), 0.0001],
            "hedge_execution_return_last": [0.0, float("nan")],
        }
    )
    ledger = make_ledger_from_position(frame, pd.Series([1, 1]))
    # q=0.01 BTC and current mark=50, so funding is 0.01*50*0.01%=0.00005.
    assert abs(ledger.funding_cashflow.iloc[1] - 0.00005) < 1e-12
    assert ledger.funding_cashflow.iloc[1] != 0.0001


def test_funding_is_only_booked_at_settlements_and_to_prior_position():
    frame = build().head(32).copy()
    signal = pd.Series(True, index=frame.index)
    ledger = make_ledger(frame, signal)
    assert (ledger.loc[ledger.funding_settled.isna(), "funding_cashflow"] == 0).all()
    settlements = ledger.funding_settled.notna()
    assert (
        ledger.loc[settlements, "funding_position_prior_interval"]
        == ledger.position.shift(1).fillna(0).loc[settlements]
    ).all()


def test_terminal_exit_does_not_change_gross_return():
    frame = build().head(32).copy()
    ledger = make_ledger(frame, pd.Series(True, index=frame.index))
    gross = cash_return(ledger.gross_return)
    net_without_exit = ledger.gross_return - ledger.trading_fee_return
    net_with_exit = ledger.gross_return - ledger.total_fee_return
    assert gross == ledger.gross_return.fillna(0).sum()
    assert cash_return(net_with_exit) < cash_return(net_without_exit)
