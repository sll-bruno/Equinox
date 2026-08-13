import pandas as pd
from src.run_baselines import (
    PERP_TAKER_FEE_RATE,
    SPOT_TAKER_FEE_RATE,
    build,
    make_ledger,
    turnover,
)


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


def test_features_do_not_use_same_settlement_funding():
    frame = build()
    expected = frame.funding_settled.ffill().shift(1)
    pd.testing.assert_series_equal(frame.last_settled_funding, expected, check_names=False)


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
    gross = (1 + ledger.gross_return.fillna(0)).prod() - 1
    net_without_exit = ledger.gross_return - ledger.trading_fee_return
    net_with_exit = ledger.gross_return - ledger.total_fee_return
    assert gross == (1 + ledger.gross_return.fillna(0)).prod() - 1
    assert (1 + net_with_exit.fillna(0)).prod() < (1 + net_without_exit.fillna(0)).prod()
