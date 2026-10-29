import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { HourRow } from "../types";
import type { ChartTheme } from "../theme";
import { gw, mwTicks } from "../format";

const hh = (h: number) => String(h).padStart(2, "0");

export function HourChart({ rows, theme }: { rows: HourRow[]; theme: ChartTheme }) {
  const yTicks = mwTicks(Math.max(0, ...rows.map((r) => r.mae_mw ?? 0)));
  return (
    <div className="chart" role="img" aria-label="Mean absolute error by hour of day">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 28, right: 12, bottom: 0, left: 0 }} barCategoryGap={2}>
          <CartesianGrid stroke={theme.grid} vertical={false} />
          <XAxis
            dataKey="hour"
            tickFormatter={hh}
            stroke={theme.axis}
            tick={{ fill: theme.text, fontSize: 12 }}
            interval={2}
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
          <Tooltip
            formatter={(v) => [gw(Number(v)), "Mean absolute error"]}
            labelFormatter={(h) => `${hh(Number(h))}:00 UTC`}
            contentStyle={{ background: theme.surface, borderColor: theme.grid, color: theme.text }}
            cursor={{ fill: theme.grid, opacity: 0.5 }}
          />
          <Bar dataKey="mae_mw" fill={theme.bar} radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
