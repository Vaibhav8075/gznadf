"""Download national wind actuals (FUELHH) and forecasts (WINDFOR) from Elexon BMRS.

Both datasets come from the public Insights Solution API, which needs no key:
  - FUELHH/stream  : half-hourly outturn generation by fuel type (we keep WIND)
  - WINDFOR/stream : hourly national wind forecasts, each row tagged with the
                     time the forecast was published
"""

from __future__ import annotations

from datetime import date, datetime

import httpx

from . import config
from .timeutil import parse_iso

Actual = tuple[int, float]  # (startTime epoch s, generation MW)
Forecast = tuple[int, int, float]  # (publishTime, startTime, generation MW)


def _get(client: httpx.Client, path: str, params: dict[str, str]) -> list[dict]:
    resp = client.get(f"{config.ELEXON_BASE_URL}/{path}", params=params)
    resp.raise_for_status()
    payload = resp.json()
    # The stream endpoints return a bare list; other endpoints wrap it in "data".
    return payload["data"] if isinstance(payload, dict) else payload


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_actuals(client: httpx.Client, date_from: date, date_to: date) -> list[Actual]:
    rows = _get(
        client,
        "FUELHH/stream",
        {
            "settlementDateFrom": date_from.isoformat(),
            "settlementDateTo": date_to.isoformat(),
            "fuelType": "WIND",
        },
    )
    out: dict[int, float] = {}
    for row in rows:
        if row.get("fuelType") != "WIND" or row.get("generation") is None:
            continue
        out[parse_iso(row["startTime"])] = float(row["generation"])
    return sorted(out.items())


def fetch_forecasts(client: httpx.Client, publish_from: datetime, publish_to: datetime) -> list[Forecast]:
    rows = _get(
        client,
        "WINDFOR/stream",
        {"publishDateTimeFrom": _iso(publish_from), "publishDateTimeTo": _iso(publish_to)},
    )
    out: dict[tuple[int, int], float] = {}
    for row in rows:
        if row.get("generation") is None:
            continue
        out[(parse_iso(row["publishTime"]), parse_iso(row["startTime"]))] = float(row["generation"])
    return sorted((p, s, g) for (p, s), g in out.items())


def fetch_january_2026() -> tuple[list[Actual], list[Forecast]]:
    """Everything needed to judge purchase decisions for January 2026 targets."""
    with httpx.Client(timeout=config.HTTP_TIMEOUT_S) as client:
        actuals = fetch_actuals(
            client,
            config.TARGET_START.date(),
            config.TARGET_END.date(),
        )
        forecasts = fetch_forecasts(client, config.FORECAST_PUBLISH_FROM, config.FORECAST_PUBLISH_TO)
    return actuals, forecasts
