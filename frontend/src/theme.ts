import { useEffect, useState } from "react";

// Two-series palette (blue = actual, orange = forecast) checked for colour-blind
// separation and contrast on both surfaces.
export interface ChartTheme {
  actual: string;
  forecast: string;
  bar: string;
  grid: string;
  axis: string;
  text: string;
  surface: string;
  reference: string;
}

const light: ChartTheme = {
  actual: "#2a78d6",
  forecast: "#eb6834",
  bar: "#2a78d6",
  grid: "#e1e0d9",
  axis: "#898781",
  text: "#52514e",
  surface: "#fcfcfb",
  reference: "#52514e",
};

const dark: ChartTheme = {
  actual: "#3987e5",
  forecast: "#d95926",
  bar: "#3987e5",
  grid: "#2c2c2a",
  axis: "#898781",
  text: "#c3c2b7",
  surface: "#1a1a19",
  reference: "#c3c2b7",
};

export function useChartTheme(): ChartTheme {
  const query = "(prefers-color-scheme: dark)";
  const [isDark, setDark] = useState(() => window.matchMedia?.(query).matches ?? false);
  useEffect(() => {
    const mq = window.matchMedia?.(query);
    if (!mq) return;
    const onChange = (e: MediaQueryListEvent) => setDark(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return isDark ? dark : light;
}
