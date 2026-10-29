import pytest

from app.selection import select_forecast, select_series

H = 3600
T = 100 * H  # an arbitrary target time (epoch seconds)


def test_picks_latest_forecast_published_at_least_h_before_target():
    pubs = [T - 30 * H, T - 10 * H, T - 5 * H, T - 1 * H]
    gens = [1.0, 2.0, 3.0, 4.0]
    chosen = select_forecast(pubs, gens, T, horizon_h=4)
    assert chosen.publish == T - 5 * H
    assert chosen.generation == 3.0
    assert chosen.lead_hours == 5


def test_publish_exactly_h_before_target_is_allowed():
    pubs = [T - 8 * H, T - 4 * H]
    chosen = select_forecast(pubs, [1.0, 2.0], T, horizon_h=4)
    assert chosen.publish == T - 4 * H


def test_publish_one_second_too_late_is_rejected():
    pubs = [T - 8 * H, T - 4 * H + 1]
    chosen = select_forecast(pubs, [1.0, 2.0], T, horizon_h=4)
    assert chosen.publish == T - 8 * H


def test_returns_none_when_every_forecast_is_too_recent():
    assert select_forecast([T - 2 * H, T - H], [1.0, 2.0], T, horizon_h=6) is None


def test_forecasts_published_after_target_never_used_at_zero_horizon():
    # WINDFOR runs also contain rows for hours that have already passed.
    pubs = [T - 3 * H, T + 2 * H]
    chosen = select_forecast(pubs, [1.0, 9.0], T, horizon_h=0)
    assert chosen.generation == 1.0


def test_max_horizon_drops_stale_forecasts():
    pubs = [T - 60 * H]
    assert select_forecast(pubs, [1.0], T, horizon_h=4, max_horizon_h=48) is None
    assert select_forecast(pubs, [1.0], T, horizon_h=4).publish == T - 60 * H


def test_fractional_horizon():
    pubs = [T - 3 * H, T - 90 * 60]
    assert select_forecast(pubs, [1.0, 2.0], T, horizon_h=1.5).generation == 2.0
    assert select_forecast(pubs, [1.0, 2.0], T, horizon_h=1.6).generation == 1.0


def test_negative_horizon_rejected():
    with pytest.raises(ValueError):
        select_forecast([T - H], [1.0], T, horizon_h=-1)


def test_empty_history():
    assert select_forecast([], [], T, horizon_h=0) is None


def test_select_series_skips_targets_without_forecasts():
    by_target = {
        T: ([T - 10 * H, T - 2 * H], [5.0, 6.0]),
        T + H: ([T + H - 1 * H], [7.0]),  # only a 1 h-ahead forecast
    }
    out = select_series(by_target, [T, T + H, T + 2 * H], horizon_h=2)
    assert [(s.target, s.generation) for s in out] == [(T, 6.0)]
