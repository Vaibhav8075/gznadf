import { useEffect, useState } from "react";
import { fetchAccuracy, fetchMeta, fetchSeries, type Query } from "./api";
import type { AccuracyResponse, MetaResponse, SeriesResponse } from "./types";
import { useChartTheme } from "./theme";
import { Card } from "./components/Card";
import { Controls } from "./components/Controls";
import { StatTiles } from "./components/StatTiles";
import { Insight } from "./components/Insight";
import { SeriesChart } from "./components/SeriesChart";
import { HorizonChart } from "./components/HorizonChart";
import { ErrorHistogram } from "./components/ErrorHistogram";
import { HourChart } from "./components/HourChart";

const INITIAL: Query = { start: "2026-01-01", end: "2026-01-31", horizon: 4 };

function useDebounced<T>(value: T, ms: number): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return v;
}

export default function App() {
  const theme = useChartTheme();
  const [query, setQuery] = useState<Query>(INITIAL);
  const q = useDebounced(query, 250);
  const [series, setSeries] = useState<SeriesResponse | null>(null);
  const [acc, setAcc] = useState<AccuracyResponse | null>(null);
  const [meta, setMeta] = useState<MetaResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    Promise.all([fetchSeries(q, ctrl.signal), fetchAccuracy(q, ctrl.signal)])
      .then(([s, a]) => {
        setSeries(s);
        setAcc(a);
        setError(null);
      })
      .catch((e: unknown) => {
        if (!ctrl.signal.aborted) setError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false);
      });
    return () => ctrl.abort();
  }, [q]);

  useEffect(() => {
    const ctrl = new AbortController();
    fetchMeta(ctrl.signal).then(setMeta).catch(() => undefined);
    return () => ctrl.abort();
  }, []);

  const s = acc?.summary;

  return (
    <div className="page">
      <header className="masthead">
        <div>
          <p className="eyebrow">UK national wind · Elexon BMRS · January 2026</p>
          <h1>Wind Forecast Monitor</h1>
          <p className="lede">
            How far could the wind forecast be trusted when buying power ahead? Pick a period and a horizon: each hour
            is shown with the latest forecast that had been published at least that many hours earlier.
          </p>
        </div>
        <span className={`status ${loading ? "status-on" : ""}`} aria-live="polite">
          {loading ? "Updating…" : ""}
        </span>
      </header>

      <Controls value={query} onChange={setQuery} />

      {error && (
        <div className="error" role="alert">
          Could not load data: {error}
        </div>
      )}

      {series && (
        <Card
          title="Actual vs forecast generation"
          subtitle={`Actual is half-hourly outturn; forecast is hourly. Times in UTC (= UK time in January). Horizon ${acc?.horizon_h ?? q.horizon} h.`}
        >
          <SeriesChart data={series} theme={theme} />
        </Card>
      )}

      {s && s.n > 0 && (
        <>
          <StatTiles s={s} />
          <Insight s={s} horizon={acc?.horizon_h ?? q.horizon} />
        </>
      )}
      {s && s.n === 0 && <div className="error">No hours in this period have both a forecast and an actual.</div>}

      {acc && (
        <div className="grid">
          <Card
            title="Error grows with horizon"
            subtitle="Mean and 90th-percentile absolute error for the selected dates, at every horizon. Dashed line = current horizon."
          >
            <HorizonChart rows={acc.by_horizon} horizon={acc.horizon_h} theme={theme} />
          </Card>
          <Card
            title="Error distribution"
            subtitle="Hours by forecast − actual. Bars right of zero are hours where less wind arrived than forecast."
          >
            <ErrorHistogram bins={acc.error_histogram} theme={theme} />
          </Card>
          <Card title="Error by time of day" subtitle="Mean absolute error for each delivery hour (UTC).">
            <HourChart rows={acc.by_hour_utc} theme={theme} />
          </Card>
          <Card title="How to read these numbers">
            <ul className="explain">
              <li>
                <strong>Error</strong> is forecast − actual. Positive means the forecast promised more wind than
                arrived, so a buyer relying on it would be short.
              </li>
              <li>
                <strong>Horizon</strong> is the minimum gap between a forecast's publish time and the hour it
                predicts. Day-ahead purchases are made the day before delivery, so for most delivery hours the
                forecast in hand is roughly 12–36 h old.
              </li>
              <li>
                <strong>P90</strong> means 9 of 10 hours were no worse than this value.
              </li>
              <li>Metrics use hours where both a forecast and an actual exist.</li>
            </ul>
          </Card>
        </div>
      )}

      <footer className="footer muted">
        Data: Elexon BMRS FUELHH (fuel type WIND) and WINDFOR, January 2026 targets.
        {meta && (
          <>
            {" "}
            {meta.forecast_publishes} forecast runs used. Source: {meta.data_source}.
          </>
        )}
      </footer>
    </div>
  );
}
