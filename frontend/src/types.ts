export interface Point {
  time: string;
  generation_mw: number;
}

export interface ForecastPoint extends Point {
  publish_time: string;
  lead_hours: number;
}

export interface SeriesResponse {
  start: string;
  end: string;
  horizon_h: number;
  actual: Point[];
  forecast: ForecastPoint[];
}

export interface Summary {
  n: number;
  mae_mw?: number;
  rmse_mw?: number;
  bias_mw?: number;
  mean_actual_mw?: number;
  nmae_pct?: number | null;
  abs_error_p50_mw?: number;
  abs_error_p90_mw?: number;
  abs_error_p99_mw?: number;
  abs_error_max_mw?: number;
  over_forecast_share_pct?: number;
  actual_to_forecast_p10?: number | null;
  actual_to_forecast_p50?: number | null;
  shortfall_p90_mw?: number;
}

export interface HorizonRow {
  horizon_h: number;
  n: number;
  mae_mw: number | null;
  rmse_mw: number | null;
  abs_error_p90_mw: number | null;
  bias_mw: number | null;
}

export interface HourRow {
  hour: number;
  n: number;
  mae_mw: number | null;
  bias_mw: number | null;
}

export interface HistogramBin {
  from_mw: number;
  to_mw: number;
  count: number;
}

export interface AccuracyResponse {
  start: string;
  end: string;
  horizon_h: number;
  summary: Summary;
  by_hour_utc: HourRow[];
  by_horizon: HorizonRow[];
  error_histogram: HistogramBin[];
}

export interface MetaResponse {
  forecast_publishes: number;
  first_publish: string | null;
  last_publish: string | null;
  data_source: string;
  loaded_at: string;
}
