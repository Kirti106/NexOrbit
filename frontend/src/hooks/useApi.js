import { useEffect, useState } from "react";
import { describeError } from "../api/client";

/**
 * Run an async fetcher on mount / when deps change, optionally polling.
 * Keeps the previous data on screen if a refresh fails.
 * Returns { data, error, loading }.
 */
export function useApi(fetcher, deps = [], { intervalMs = 0, enabled = true } = {}) {
  const [state, setState] = useState({ data: null, error: null, loading: enabled });

  useEffect(() => {
    if (!enabled) {
      setState({ data: null, error: null, loading: false });
      return undefined;
    }

    let cancelled = false;
    setState((previous) => ({ ...previous, loading: true }));

    const run = async () => {
      try {
        const data = await fetcher();
        if (!cancelled) setState({ data, error: null, loading: false });
      } catch (error) {
        if (!cancelled) {
          setState((previous) => ({
            data: previous.data,
            error: describeError(error),
            loading: false,
          }));
        }
      }
    };

    run();
    const timer = intervalMs > 0 ? setInterval(run, intervalMs) : null;

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, enabled, intervalMs]);

  return state;
}
