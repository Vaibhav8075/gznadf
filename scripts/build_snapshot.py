"""Download January 2026 data from Elexon and save the bundled fallback snapshot.

Usage (from the repository root):
    python scripts/build_snapshot.py

The app downloads live data on its own; the snapshot is only used when the
Elexon API cannot be reached, so a deployed demo keeps working.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app import config, elexon, store  # noqa: E402


def main() -> None:
    actuals, forecasts = elexon.fetch_january_2026()
    store.write_compact(config.SNAPSHOT_PATH, actuals, forecasts)
    size_kb = config.SNAPSHOT_PATH.stat().st_size / 1024
    print(f"{len(actuals)} actual rows, {len(forecasts)} forecast rows -> {config.SNAPSHOT_PATH} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
