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

import { ApiError } from "../components/ApiState";
import { useApi } from "../hooks/useApi";
import { getPosition, searchSatellites } from "../api/client";
import { classifyOrbit, fmtDate, fmtKm } from "../utils/format";
import "./Tracking.css";

const filters = [
  { label: "ALL", type: "" },
  { label: "PAYLOAD", type: "PAYLOAD" },
  { label: "DEBRIS", type: "DEBRIS" },
  { label: "ROCKET BODY", type: "ROCKET BODY" },
  { label: "UNKNOWN", type: "UNKNOWN" },
];

function Tracking() {
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [activeFilter, setActiveFilter] = useState(filters[0]);
  const [selectedSatellite, setSelectedSatellite] = useState(null);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(search.trim()), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const list = useApi(
    () => searchSatellites({ q: debounced, type: activeFilter.type, limit: 100 }),
    [debounced, activeFilter]
  );
  const position = useApi(() => getPosition(selectedSatellite.norad_id), [selectedSatellite?.norad_id], {
    enabled: selectedSatellite != null,
  });

  const satellites = list.data?.items || [];
  const total = list.data?.total ?? 0;
  const pos = selectedSatellite ? position.data : null;

  return (
    <div className="tracking-page">
      <div className="tracking-header">
        <p className="section-eyebrow">MISSION CONTROL / CATALOGUE</p>
        <h1>Satellite Tracking</h1>
        <p>Search, explore and inspect objects in Earth's orbital environment.</p>
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
              key={filter.label}
              className={`orbit-filter ${activeFilter.label === filter.label ? "active" : ""}`}
              onClick={() => setActiveFilter(filter)}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      <ApiError message={list.error} title="Could not load the catalogue" />

      <div className="tracking-layout">
        <div className="satellite-table-wrapper">
          <table className="satellite-table">
            <thead>
              <tr>
                <th>SATELLITE</th>
                <th>NORAD ID</th>
                <th>TYPE</th>
                <th>OWNER</th>
                <th>STATUS</th>
              </tr>
            </thead>

            <tbody>
              {satellites.map((satellite) => (
                <tr
                  key={satellite.norad_id}
                  className={
                    selectedSatellite?.norad_id === satellite.norad_id ? "selected-satellite" : ""
                  }
                  onClick={() => setSelectedSatellite(satellite)}
                >
                  <td>
                    <span className="satellite-name">
                      <Satellite
                        size={14}
                        style={{ display: "inline", marginRight: "9px", color: "#65b9ff" }}
                      />
                      {satellite.name || "(unnamed)"}
                    </span>
                  </td>
                  <td>{satellite.norad_id}</td>
                  <td>
                    <span className="tracking-badge">{satellite.object_type}</span>
                  </td>
                  <td>{satellite.owner_country || "—"}</td>
                  <td>
                    <span className="satellite-status">
                      {satellite.decay_date ? "● Decayed" : "● In orbit"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {list.loading && satellites.length === 0 && (
            <div className="no-satellites">Loading catalogue...</div>
          )}
          {!list.loading && !list.error && satellites.length === 0 && (
            <div className="no-satellites">No satellites found. Try another search or filter.</div>
          )}
        </div>

        {selectedSatellite && (
          <aside className="satellite-details">
            <div className="details-header">
              <div>
                <p className="section-eyebrow">OBJECT IDENTIFICATION</p>
                <h2>Satellite Details</h2>
              </div>

              <button
                className="close-details"
                onClick={() => setSelectedSatellite(null)}
                aria-label="Close satellite details"
              >
                <X size={19} />
              </button>
            </div>

            <div className="details-identity">
              <div className="details-satellite-icon">
                <Satellite size={30} />
              </div>

              <div>
                <h3>{selectedSatellite.name}</h3>
                <p>NORAD ID: {selectedSatellite.norad_id}</p>
              </div>
            </div>

            <div className="details-status-row">
              <span className="tracking-badge">{selectedSatellite.object_type}</span>
              {pos && <span className="tracking-badge">{classifyOrbit(pos.altitude_km)}</span>}
              <span className="satellite-status">
                {selectedSatellite.decay_date ? "● Decayed" : "● In orbit"}
              </span>
            </div>

            <div className="details-divider"></div>

            <p className="details-section-label">CURRENT ORBITAL STATE</p>

            {position.loading && <p className="details-disclaimer">Propagating orbit...</p>}
            {position.error && (
              <p className="details-disclaimer">
                No current orbital elements for this object ({position.error}).
              </p>
            )}

            {pos && (
              <div className="orbital-parameter-grid">
                <div className="parameter-card">
                  <Orbit size={17} />
                  <span>Altitude</span>
                  <strong>{fmtKm(pos.altitude_km)}</strong>
                </div>
                <div className="parameter-card">
                  <Gauge size={17} />
                  <span>Speed</span>
                  <strong>{pos.speed_kms.toFixed(2)} km/s</strong>
                </div>
                <div className="parameter-card">
                  <Crosshair size={17} />
                  <span>Orbit regime</span>
                  <strong>{classifyOrbit(pos.altitude_km)}</strong>
                </div>
                <div className="parameter-card">
                  <Radio size={17} />
                  <span>Radar size</span>
                  <strong>{selectedSatellite.rcs_size || "—"}</strong>
                </div>
              </div>
            )}

            <div className="details-divider"></div>

            <p className="details-section-label">CATALOGUE INFORMATION</p>

            <div className="mission-detail">
              <Calendar size={17} />
              <div>
                <span>Launch Date</span>
                <strong>{fmtDate(selectedSatellite.launch_date)}</strong>
              </div>
            </div>

            <div className="mission-detail">
              <Satellite size={17} />
              <div>
                <span>Owner / Country</span>
                <strong>{selectedSatellite.owner_country || "—"}</strong>
              </div>
            </div>

            <p className="details-disclaimer">
              Position propagated with SGP4 from CelesTrak mean elements. Accuracy
              degrades within days of the element epoch.
            </p>
          </aside>
        )}
      </div>

      <p className="section-description" style={{ marginTop: "18px" }}>
        Showing {satellites.length} of {total.toLocaleString("en-US")} matching objects.
      </p>
    </div>
  );
}

export default Tracking;
