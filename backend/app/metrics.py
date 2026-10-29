"""Forecast accuracy metrics.

Error is defined as forecast - actual (MW): positive means the forecast was too
high, i.e. less wind turned up than expected and the buyer is short.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np


def _r(x: float | None, nd: int = 1) -> float | None:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return round(float(x), nd)


def error_summary(actual: Sequence[float], forecast: Sequence[float]) -> dict:
    a = np.asarray(actual, dtype=float)
    f = np.asarray(forecast, dtype=float)
    if a.shape != f.shape:
        raise ValueError("actual and forecast must have the same length")
    n = int(a.size)
    if n == 0:
        return {"n": 0}
    err = f - a
    abs_err = np.abs(err)
    mean_actual = float(a.mean())

    # How much of the forecast wind actually arrived. Only meaningful when a
    # positive amount was forecast.
    mask = f > 0
    ratio = a[mask] / f[mask]
    shortfall = f - a  # MW the buyer would be short if they trusted the forecast

    return {
        "n": n,
        "mae_mw": _r(abs_err.mean()),
        "rmse_mw": _r(math.sqrt(float((err**2).mean()))),
        "bias_mw": _r(err.mean()),
        "mean_actual_mw": _r(mean_actual),
        "nmae_pct": _r(100 * abs_err.mean() / mean_actual) if mean_actual > 0 else None,
        "abs_error_p50_mw": _r(np.percentile(abs_err, 50)),
        "abs_error_p90_mw": _r(np.percentile(abs_err, 90)),
        "abs_error_p99_mw": _r(np.percentile(abs_err, 99)),
        "abs_error_max_mw": _r(abs_err.max()),
        "over_forecast_share_pct": _r(100 * float((err > 0).mean())),
        "actual_to_forecast_p10": _r(np.percentile(ratio, 10), 3) if ratio.size else None,
        "actual_to_forecast_p50": _r(np.percentile(ratio, 50), 3) if ratio.size else None,
        "shortfall_p90_mw": _r(np.percentile(shortfall, 90)),
    }


def histogram(errors: Sequence[float], bin_mw: float = 500.0) -> list[dict]:
    e = np.asarray(errors, dtype=float)
    if e.size == 0:
        return []
    lo = math.floor(e.min() / bin_mw) * bin_mw
    hi = math.ceil(e.max() / bin_mw) * bin_mw
    if hi == lo:
        hi = lo + bin_mw
    edges = np.arange(lo, hi + bin_mw, bin_mw)
    counts, edges = np.histogram(e, bins=edges)
    return [
        {"from_mw": float(edges[i]), "to_mw": float(edges[i + 1]), "count": int(c)}
        for i, c in enumerate(counts)
    ]


def by_hour_of_day(hours: Sequence[int], actual: Sequence[float], forecast: Sequence[float]) -> list[dict]:
    h = np.asarray(hours, dtype=int)
    a = np.asarray(actual, dtype=float)
    f = np.asarray(forecast, dtype=float)
    out = []
    for hour in range(24):
        m = h == hour
        if not m.any():
            out.append({"hour": hour, "n": 0, "mae_mw": None, "bias_mw": None})
            continue
        err = f[m] - a[m]
        out.append(
            {
                "hour": hour,
                "n": int(m.sum()),
                "mae_mw": _r(np.abs(err).mean()),
                "bias_mw": _r(err.mean()),
            }
        )
    return out
