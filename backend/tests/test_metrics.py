import math

import pytest

from app.metrics import by_hour_of_day, error_summary, histogram


def test_basic_error_statistics():
    actual = [100.0, 200.0, 300.0, 400.0]
    forecast = [110.0, 180.0, 330.0, 400.0]  # errors +10, -20, +30, 0
    s = error_summary(actual, forecast)
    assert s["n"] == 4
    assert s["mae_mw"] == 15.0
    assert s["bias_mw"] == 5.0
    assert s["rmse_mw"] == round(math.sqrt((100 + 400 + 900 + 0) / 4), 1)
    assert s["mean_actual_mw"] == 250.0
    assert s["nmae_pct"] == 6.0
    assert s["over_forecast_share_pct"] == 50.0
    assert s["abs_error_max_mw"] == 30.0


def test_percentiles_on_known_distribution():
    actual = [0.0] * 101
    forecast = [float(i) for i in range(101)]  # abs errors 0..100
    s = error_summary(actual, forecast)
    assert s["abs_error_p50_mw"] == 50.0
    assert s["abs_error_p90_mw"] == 90.0
    assert s["abs_error_p99_mw"] == 99.0


def test_ratio_ignores_zero_forecasts():
    s = error_summary([50.0, 80.0, 10.0], [100.0, 100.0, 0.0])
    # ratios only from the two positive forecasts: 0.5 and 0.8
    assert s["actual_to_forecast_p50"] == pytest.approx(0.65)


def test_empty_input():
    assert error_summary([], []) == {"n": 0}
    assert histogram([]) == []


def test_mismatched_lengths_rejected():
    with pytest.raises(ValueError):
        error_summary([1.0], [1.0, 2.0])


def test_histogram_counts_everything():
    errs = [-1200.0, -10.0, 0.0, 499.0, 501.0, 2600.0]
    bins = histogram(errs, bin_mw=500)
    assert sum(b["count"] for b in bins) == len(errs)
    assert bins[0]["from_mw"] == -1500.0
    assert bins[-1]["to_mw"] == 3000.0


def test_by_hour_of_day():
    rows = by_hour_of_day([0, 0, 5], [10.0, 20.0, 30.0], [12.0, 16.0, 30.0])
    assert len(rows) == 24
    assert rows[0] == {"hour": 0, "n": 2, "mae_mw": 3.0, "bias_mw": -1.0}
    assert rows[5]["mae_mw"] == 0.0
    assert rows[1]["n"] == 0 and rows[1]["mae_mw"] is None
