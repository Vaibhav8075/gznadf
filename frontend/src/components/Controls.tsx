import type { Query } from "../api";

const MIN_DATE = "2026-01-01";
const MAX_DATE = "2026-01-31";
const PRESETS = [
  { h: 4, label: "4 h" },
  { h: 12, label: "12 h" },
  { h: 24, label: "24 h · day-ahead" },
  { h: 36, label: "36 h" },
];

interface Props {
  value: Query;
  onChange: (q: Query) => void;
}

export function Controls({ value, onChange }: Props) {
  const set = (patch: Partial<Query>) => onChange({ ...value, ...patch });

  return (
    <section className="controls" aria-label="Filters">
      <div className="field">
        <label htmlFor="start">From</label>
        <input
          id="start"
          type="date"
          min={MIN_DATE}
          max={MAX_DATE}
          value={value.start}
          onChange={(e) => {
            const start = e.target.value || MIN_DATE;
            set({ start, end: value.end < start ? start : value.end });
          }}
        />
      </div>
      <div className="field">
        <label htmlFor="end">To</label>
        <input
          id="end"
          type="date"
          min={value.start}
          max={MAX_DATE}
          value={value.end}
          onChange={(e) => set({ end: e.target.value || MAX_DATE })}
        />
      </div>
      <div className="field field-grow">
        <label htmlFor="horizon">
          Forecast horizon <strong>{value.horizon} h</strong>
          <span className="muted"> — use the latest forecast published at least this long before each hour</span>
        </label>
        <input
          id="horizon"
          type="range"
          min={0}
          max={48}
          step={1}
          value={value.horizon}
          onChange={(e) => set({ horizon: Number(e.target.value) })}
        />
        <div className="chips" role="group" aria-label="Horizon presets">
          {PRESETS.map((p) => (
            <button
              key={p.h}
              type="button"
              className={`chip ${value.horizon === p.h ? "chip-on" : ""}`}
              aria-pressed={value.horizon === p.h}
              onClick={() => set({ horizon: p.h })}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
