from app import config, elexon, store


def _fail():
    raise ConnectionError("Elexon unreachable")


def test_falls_back_to_bundled_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("WFM_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(elexon, "fetch_january_2026", _fail)
    store.set_dataset(None)
    try:
        ds = store.get_dataset()
        assert ds.source == "bundled snapshot"
        assert len(ds.actuals) == 31 * 48  # every half hour of January
        assert len(ds.forecasts_by_target) == 31 * 24  # every hour of January
    finally:
        store.set_dataset(None)


def test_live_download_is_cached(monkeypatch, tmp_path):
    actuals, forecasts = store.read_compact(config.SNAPSHOT_PATH)
    monkeypatch.setenv("WFM_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(elexon, "fetch_january_2026", lambda: (actuals, forecasts))
    store.set_dataset(None)
    try:
        assert store.get_dataset().source == "elexon (live download)"
        assert (tmp_path / store.CACHE_FILE_NAME).exists()
        # A fresh process would now read the cache instead of the network.
        monkeypatch.setattr(elexon, "fetch_january_2026", _fail)
        store.set_dataset(None)
        assert store.get_dataset().source == "elexon (cached download)"
    finally:
        store.set_dataset(None)
