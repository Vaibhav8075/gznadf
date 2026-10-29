import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { HistogramBin } from "../types";
import type { ChartTheme } from "../theme";
import { countTicks } from "../format";

const binLabel = (b: HistogramBin) => `${b.from_mw / 1000} to ${b.to_mw / 1000} GW`;

export function ErrorHistogram({ bins, theme }: { bins: HistogramBin[]; theme: ChartTheme }) {
  const rows = bins.map((b) => ({ ...b, mid: (b.from_mw + b.to_mw) / 2 }));
  const yTicks = countTicks(Math.max(0, ...bins.map((b) => b.count)));
  return (
    <div className="chart" role="img" aria-label="Distribution of forecast errors">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 28, right: 12, bottom: 20, left: 0 }} barCategoryGap={2}>
          <CartesianGrid stroke={theme.grid} vertical={false} />
          <XAxis
            dataKey="mid"
            tickFormatter={(v: number) => `${v / 1000}`}
            stroke={theme.axis}
            tick={{ fill: theme.text, fontSize: 12 }}
            label={{ value: "forecast − actual (GW)", position: "insideBottom", fill: theme.text, fontSize: 12, dy: 14 }}
            height={40}
            interval="preserveStartEnd"
          />
          <YAxis
            stroke={theme.axis}
            tick={{ fill: theme.text, fontSize: 12 }}
            width={40}
            allowDecimals={false}
            ticks={yTicks}
            domain={[0, yTicks[yTicks.length - 1]]}
            label={{ value: "hours", position: "top", offset: 16, fill: theme.text, fontSize: 12 }}
          />
          <Tooltip
            formatter={(v) => [`${v} hours`, "Count"]}
            labelFormatter={(_, p) => (p?.[0]?.payload ? binLabel(p[0].payload as HistogramBin) : "")}
            contentStyle={{ background: theme.surface, borderColor: theme.grid, color: theme.text }}
            cursor={{ fill: theme.grid, opacity: 0.5 }}
          />
          <Bar dataKey="count" fill={theme.bar} radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
