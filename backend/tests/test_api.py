from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import store
from app.main import app

H = 3600
T0 = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp())


@pytest.fixture()
def client():
    # Two days of synthetic data: actual = 1000 MW every half hour; forecast runs
    # published every 6 h, with each run's value equal to its lead time in hours
    # so the test can see which run was picked.
    actuals = [(T0 + i * 1800, 1000.0) for i in range(96)]
    forecasts = []
    for run in range(-8, 8):
        pub = T0 + run * 6 * H + 1800  # published at hh:30 like WINDFOR
        for k in range(48):
            tgt = T0 + k * H
            lead = (tgt - pub) / H
            forecasts.append((pub, tgt, 1000.0 + lead))
    store.set_dataset(store.Dataset.build(actuals, forecasts, source="test"))
    yield TestClient(app)
    store.set_dataset(None)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_meta(client):
    body = client.get("/api/meta").json()
    assert body["actual_points"] == 96
    assert body["forecast_targets"] == 48
    assert body["data_source"] == "test"


def test_series_respects_horizon(client):
    body = client.get("/api/series", params={"start": "2026-01-01", "end": "2026-01-02", "horizon": 4}).json()
    assert len(body["actual"]) == 96
    leads = [f["lead_hours"] for f in body["forecast"]]
    assert leads and min(leads) >= 4
    # runs are 6 h apart, so the chosen run is never more than 4 + 6 h old
    assert max(leads) <= 10


def test_accuracy_shape(client):
    body = client.get("/api/accuracy", params={"start": "2026-01-01", "end": "2026-01-01", "horizon": 0}).json()
    s = body["summary"]
    assert s["n"] == 24
    assert s["bias_mw"] > 0  # synthetic forecast is always 1000 + lead
    assert len(body["by_hour_utc"]) == 24
    assert body["by_horizon"][0]["horizon_h"] == 0
    assert sum(b["count"] for b in body["error_histogram"]) == 24


@pytest.mark.parametrize(
    "params",
    [
        {"start": "2025-12-31", "end": "2026-01-02"},
        {"start": "2026-01-10", "end": "2026-02-01"},
        {"start": "2026-01-05", "end": "2026-01-04"},
        {"horizon": 49},
        {"horizon": -1},
    ],
)
def test_bad_parameters_rejected(client, params):
    assert client.get("/api/series", params=params).status_code == 422
