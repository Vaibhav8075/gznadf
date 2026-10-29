import type { Summary } from "../types";
import { gw, pct, signedGw } from "../format";

interface Tile {
  label: string;
  value: string;
  note: string;
}

export function StatTiles({ s }: { s: Summary }) {
  const ratio = s.actual_to_forecast_p10;
  const tiles: Tile[] = [
    {
      label: "Mean absolute error",
      value: gw(s.mae_mw),
      note: `${pct(s.nmae_pct)} of mean actual (${gw(s.mean_actual_mw)})`,
    },
    {
      label: "Bias (forecast − actual)",
      value: signedGw(s.bias_mw),
      note: `forecast too high in ${pct(s.over_forecast_share_pct)} of hours`,
    },
    {
      label: "P90 absolute error",
      value: gw(s.abs_error_p90_mw),
      note: `P50 ${gw(s.abs_error_p50_mw)} · P99 ${gw(s.abs_error_p99_mw)}`,
    },
    {
      label: "Wind you can count on",
      value: ratio == null ? "–" : `${Math.round(ratio * 100)}%`,
      note: "of forecast arrived in 9 of 10 hours (P10 of actual ÷ forecast)",
    },
    {
      label: "Cover to hold (P90 shortfall)",
      value: gw(s.shortfall_p90_mw),
      note: "shortfall below forecast was no larger in 9 of 10 hours",
    },
  ];

  return (
    <div className="tiles">
      {tiles.map((t) => (
        <div className="tile" key={t.label}>
          <div className="tile-label">{t.label}</div>
          <div className="tile-value">{t.value}</div>
          <div className="tile-note">{t.note}</div>
        </div>
      ))}
    </div>
  );
}
