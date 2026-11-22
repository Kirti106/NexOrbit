import { useMemo, useState } from "react";
import {
  AlertTriangle,
  Search,
  ShieldAlert,
  Clock,
  X,
  ArrowUpRight,
} from "lucide-react";

import { ApiError } from "../components/ApiState";
import { useApi } from "../hooks/useApi";
import { getConjunctions } from "../api/client";
import { fmtProb, fmtUtc } from "../utils/format";
import "./Alerts.css";

const PER_TIER = 100;
const BASIS = "Predicted (SOCRATES-derived), not observed";
const filters = ["ALL", "HIGH", "MEDIUM", "LOW"];

// Fetch each risk tier separately so every tier is represented, then merge by time.
async function loadConjunctions() {
  const minTca = new Date().toISOString();
  const tiers = ["high", "medium", "low"];
  const responses = await Promise.all(
    tiers.map((risk) => getConjunctions({ risk, limit: PER_TIER, minTca }))
  );
  const items = responses
    .flatMap((response) => response.items)
    .sort((a, b) => new Date(a.tca) - new Date(b.tca));
  return { items, generated_at: responses[0].generated_at };
}

function toAlert(item) {
  return {
    id: `${item.norad_id_1}-${item.norad_id_2}-${item.tca}`,
    title: `${item.object_name_1 || item.norad_id_1} / ${item.object_name_2 || item.norad_id_2}`,
    severity: item.risk_tier.toUpperCase(),
    distance: `${item.min_range_km.toFixed(3)} km`,
    velocity: item.rel_speed_kms != null ? `${item.rel_speed_kms.toFixed(2)} km/s` : "—",
    time: fmtUtc(item.tca),
    maxProb: item.max_prob,
    fetchedAt: item.fetched_at,
    ids: `NORAD ${item.norad_id_1} / ${item.norad_id_2}`,
  };
}

function Alerts() {
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [selectedAlert, setSelectedAlert] = useState(null);

  const { data, error, loading } = useApi(loadConjunctions, [], { intervalMs: 300000 });

  const alerts = useMemo(() => (data?.items || []).map(toAlert), [data]);

  const filteredAlerts = alerts.filter((alert) => {
    const matchesFilter = activeFilter === "ALL" || alert.severity === activeFilter;
    const term = search.toLowerCase();
    const matchesSearch =
      alert.title.toLowerCase().includes(term) || alert.ids.toLowerCase().includes(term);
    return matchesFilter && matchesSearch;
  });

  const count = (severity) => {
    const n = alerts.filter((a) => a.severity === severity).length;
    return n >= PER_TIER ? `${n}+` : String(n);
  };

  const asOf = alerts[0]?.fetchedAt;

  return (
    <div className="alerts-page">
      <div className="alerts-header">
        <div>
          <p className="section-eyebrow">MISSION CONTROL / RISK MONITORING</p>
          <h1>Conjunction Alerts</h1>
          <p>Monitor potential close approaches between orbital objects.</p>
        </div>
        <div className="alerts-demo-status">
          {error && !data ? "BACKEND OFFLINE" : asOf ? `PREDICTIONS AS OF ${fmtUtc(asOf).toUpperCase()}` : "LOADING..."}
        </div>
      </div>

      <ApiError message={error} title="Could not load conjunctions" />

      <div className="alert-summary-grid">
        {[
          { label: "HIGH TIER", value: count("HIGH") },
          { label: "MEDIUM TIER", value: count("MEDIUM") },
          { label: "LOW TIER", value: count("LOW") },
          { label: "UPCOMING LOADED", value: alerts.length },
        ].map((item) => (
          <div className="alert-summary-card" key={item.label}>
            <span>{item.label}</span>
            <h2>{loading && !data ? "…" : item.value}</h2>
            <p>Upcoming predicted events</p>
          </div>
        ))}
      </div>

      <div className="alerts-toolbar">
        <div className="alerts-search">
          <Search size={18} />
          <input
            placeholder="Search object name or NORAD ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="alerts-filters">
          {filters.map((filter) => (
            <button
              key={filter}
              className={activeFilter === filter ? "active" : ""}
              onClick={() => setActiveFilter(filter)}
            >
              {filter}
            </button>
          ))}
        </div>
      </div>

      <div className="alerts-layout">
        <div className="alerts-list">
          {filteredAlerts.map((alert) => (
            <article
              key={alert.id}
              className={`alert-card ${alert.severity.toLowerCase()}`}
              onClick={() => setSelectedAlert(alert)}
            >
              <div className="alert-card-top">
                <span className={`severity-tag ${alert.severity.toLowerCase()}`}>
                  <AlertTriangle size={12} />
                  {alert.severity} TIER
                </span>
                <span className="alert-id">{alert.ids}</span>
              </div>

              <h3>{alert.title}</h3>

              <div className="alert-metrics">
                <div>
                  <span>CLOSEST APPROACH</span>
                  <strong>{alert.distance}</strong>
                </div>
                <div>
                  <span>RELATIVE VELOCITY</span>
                  <strong>{alert.velocity}</strong>
                </div>
                <div>
                  <span>ENCOUNTER TIME</span>
                  <strong>{alert.time}</strong>
                </div>
              </div>

              <div
                className="alert-card-footer"
                title={`SOCRATES maximum probability: ${fmtProb(alert.maxProb)} (an estimate, not an observed collision probability)`}
              >
                <span>{BASIS}</span>
                <ArrowUpRight size={17} />
              </div>
            </article>
          ))}

          {!loading && !error && filteredAlerts.length === 0 && (
            <div className="alerts-empty">No matching alerts found.</div>
          )}
        </div>

        <aside className="alert-detail-panel">
          {selectedAlert ? (
            <>
              <div className="alert-detail-heading">
                <h3>ALERT DETAILS</h3>
                <button onClick={() => setSelectedAlert(null)} aria-label="Close alert details">
                  <X size={17} />
                </button>
              </div>

              <span className={`severity-tag ${selectedAlert.severity.toLowerCase()}`}>
                {selectedAlert.severity} TIER
              </span>

              <h2>{selectedAlert.title}</h2>
              <p>{BASIS}. Risk tiers are derived from SOCRATES output and are not observed collision probabilities.</p>

              <div className="alert-detail-metric">
                <span>Objects</span>
                <strong>{selectedAlert.ids}</strong>
              </div>
              <div className="alert-detail-metric">
                <span>Closest approach</span>
                <strong>{selectedAlert.distance}</strong>
              </div>
              <div className="alert-detail-metric">
                <span>Relative velocity</span>
                <strong>{selectedAlert.velocity}</strong>
              </div>
              <div className="alert-detail-metric">
                <span>Time of closest approach</span>
                <strong>{selectedAlert.time}</strong>
              </div>
              <div
                className="alert-detail-metric"
                title="SOCRATES maximum-probability estimate under assumed covariance. Secondary information only."
              >
                <span>SOCRATES max probability</span>
                <strong>{fmtProb(selectedAlert.maxProb)}</strong>
              </div>
              <div className="alert-detail-metric">
                <span>Predictions as of</span>
                <strong>{fmtUtc(selectedAlert.fetchedAt)}</strong>
              </div>

              <p className="alert-disclaimer">
                Constellation self-conjunction artifacts are excluded. Element sets age
                quickly, so treat events as screening results, not warnings.
              </p>
            </>
          ) : (
            <div className="alert-detail-empty">
              <ShieldAlert size={28} />
              <h3>ALERT INTELLIGENCE</h3>
              <p>Select an alert to inspect its encounter information.</p>
            </div>
          )}
        </aside>
      </div>

      <div className="alerts-footnote">
        <Clock size={15} />
        Showing up to {PER_TIER} upcoming events per tier. All events are SOCRATES-derived
        predictions, not observed conjunctions.
      </div>
    </div>
  );
}

export default Alerts;
