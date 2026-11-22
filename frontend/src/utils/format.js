// Orbit regime from altitude (km). Simple bands, good enough for display.
export function classifyOrbit(altitudeKm) {
  if (altitudeKm == null || Number.isNaN(altitudeKm)) return "LEO";
  if (altitudeKm < 2000) return "LEO";
  if (altitudeKm < 34000) return "MEO";
  return "GEO";
}

export const ORBIT_COLORS = { LEO: "#65b9ff", MEO: "#b794f6", GEO: "#ffca72" };

export function fmtInt(value) {
  return value == null ? "—" : Number(value).toLocaleString("en-US");
}

export function fmtKm(value, digits = 1) {
  return value == null ? "—" : `${Number(value).toLocaleString("en-US", { maximumFractionDigits: digits })} km`;
}

export function fmtUtc(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(date.getUTCDate())} ${date.toLocaleString("en-GB", { month: "short", timeZone: "UTC" })} ${date.getUTCFullYear()} · ${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())} UTC`;
}

export function fmtDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
}

export function fmtProb(value) {
  return value == null ? "—" : Number(value).toExponential(2);
}
