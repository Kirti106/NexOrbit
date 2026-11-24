import axios from "axios";

// Backend base URL, including /api. Set VITE_API_URL in frontend/.env to override.
export const API_URL = import.meta.env.VITE_API_URL || "https://nexorbit-backend.onrender.com/api";

const http = axios.create({ baseURL: API_URL, timeout: 30000 });

const get = (path, params) => http.get(path, { params }).then((res) => res.data);

export const getHealth = () => get("/health");
export const getStats = () => get("/stats");
export const getLiveSatellites = (limit = 500) => get("/satellites/live", { limit });
export const getLivePositions = (limit = 500) => get("/satellites/live", { limit });
export const searchSatellites = ({ q, type, limit = 100 } = {}) =>
  get("/satellites", { q: q || undefined, type: type || undefined, limit });
export const getPosition = (noradId) => get(`/satellites/${noradId}/position`);
export const getGroundTrack = (noradId, hours = 3, stepS = 60) =>
  get(`/satellites/${noradId}/ground-track`, { hours, step_s: stepS });
export const getConjunctions = ({ risk, limit = 100, minTca } = {}) =>
  get("/conjunctions", { risk, limit, min_tca: minTca });
export const getAnomalies = (limit = 10) => get("/anomalies", { limit });

export function describeError(error) {
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail;
    return typeof detail === "string" ? detail : JSON.stringify(detail);
  }
  if (error?.code === "ERR_NETWORK" || error?.message === "Network Error") {
    return `Cannot reach the NexOrbit backend at ${API_URL}. Is it running?`;
  }
  return error?.message || "Unexpected error";
}
