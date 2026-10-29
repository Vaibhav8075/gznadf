const nf0 = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1 });

export const mw = (v: number | null | undefined) => (v == null ? "–" : `${nf0.format(v)} MW`);
export const gw = (v: number | null | undefined) => (v == null ? "–" : `${nf1.format(v / 1000)} GW`);
export const pct = (v: number | null | undefined) => (v == null ? "–" : `${nf0.format(v)}%`);
export const signedGw = (v: number | null | undefined) =>
  v == null ? "–" : `${v > 0 ? "+" : v < 0 ? "−" : ""}${nf1.format(Math.abs(v) / 1000)} GW`;

// January 2026 is GMT, so UTC labels are also UK local time.
const dayFmt = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
const fullFmt = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "UTC",
});
const hourFmt = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "UTC" });

export const fmtDay = (ms: number) => dayFmt.format(ms);
export const fmtDateTime = (ms: number) => fullFmt.format(ms);
export const fmtHour = (ms: number) => hourFmt.format(ms);

/** Round tick values for a 0-based MW axis, labelled in GW. */
export function mwTicks(maxMw: number, maxTicks = 6): number[] {
  return niceTicks(maxMw, [250, 500, 1000, 2000, 2500, 5000, 10000], maxTicks);
}

/** Round ticks from 0 for a count axis. */
export const countTicks = (max: number) => niceTicks(max, [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500]);

function niceTicks(maxMw: number, steps: number[], maxTicks = 6): number[] {
  const step = steps.find((s) => maxMw / s <= maxTicks - 1) ?? steps[steps.length - 1];
  const top = Math.max(step, Math.ceil(maxMw / step) * step);
  const ticks: number[] = [];
  for (let v = 0; v <= top; v += step) ticks.push(v);
  return ticks;
}
