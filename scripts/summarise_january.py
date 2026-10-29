"""Print and save headline accuracy numbers for all of January 2026.

Usage (from the repository root):
    python scripts/summarise_january.py

Writes docs/jan2026_metrics.json; docs/analysis.md quotes numbers from it.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app import analysis, store  # noqa: E402
from app.timeutil import to_iso  # noqa: E402

HORIZONS = [0, 4, 12, 24, 36, 48]


def main() -> None:
    ds = store.get_dataset()
    lo, hi = analysis.window_bounds(date(2026, 1, 1), date(2026, 1, 31))
    out = {"period": "2026-01-01 to 2026-01-31 (UTC target times)", "data_source": ds.source, "horizons": {}}
    print(f"source: {ds.source}")
    print("| H (h) | hours | MAE (MW) | RMSE (MW) | bias (MW) | nMAE % | P90 abs (MW) | P99 abs (MW) | too high % | P10 actual/forecast |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for h in HORIZONS:
        acc = analysis.accuracy(ds, lo, hi, h)
        s = acc["summary"]
        hours = [r for r in acc["by_hour_utc"] if r["n"]]
        worst = max(hours, key=lambda r: r["mae_mw"])
        best = min(hours, key=lambda r: r["mae_mw"])
        out["horizons"][str(h)] = {"summary": s, "worst_hour_utc": worst, "best_hour_utc": best}
        print(
            f"| {h} | {s['n']} | {s['mae_mw']} | {s['rmse_mw']} | {s['bias_mw']} | {s['nmae_pct']} | "
            f"{s['abs_error_p90_mw']} | {s['abs_error_p99_mw']} | {s['over_forecast_share_pct']} | {s['actual_to_forecast_p10']} |"
        )
        print(f"    worst hour {worst['hour']:02d}:00 MAE {worst['mae_mw']}; best hour {best['hour']:02d}:00 MAE {best['mae_mw']}")
    # Publish cadence and lead-time range of the forecast runs in scope.
    from collections import Counter

    clock = Counter(to_iso(p)[11:16] for p in ds.publish_times)
    leads = [
        (tgt - pub) / 3600
        for tgt, (pubs, _) in ds.forecasts_by_target.items()
        for pub in pubs
        if pub <= tgt
    ]
    out["forecast_runs"] = {
        "count": len(ds.publish_times),
        "publish_clock_times_utc": dict(sorted(clock.items())),
        "max_lead_hours": max(leads),
    }
    print(f"runs: {len(ds.publish_times)}; publish times (UTC): {dict(sorted(clock.items()))}; max lead {max(leads)} h")
    path = ROOT / "docs" / "jan2026_metrics.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
