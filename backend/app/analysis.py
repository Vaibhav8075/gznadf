"""Glue between the stored data, the selection rule and the metrics."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from . import config, metrics
from .selection import Selected, select_series
from .store import Dataset
from .timeutil import epoch, to_iso

HOUR_S = 3600
HORIZON_GRID = list(range(0, config.MAX_HORIZON_H + 1, 2))


class WindowError(ValueError):
    pass


def window_bounds(start: date, end: date) -> tuple[int, int]:
    """Inclusive date range -> [start, end) epoch seconds, clipped to January 2026."""
    if end < start:
        raise WindowError("end date must be on or after start date")
    lo = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    hi = datetime(end.year, end.month, end.day, tzinfo=timezone.utc) + timedelta(days=1)
    if lo < config.TARGET_START or hi > config.TARGET_END:
        raise WindowError("dates must be within January 2026 (2026-01-01 to 2026-01-31)")
    return epoch(lo), epoch(hi)


def forecast_targets(ds: Dataset, lo: int, hi: int) -> list[int]:
    return sorted(t for t in ds.forecasts_by_target if lo <= t < hi)


def selected_forecasts(ds: Dataset, lo: int, hi: int, horizon_h: float) -> list[Selected]:
    # No upper cap on lead time: WINDFOR publishes at hh:30 for hourly targets,
    # so the forecast in hand at H = 48 is always 48.5 h old or more. Capping
    # at exactly 48 h would leave the 48 h setting empty.
    return select_series(ds.forecasts_by_target, forecast_targets(ds, lo, hi), horizon_h)


def series(ds: Dataset, lo: int, hi: int, horizon_h: float) -> dict:
    actual = [
        {"time": to_iso(t), "generation_mw": g} for t, g in sorted(ds.actuals.items()) if lo <= t < hi
    ]
    forecast = [
        {
            "time": to_iso(s.target),
            "generation_mw": s.generation,
            "publish_time": to_iso(s.publish),
            "lead_hours": round(s.lead_hours, 2),
        }
        for s in selected_forecasts(ds, lo, hi, horizon_h)
    ]
    return {"actual": actual, "forecast": forecast}


def _pairs(ds: Dataset, lo: int, hi: int, horizon_h: float):
    """Targets where both a selected forecast and an actual exist."""
    times, act, fc = [], [], []
    for s in selected_forecasts(ds, lo, hi, horizon_h):
        a = ds.actuals.get(s.target)
        if a is None:
            continue
        times.append(s.target)
        act.append(a)
        fc.append(s.generation)
    return times, act, fc


def accuracy(ds: Dataset, lo: int, hi: int, horizon_h: float) -> dict:
    times, act, fc = _pairs(ds, lo, hi, horizon_h)
    hours = [(t // HOUR_S) % 24 for t in times]
    errors = [f - a for a, f in zip(act, fc)]

    curve = []
    for h in HORIZON_GRID:
        _, a_h, f_h = _pairs(ds, lo, hi, h)
        s = metrics.error_summary(a_h, f_h)
        curve.append(
            {
                "horizon_h": h,
                "n": s["n"],
                "mae_mw": s.get("mae_mw"),
                "rmse_mw": s.get("rmse_mw"),
                "abs_error_p90_mw": s.get("abs_error_p90_mw"),
                "bias_mw": s.get("bias_mw"),
            }
        )

    return {
        "summary": metrics.error_summary(act, fc),
        "by_hour_utc": metrics.by_hour_of_day(hours, act, fc),
        "by_horizon": curve,
        "error_histogram": metrics.histogram(errors),
        "notes": {
            "error_definition": "forecast - actual (MW); positive = forecast too high",
            "resolution": "evaluated at hourly targets, where both a forecast and a half-hourly actual exist",
        },
    }
