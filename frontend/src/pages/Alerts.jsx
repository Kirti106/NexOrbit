
import { useState } from "react";
import {
  AlertTriangle,
  Search,
  ShieldAlert,
  Clock,
  Activity,
  X,
  ArrowUpRight,
} from "lucide-react";

import "./Alerts.css";

const alerts = [
  {
    id: "CA-2026-001",
    title: "ISS / OBJECT 48291",
    severity: "CRITICAL",
    distance: "0.8 km",
    velocity: "14.2 km/s",
    time: "22 Nov 2026 · 08:45 UTC",
    probability: "Pending assessment",
    description: "Potentially close orbital encounter requiring further screening.",
  },
  {
    id: "CA-2026-002",
    title: "NOAA 19 / OBJECT 51208",
    severity: "HIGH",
    distance: "2.4 km",
    velocity: "9.8 km/s",
    time: "22 Nov 2026 · 11:20 UTC",
    probability: "Pending assessment",
    description: "Close approach flagged for additional orbital analysis.",
  },
  {
    id: "CA-2026-003",
    title: "TERRA / OBJECT 39120",
    severity: "MEDIUM",
    distance: "6.7 km",
    velocity: "7.4 km/s",
    time: "22 Nov 2026 · 15:10 UTC",
    probability: "Pending assessment",
    description: "Monitoring recommended as the encounter approaches.",
  },
  {
    id: "CA-2026-004",
    title: "GPS BIIR-2 / OBJECT 60123",
    severity: "LOW",
    distance: "12.5 km",
    velocity: "4.6 km/s",
    time: "23 Nov 2026 · 02:30 UTC",
    probability: "Pending assessment",
    description: "Low-priority proximity event in the demonstration catalogue.",
  },
];

const filters = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"];

function Alerts() {
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [selectedAlert, setSelectedAlert] = useState(null);

  const filteredAlerts = alerts.filter((alert) => {
    const matchesFilter =
      activeFilter === "ALL" || alert.severity === activeFilter;

    const matchesSearch =
      alert.title.toLowerCase().includes(search.toLowerCase()) ||
      alert.id.toLowerCase().includes(search.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  const counts = {
    CRITICAL: alerts.filter((a) => a.severity === "CRITICAL").length,
    HIGH: alerts.filter((a) => a.severity === "HIGH").length,
    MEDIUM: alerts.filter((a) => a.severity === "MEDIUM").length,
    LOW: alerts.filter((a) => a.severity === "LOW").length,
  };

  return (
    <div className="alerts-page">
      <div className="alerts-header">
        <div>
          <p className="section-eyebrow">MISSION CONTROL / RISK MONITORING</p>
          <h1>Conjunction Alerts</h1>
          <p>Monitor potential close approaches between orbital objects.</p>
        </div>
        <div className="alerts-demo-status">SIMULATED DEMO DATA</div>
      </div>

      <div className="alert-summary-grid">
        {[
          { label: "CRITICAL", value: counts.CRITICAL },
          { label: "HIGH RISK", value: counts.HIGH },
          { label: "MEDIUM RISK", value: counts.MEDIUM },
          { label: "LOW RISK", value: counts.LOW },
        ].map((item) => (
          <div className="alert-summary-card" key={item.label}>
            <span>{item.label}</span>
            <h2>{item.value}</h2>
            <p>Demo events</p>
          </div>
        ))}
      </div>

      <div className="alerts-toolbar">
        <div className="alerts-search">
          <Search size={18} />
          <input
            placeholder="Search alert or object..."
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
                  {alert.severity}
                </span>
                <span className="alert-id">{alert.id}</span>
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

              <div className="alert-card-footer">
                <span>Assessment pending</span>
                <ArrowUpRight size={17} />
              </div>
            </article>
          ))}

          {filteredAlerts.length === 0 && (
            <div className="alerts-empty">
              No matching alerts found.
            </div>
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
                {selectedAlert.severity}
              </span>

              <h2>{selectedAlert.title}</h2>
              <p>{selectedAlert.description}</p>

              <div className="alert-detail-metric">
                <span>Alert ID</span>
                <strong>{selectedAlert.id}</strong>
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
                <span>Encounter time</span>
                <strong>{selectedAlert.time}</strong>
              </div>
              <div className="alert-detail-metric">
                <span>Collision probability</span>
                <strong>{selectedAlert.probability}</strong>
              </div>

              <p className="alert-disclaimer">
                Demonstration record only. No validated conjunction
                assessment or collision probability is available.
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
        All alert records are simulated frontend examples, not actual
        conjunction warnings.
      </div>
    </div>
  );
}

export default Alerts;
