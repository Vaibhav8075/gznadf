import type { Summary } from "../types";
import { gw, pct } from "../format";

// Plain-language reading of the numbers for the purchasing team.
export function Insight({ s, horizon }: { s: Summary; horizon: number }) {
  if (!s.n) return null;
  const ratio = s.actual_to_forecast_p10;
  const over = (s.bias_mw ?? 0) > 0;
  return (
    <div className="insight" role="note">
      <strong>What this means at {horizon} h ahead.</strong>{" "}
      Over {s.n} hourly targets, the forecast was {over ? "too high" : "too low"} on average by{" "}
      {gw(Math.abs(s.bias_mw ?? 0))} and too high in {pct(s.over_forecast_share_pct)} of hours.
      {ratio != null && (
        <>
          {" "}
          In 9 of 10 hours at least {Math.round(ratio * 100)}% of the forecast wind turned up, so a cautious plan
          treats roughly that share of the forecast as firm and buys cover for the rest, or holds about{" "}
          {gw(s.shortfall_p90_mw)} of cover against a shortfall.
        </>
      )}
    </div>
  );
}
