import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { HorizonRow } from "../types";
import type { ChartTheme } from "../theme";
import { gw, mwTicks, signedGw } from "../format";

interface Props {
  rows: HorizonRow[];
  horizon: number;
  theme: ChartTheme;
}

export function HorizonChart({ rows, horizon, theme }: Props) {
  const yTicks = mwTicks(Math.max(0, ...rows.map((r) => r.abs_error_p90_mw ?? 0)));
  return (
    <>
      <div className="chart" role="img" aria-label="Forecast error by horizon">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 28, right: 12, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={theme.grid} vertical={false} />
            <XAxis
              dataKey="horizon_h"
              type="number"
              domain={[0, 48]}
              ticks={[0, 6, 12, 18, 24, 30, 36, 42, 48]}
              tickFormatter={(v: number) => `${v} h`}
              stroke={theme.axis}
              tick={{ fill: theme.text, fontSize: 12 }}
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
              formatter={(v) => gw(Number(v))}
              labelFormatter={(v) => `Horizon ${v} h`}
              contentStyle={{ background: theme.surface, borderColor: theme.grid, color: theme.text }}
            />
            <Legend wrapperStyle={{ fontSize: 13, color: theme.text }} />
            <ReferenceLine x={horizon} stroke={theme.reference} strokeDasharray="4 4" />
            <Line
              name="Mean absolute error"
              dataKey="mae_mw"
              stroke={theme.actual}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              isAnimationActive={false}
            />
            <Line
              name="P90 absolute error"
              dataKey="abs_error_p90_mw"
              stroke={theme.forecast}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <details className="table-view">
        <summary>View as table</summary>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Horizon</th>
                <th>Hours</th>
                <th>MAE</th>
                <th>RMSE</th>
                <th>P90 |error|</th>
                <th>Bias</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.horizon_h}>
                  <td>{r.horizon_h} h</td>
                  <td>{r.n}</td>
                  <td>{gw(r.mae_mw)}</td>
                  <td>{gw(r.rmse_mw)}</td>
                  <td>{gw(r.abs_error_p90_mw)}</td>
                  <td>{signedGw(r.bias_mw)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
