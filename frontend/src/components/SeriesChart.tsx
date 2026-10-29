import { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SeriesResponse } from "../types";
import type { ChartTheme } from "../theme";
import { fmtDateTime, fmtDay, fmtHour, gw, mwTicks } from "../format";

interface Row {
  t: number;
  actual?: number;
  forecast?: number;
  publish?: number;
  lead?: number;
}

function buildRows(data: SeriesResponse): Row[] {
  const rows = new Map<number, Row>();
  for (const p of data.actual) {
    const t = Date.parse(p.time);
    rows.set(t, { t, actual: p.generation_mw });
  }
  for (const p of data.forecast) {
    const t = Date.parse(p.time);
    const row = rows.get(t) ?? { t };
    row.forecast = p.generation_mw;
    row.publish = Date.parse(p.publish_time);
    row.lead = p.lead_hours;
    rows.set(t, row);
  }
  return [...rows.values()].sort((a, b) => a.t - b.t);
}

interface TipProps {
  active?: boolean;
  payload?: ReadonlyArray<{ payload?: Row }>;
}

function SeriesTooltip({ active, payload }: TipProps) {
  const row = payload?.[0]?.payload;
  if (!active || !row) return null;
  return (
    <div className="tooltip">
      <div className="tooltip-title">{fmtDateTime(row.t)} UTC</div>
      <div>Actual: {row.actual == null ? "–" : gw(row.actual)}</div>
      <div>Forecast: {row.forecast == null ? "–" : gw(row.forecast)}</div>
      {row.publish != null && (
        <div className="muted">
          published {fmtDateTime(row.publish)} ({row.lead} h before)
        </div>
      )}
    </div>
  );
}

export function SeriesChart({ data, theme }: { data: SeriesResponse; theme: ChartTheme }) {
  const rows = useMemo(() => buildRows(data), [data]);
  const spanDays = rows.length ? (rows[rows.length - 1].t - rows[0].t) / 86_400_000 : 0;
  const tickFmt = spanDays <= 2 ? fmtHour : fmtDay;
  const yMax = rows.reduce((m, r) => Math.max(m, r.actual ?? 0, r.forecast ?? 0), 0);
  const yTicks = mwTicks(yMax);

  return (
    <div className="chart chart-tall" role="img" aria-label="Line chart of actual and forecast wind generation">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 28, right: 12, bottom: 0, left: 0 }}>
          <CartesianGrid stroke={theme.grid} vertical={false} />
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={["dataMin", "dataMax"]}
            tickFormatter={tickFmt}
            stroke={theme.axis}
            tick={{ fill: theme.text, fontSize: 12 }}
            minTickGap={24}
          />
          <YAxis
            tickFormatter={(v: number) => `${v / 1000}`}
            ticks={yTicks}
            domain={[0, yTicks[yTicks.length - 1]]}
            stroke={theme.axis}
            tick={{ fill: theme.text, fontSize: 12 }}
            width={40}
            label={{ value: "GW", position: "top", offset: 16, fill: theme.text, fontSize: 12 }}
          />
          <Tooltip content={<SeriesTooltip />} cursor={{ stroke: theme.axis, strokeDasharray: "3 3" }} />
          <Legend wrapperStyle={{ fontSize: 13, color: theme.text }} />
          <Line
            name="Actual (FUELHH)"
            dataKey="actual"
            stroke={theme.actual}
            strokeWidth={2}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
          <Line
            name="Forecast (WINDFOR)"
            dataKey="forecast"
            stroke={theme.forecast}
            strokeWidth={2}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
