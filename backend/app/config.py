"""Fixed settings for the January 2026 study window.

All times are handled in UTC. In January the UK is on GMT, so UTC equals
UK local time for every target in scope.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"

# Target times (the half-hour / hour the power is delivered) that are in scope.
TARGET_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
TARGET_END = datetime(2026, 2, 1, tzinfo=timezone.utc)  # exclusive

# Forecast horizons offered to the user, in hours.
MIN_HORIZON_H = 0
MAX_HORIZON_H = 48

# To evaluate a 48 h horizon for 1 Jan 00:00 we need forecasts published up
# to 48 h earlier, so the forecast download starts a little before that.
FORECAST_PUBLISH_FROM = TARGET_START - timedelta(hours=MAX_HORIZON_H + 24)
FORECAST_PUBLISH_TO = TARGET_END

HTTP_TIMEOUT_S = float(os.environ.get("WFM_HTTP_TIMEOUT", "20"))

BACKEND_DIR = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = BACKEND_DIR / "data" / "jan2026_snapshot.json.gz"


def cache_dir() -> Path:
    """Where the downloaded data is cached between restarts.

    Serverless platforms only allow writes under /tmp.
    """
    override = os.environ.get("WFM_CACHE_DIR")
    if override:
        return Path(override)
    if os.environ.get("VERCEL"):
        return Path("/tmp/wfm-cache")
    return BACKEND_DIR / ".cache"
