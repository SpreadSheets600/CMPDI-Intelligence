import { useEffect, useState } from "react";
import { getJSON } from "../api.js";

// Fetch page data once on mount. Returns {data, error, reload}.
export function usePageData(url) {
  const [state, setState] = useState({ data: null, error: null });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, error: null }));
    getJSON(url)
      .then((data) => alive && setState({ data, error: null }))
      .catch((e) => alive && setState({ data: null, error: e.message }));
    return () => {
      alive = false;
    };
  }, [url, tick]);
  return { ...state, reload: () => setTick((t) => t + 1) };
}

// Poll a JSON endpoint on an interval; only state changes re-render.
export function usePolling(url, intervalMs = 2500) {
  const [data, setData] = useState(null);
  useEffect(() => {
    let alive = true;
    let last = null;
    const tick = async () => {
      try {
        const fresh = await getJSON(url);
        const payload = JSON.stringify(fresh);
        if (alive && payload !== last) {
          last = payload;
          setData(fresh);
        }
      } catch {
        /* server briefly unavailable: keep last render */
      }
    };
    tick();
    const id = setInterval(tick, intervalMs);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [url, intervalMs]);
  return data;
}

// Search params as a plain object with a setter that preserves other keys.
export function useQueryParams() {
  const params = new URLSearchParams(window.location.search);
  const set = (patch) => {
    const next = new URLSearchParams(window.location.search);
    for (const [k, v] of Object.entries(patch)) {
      if (v) next.set(k, v);
      else next.delete(k);
    }
    window.location.search = next.toString();
  };
  return [Object.fromEntries(params), set];
}

// Canvas visuals read theme colors from CSS variables so they restyle
// instantly when the theme flips (used by graph + insights chart).
export function cmpdiColors() {
  const css = getComputedStyle(document.documentElement);
  const v = (name, fallback) => {
    const raw = css.getPropertyValue(name).trim();
    if (!raw) return fallback;
    const [r, g, b] = raw.split(/\s+/).map(Number);
    return `rgb(${r}, ${g}, ${b})`;
  };
  return {
    coal: v("--c-coal", "#d97706"),
    ink: v("--c-ink", "#1c1917"),
    paper: v("--c-paper", "#fafaf9"),
    surface: v("--c-surface", "#ffffff"),
    seam: v("--c-seam", "#e7e5e4"),
    muted1: v("--c-muted1", "#a8a29e"),
    muted2: v("--c-muted2", "#78716c"),
    muted3: v("--c-muted3", "#57534e"),
    dark: document.documentElement.classList.contains("dark"),
  };
}
