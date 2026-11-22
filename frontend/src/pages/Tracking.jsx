import { useEffect, useState } from "react";
import {
  Search,
  Satellite,
  X,
  Orbit,
  Radio,
  Calendar,
  Gauge,
  Crosshair,
} from "lucide-react";

import { getSatellite, getSatellites } from "../api/client";
import "./Tracking.css";

const filters = ["ALL", "LEO", "MEO", "GEO"];

function display(value, suffix = "") {
  return value == null ? "—" : `${value}${suffix}`;
}

function date(value) {
  return value ? new Date(value).toLocaleDateString() : "—";
}

function Tracking() {
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [selectedId, setSelectedId] = useState(null);
  const [selectedSatellite, setSelectedSatellite] = useState(null);
  const [catalogueResult, setCatalogueResult] = useState({
    query: null,
    data: { total: 0, items: [] },
    error: "",
  });
  const queryKey = `${search.trim()}|${activeFilter}`;
  const loading = catalogueResult.query !== queryKey;
  const error = catalogueResult.query === queryKey ? catalogueResult.error : "";
  const catalogue = catalogueResult.data;

  useEffect(() => {
    const controller = new AbortController();
    getSatellites({
      q: search.trim(),
      orbit_class: activeFilter === "ALL" ? "" : activeFilter,
      limit: "100",
      offset: "0",
    }, { signal: controller.signal })
      .then((response) => setCatalogueResult({ query: queryKey, data: response, error: "" }))
      .catch((requestError) => {
        if (requestError.name !== "AbortError") {
          setCatalogueResult({
            query: queryKey,
            data: { total: 0, items: [] },
            error: requestError.message,
          });
        }
      });
    return () => controller.abort();
  }, [search, activeFilter, queryKey]);

  useEffect(() => {
    if (selectedId == null) return undefined;
    const controller = new AbortController();
    getSatellite(selectedId, { signal: controller.signal })
      .then(setSelectedSatellite)
      .catch((requestError) => {
        if (requestError.name !== "AbortError") {
          setCatalogueResult((previous) => ({
            ...previous,
            error: requestError.message,
          }));
        }
      });
    return () => controller.abort();
  }, [selectedId]);

  const selectedDetails = selectedSatellite?.norad_id === selectedId
    ? selectedSatellite
    : null;
  const elements = selectedDetails?.latest_orbital_elements;

  return (
    <div className="tracking-page">
      <div className="tracking-header">
        <p className="section-eyebrow">MISSION CONTROL / CATALOGUE</p>
        <h1>Satellite Tracking</h1>
        <p>Search, explore and inspect objects in Earth&apos;s orbital environment.</p>
      </div>

      <div className="tracking-toolbar">
        <div className="tracking-search">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search satellite name or NORAD ID..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        <div className="orbit-filters">
          {filters.map((filter) => (
            <button
              key={filter}
              className={`orbit-filter ${activeFilter === filter ? "active" : ""}`}
              onClick={() => setActiveFilter(filter)}
            >
              {filter}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="no-satellites" role="alert">{error}</p>}

      <div className="tracking-layout">
        <div className="satellite-table-wrapper">
          <table className="satellite-table">
            <thead>
              <tr>
                <th>OBJECT</th>
                <th>NORAD ID</th>
                <th>ORBIT</th>
                <th>OBJECT TYPE</th>
                <th>UPDATED</th>
              </tr>
            </thead>
            <tbody>
              {catalogue.items.map((satellite) => (
                <tr
                  key={satellite.norad_id}
                  className={selectedId === satellite.norad_id ? "selected-satellite" : ""}
                  onClick={() => setSelectedId(satellite.norad_id)}
                >
                  <td>
                    <span className="satellite-name">
                      <Satellite size={14} style={{ display: "inline", marginRight: "9px", color: "#65b9ff" }} />
                      {satellite.name || "Unnamed object"}
                    </span>
                  </td>
                  <td>{satellite.norad_id}</td>
                  <td><span className="tracking-badge">{satellite.orbit_class || "—"}</span></td>
                  <td>{satellite.object_type || "Unclassified"}</td>
                  <td>{date(satellite.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {loading && <div className="no-satellites">Loading catalogue…</div>}
          {!loading && catalogue.items.length === 0 && !error && (
            <div className="no-satellites">No catalogue objects match this search.</div>
          )}
        </div>

        {selectedId != null && (
          <aside className="satellite-details">
            <div className="details-header">
              <div>
                <p className="section-eyebrow">OBJECT IDENTIFICATION</p>
                <h2>Satellite Details</h2>
              </div>
              <button
                className="close-details"
                onClick={() => setSelectedId(null)}
                aria-label="Close satellite details"
              >
                <X size={19} />
              </button>
            </div>

            {selectedDetails ? (
              <>
                <div className="details-identity">
                  <div className="details-satellite-icon"><Satellite size={30} /></div>
                  <div>
                    <h3>{selectedDetails.name || "Unnamed object"}</h3>
                    <p>NORAD ID: {selectedDetails.norad_id}</p>
                  </div>
                </div>
                <div className="details-status-row">
                  <span className="tracking-badge">{selectedDetails.orbit_class || "Orbit unknown"}</span>
                  <span className="satellite-status">{selectedDetails.object_type || "Unclassified"}</span>
                </div>
                <div className="details-divider" />
                <p className="details-section-label">LATEST ORBITAL ELEMENTS</p>
                <div className="orbital-parameter-grid">
                  <div className="parameter-card">
                    <Orbit size={17} /><span>Apogee</span>
                    <strong>{display(elements?.apogee_km, " km")}</strong>
                  </div>
                  <div className="parameter-card">
                    <Gauge size={17} /><span>Orbital Period</span>
                    <strong>{display(elements?.period_minutes, " min")}</strong>
                  </div>
                  <div className="parameter-card">
                    <Crosshair size={17} /><span>Inclination</span>
                    <strong>{display(elements?.inclination, "°")}</strong>
                  </div>
                  <div className="parameter-card">
                    <Radio size={17} /><span>Eccentricity</span>
                    <strong>{display(elements?.eccentricity)}</strong>
                  </div>
                </div>
                <div className="details-divider" />
                <p className="details-section-label">CATALOGUE INFORMATION</p>
                <div className="mission-detail">
                  <Calendar size={17} />
                  <div><span>Launch Date</span><strong>{date(selectedDetails.launch_date)}</strong></div>
                </div>
                <div className="mission-detail">
                  <Satellite size={17} />
                  <div>
                    <span>Country / Source</span>
                    <strong>{selectedDetails.country || selectedDetails.mission_info?.source || "Not provided"}</strong>
                  </div>
                </div>
                <p className="details-disclaimer">
                  Orbital values are derived from the latest available GP element set.
                  They are estimates, not precise state vectors.
                </p>
              </>
            ) : <p className="no-satellites">Loading object details…</p>}
          </aside>
        )}
      </div>

      <p className="section-description" style={{ marginTop: "18px" }}>
        Showing {catalogue.items.length.toLocaleString()} of {catalogue.total.toLocaleString()} catalogue records.
      </p>
    </div>
  );
}

export default Tracking;
