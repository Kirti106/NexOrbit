import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Search,
  ShieldAlert,
  Clock,
  X,
  ArrowUpRight,
} from "lucide-react";

import { getConjunctions } from "../api/client";
import "./Alerts.css";

const filters = ["ALL", "HIGH", "MEDIUM", "LOW"];

function formatNumber(value, suffix = "") {
  return value == null ? "—" : `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}${suffix}`;
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString() : "Time unavailable";
}

function Alerts() {
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [conjunctions, setConjunctions] = useState({ total: 0, items: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    getConjunctions({ limit: "500", include_artifacts: "false" }, { signal: controller.signal })
      .then(setConjunctions)
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  const alerts = useMemo(() => conjunctions.items.map((item) => ({
    ...item,
    severity: item.risk_tier.toUpperCase(),
    title: `${item.object_name_1 || `NORAD ${item.norad_id_1}`} / ${item.object_name_2 || `NORAD ${item.norad_id_2}`}`,
  })), [conjunctions.items]);
  const filteredAlerts = alerts.filter((alert) => {
    const matchesFilter = activeFilter === "ALL" || alert.severity === activeFilter;
    const query = search.toLowerCase();
    const matchesSearch = alert.title.toLowerCase().includes(query) ||
      String(alert.id).includes(query) ||
      String(alert.norad_id_1).includes(query) ||
      String(alert.norad_id_2).includes(query);
    return matchesFilter && matchesSearch;
  });
  const counts = Object.fromEntries(
    ["HIGH", "MEDIUM", "LOW"].map((tier) => [
      tier,
      alerts.filter((item) => item.severity === tier).length,
    ]),
  );

  return (
    <div className="alerts-page">
      <div className="alerts-header">
        <div>
          <p className="section-eyebrow">MISSION CONTROL / RISK MONITORING</p>
          <h1>Conjunction Alerts</h1>
          <p>Review predicted close approaches from the SOCRATES dataset.</p>
        </div>
        <div className="alerts-demo-status">PREDICTED, NOT OBSERVED</div>
      </div>

      {error && <p className="alerts-footnote" role="alert">{error}</p>}

      <div className="alert-summary-grid">
        {[
          { label: "HIGH RISK", value: counts.HIGH },
          { label: "MEDIUM RISK", value: counts.MEDIUM },
          { label: "LOW RISK", value: counts.LOW },
          { label: "TOTAL MATCHES", value: conjunctions.total },
        ].map((item) => (
          <div className="alert-summary-card" key={item.label}>
            <span>{item.label}</span>
            <h2>{item.value.toLocaleString()}</h2>
            <p>{item.label === "TOTAL MATCHES" ? "Dataset records" : "Loaded source events"}</p>
          </div>
        ))}
      </div>

      <div className="alerts-toolbar">
        <div className="alerts-search">
          <Search size={18} />
          <input
            placeholder="Search event, object name or NORAD ID..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
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
                  <AlertTriangle size={12} />{alert.severity}
                </span>
                <span className="alert-id">EVENT {alert.id}</span>
              </div>
              <h3>{alert.title}</h3>
              <div className="alert-metrics">
                <div><span>CLOSEST APPROACH</span><strong>{formatNumber(alert.min_range_km, " km")}</strong></div>
                <div><span>RELATIVE VELOCITY</span><strong>{formatNumber(alert.rel_speed_kms, " km/s")}</strong></div>
                <div><span>ENCOUNTER TIME (UTC)</span><strong>{formatTime(alert.tca)}</strong></div>
              </div>
              <div className="alert-card-footer">
                <span>Predicted encounter · probability estimate {formatNumber(alert.max_prob)}</span>
                <ArrowUpRight size={17} />
              </div>
            </article>
          ))}
          {loading && <div className="alerts-empty">Loading conjunction dataset…</div>}
          {!loading && filteredAlerts.length === 0 && !error && (
            <div className="alerts-empty">No matching conjunction records found.</div>
          )}
        </div>

        <aside className="alert-detail-panel">
          {selectedAlert ? (
            <>
              <div className="alert-detail-heading">
                <h3>EVENT DETAILS</h3>
                <button onClick={() => setSelectedAlert(null)} aria-label="Close event details"><X size={17} /></button>
              </div>
              <span className={`severity-tag ${selectedAlert.severity.toLowerCase()}`}>{selectedAlert.severity}</span>
              <h2>{selectedAlert.title}</h2>
              <p>SOCRATES-predicted close approach. Risk tier is a derived screening category and is not a validated collision probability.</p>
              <div className="alert-detail-metric"><span>Event ID</span><strong>{selectedAlert.id}</strong></div>
              <div className="alert-detail-metric"><span>Closest approach</span><strong>{formatNumber(selectedAlert.min_range_km, " km")}</strong></div>
              <div className="alert-detail-metric"><span>Relative velocity</span><strong>{formatNumber(selectedAlert.rel_speed_kms, " km/s")}</strong></div>
              <div className="alert-detail-metric"><span>Encounter time</span><strong>{formatTime(selectedAlert.tca)}</strong></div>
              <div className="alert-detail-metric"><span>Maximum probability estimate</span><strong>{formatNumber(selectedAlert.max_prob)}</strong></div>
              <p className="alert-disclaimer">Predicted event, not an observed collision. Source estimates depend on supplied orbital and covariance data.</p>
            </>
          ) : (
            <div className="alert-detail-empty">
              <ShieldAlert size={28} />
              <h3>ALERT INTELLIGENCE</h3>
              <p>Select a conjunction to inspect its source information.</p>
            </div>
          )}
        </aside>
      </div>

      <div className="alerts-footnote">
        <Clock size={15} />
        Showing {filteredAlerts.length.toLocaleString()} of {conjunctions.total.toLocaleString()} matching records; event times are shown in your local timezone.
      </div>
    </div>
  );
}

export default Alerts;
