"""Load the January 2026 data once and keep it in memory.

Lookup order on a cold start:
  1. local cache file written by an earlier live download
  2. live download from Elexon (then written to the cache file)
  3. bundled snapshot in backend/data/ (used only if Elexon is unreachable)

January 2026 is history, so the data does not change once downloaded.
"""

from __future__ import annotations

import gzip
import json
import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from . import config, elexon
from .elexon import Actual, Forecast
from .timeutil import epoch, to_iso

log = logging.getLogger(__name__)

CACHE_FILE_NAME = "jan2026.json.gz"


@dataclass
class Dataset:
    actuals: dict[int, float]
    # target time -> (publish times sorted ascending, generation values in the same order)
    forecasts_by_target: dict[int, tuple[list[int], list[float]]]
    source: str
    loaded_at: str
    publish_times: list[int] = field(default_factory=list)

    @classmethod
    def build(cls, actuals: list[Actual], forecasts: list[Forecast], source: str) -> "Dataset":
        start, end = epoch(config.TARGET_START), epoch(config.TARGET_END)
        acts = {t: g for t, g in actuals if start <= t < end}
        grouped: dict[int, list[tuple[int, float]]] = defaultdict(list)
        pubs: set[int] = set()
        for pub, tgt, gen in forecasts:
            if start <= tgt < end:
                grouped[tgt].append((pub, gen))
                pubs.add(pub)
        by_target = {}
        for tgt, items in grouped.items():
            items.sort()
            by_target[tgt] = ([p for p, _ in items], [g for _, g in items])
        return cls(
            actuals=acts,
            forecasts_by_target=by_target,
            source=source,
            loaded_at=to_iso(int(time.time())),
            publish_times=sorted(pubs),
        )


def write_compact(path: Path, actuals: list[Actual], forecasts: list[Forecast]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {"actuals": actuals, "forecasts": forecasts}
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(body, fh, separators=(",", ":"))


def read_compact(path: Path) -> tuple[list[Actual], list[Forecast]]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        body = json.load(fh)
    actuals = [(int(t), float(g)) for t, g in body["actuals"]]
    forecasts = [(int(p), int(t), float(g)) for p, t, g in body["forecasts"]]
    return actuals, forecasts


def _load() -> Dataset:
    cache_path = config.cache_dir() / CACHE_FILE_NAME
    if cache_path.exists():
        try:
            return Dataset.build(*read_compact(cache_path), source="elexon (cached download)")
        except (OSError, ValueError, KeyError) as exc:
            log.warning("Ignoring unreadable cache %s: %s", cache_path, exc)

    try:
        actuals, forecasts = elexon.fetch_january_2026()
        try:
            write_compact(cache_path, actuals, forecasts)
        except OSError as exc:  # read-only file system: keep going with memory only
            log.warning("Could not write cache %s: %s", cache_path, exc)
        return Dataset.build(actuals, forecasts, source="elexon (live download)")
    except Exception as exc:  # network error, HTTP error, bad payload
        if config.SNAPSHOT_PATH.exists():
            log.warning("Elexon download failed (%s); using bundled snapshot", exc)
            return Dataset.build(*read_compact(config.SNAPSHOT_PATH), source="bundled snapshot")
        raise


_lock = threading.Lock()
_dataset: Dataset | None = None


def get_dataset() -> Dataset:
    global _dataset
    if _dataset is None:
        with _lock:
            if _dataset is None:
                _dataset = _load()
    return _dataset


def set_dataset(ds: Dataset | None) -> None:
    """Replace the in-memory dataset (used by tests)."""
    global _dataset
    _dataset = ds
