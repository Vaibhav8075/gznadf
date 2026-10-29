"""FastAPI application. Every route lives under /api so the same app works
behind the Vite dev proxy, nginx (Docker) and Vercel rewrites."""

from __future__ import annotations

import os
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import analysis, config
from .store import get_dataset
from .timeutil import to_iso

app = FastAPI(
    title="Wind Forecast Monitor API",
    description="UK national wind generation: Elexon BMRS actuals (FUELHH) vs forecasts (WINDFOR), January 2026.",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

origins = [o for o in os.environ.get("WFM_CORS_ORIGINS", "*").split(",") if o]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET"], allow_headers=["*"])

# Historical data never changes, so browsers and the CDN may cache responses.
CACHE_HEADERS = {"Cache-Control": "public, max-age=3600, s-maxage=86400"}

StartQ = Query(date(2026, 1, 1), description="First target date (inclusive), within January 2026")
EndQ = Query(date(2026, 1, 31), description="Last target date (inclusive), within January 2026")
HorizonQ = Query(
    4.0,
    ge=config.MIN_HORIZON_H,
    le=config.MAX_HORIZON_H,
    description="Minimum hours between a forecast's publish time and its target time",
)


def _bounds(start: date, end: date) -> tuple[int, int]:
    try:
        return analysis.window_bounds(start, end)
    except analysis.WindowError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/meta")
def meta() -> JSONResponse:
    ds = get_dataset()
    pubs = ds.publish_times
    return JSONResponse(
        {
            "target_start": to_iso(int(config.TARGET_START.timestamp())),
            "target_end_exclusive": to_iso(int(config.TARGET_END.timestamp())),
            "horizon_min_h": config.MIN_HORIZON_H,
            "horizon_max_h": config.MAX_HORIZON_H,
            "actual_points": len(ds.actuals),
            "forecast_targets": len(ds.forecasts_by_target),
            "forecast_publishes": len(pubs),
            "first_publish": to_iso(pubs[0]) if pubs else None,
            "last_publish": to_iso(pubs[-1]) if pubs else None,
            "data_source": ds.source,
            "loaded_at": ds.loaded_at,
        }
    )


@app.get("/api/series")
def series(start: date = StartQ, end: date = EndQ, horizon: float = HorizonQ) -> JSONResponse:
    lo, hi = _bounds(start, end)
    body = analysis.series(get_dataset(), lo, hi, horizon)
    body.update({"start": start.isoformat(), "end": end.isoformat(), "horizon_h": horizon})
    return JSONResponse(body, headers=CACHE_HEADERS)


@app.get("/api/accuracy")
def accuracy(start: date = StartQ, end: date = EndQ, horizon: float = HorizonQ) -> JSONResponse:
    lo, hi = _bounds(start, end)
    body = analysis.accuracy(get_dataset(), lo, hi, horizon)
    body.update({"start": start.isoformat(), "end": end.isoformat(), "horizon_h": horizon})
    return JSONResponse(body, headers=CACHE_HEADERS)
