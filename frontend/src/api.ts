import type { AccuracyResponse, MetaResponse, SeriesResponse } from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "";

async function getJson<T>(path: string, params: Record<string, string>, signal?: AbortSignal): Promise<T> {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ""}`, { signal });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* not JSON */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export interface Query {
  start: string;
  end: string;
  horizon: number;
}

const toParams = (q: Query) => ({ start: q.start, end: q.end, horizon: String(q.horizon) });

export const fetchSeries = (q: Query, signal?: AbortSignal) =>
  getJson<SeriesResponse>("/api/series", toParams(q), signal);

export const fetchAccuracy = (q: Query, signal?: AbortSignal) =>
  getJson<AccuracyResponse>("/api/accuracy", toParams(q), signal);

export const fetchMeta = (signal?: AbortSignal) => getJson<MetaResponse>("/api/meta", {}, signal);
