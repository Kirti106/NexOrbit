const API_BASE = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

async function request(path, { params, signal } = {}) {
  const queryParams = params
    ? Object.fromEntries(
      Object.entries(params).filter(([, value]) => value != null && value !== ""),
    )
    : null;
  const query = queryParams ? `?${new URLSearchParams(queryParams)}` : "";
  const response = await fetch(`${API_BASE}${path}${query}`, { signal });
  if (!response.ok) {
    let message = `API request failed (${response.status})`;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {
      // Keep the HTTP status message when the server does not return JSON.
    }
    throw new Error(message);
  }
  return response.json();
}

export const getStats = (options) => request("/analytics/stats", options);
export const getAnalytics = (period, options) =>
  request("/analytics", { ...options, params: { period } });
export const getSatellites = (params, options) =>
  request("/satellites", { ...options, params });
export const getSatellite = (noradId, options) =>
  request(`/satellites/${encodeURIComponent(noradId)}`, options);
export const getLivePositions = (limit = 100, options) =>
  request("/satellites/live", { ...options, params: { limit } });
export const getConjunctions = (params, options) =>
  request("/conjunctions", { ...options, params });
