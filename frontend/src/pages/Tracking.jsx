
import { useState } from "react";
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

import "./Tracking.css";

const satellites = [
  {
    name: "ISS (ZARYA)",
    noradId: "25544",
    orbit: "LEO",
    altitude: "408 km",
    period: "92.7 minutes",
    inclination: "51.6°",
    eccentricity: "0.0006",
    launchDate: "20 November 1998",
    status: "Active",
    purpose: "Crewed research station",
  },
  {
    name: "NOAA 19",
    noradId: "33591",
    orbit: "LEO",
    altitude: "870 km",
    period: "102 minutes",
    inclination: "99.2°",
    eccentricity: "0.0012",
    launchDate: "6 February 2009",
    status: "Active",
    purpose: "Weather observation",
  },
  {
    name: "TERRA",
    noradId: "25994",
    orbit: "LEO",
    altitude: "705 km",
    period: "99 minutes",
    inclination: "98.2°",
    eccentricity: "0.0001",
    launchDate: "18 December 1999",
    status: "Active",
    purpose: "Earth observation",
  },
  {
    name: "GPS BIIR-2",
    noradId: "24876",
    orbit: "MEO",
    altitude: "20,200 km",
    period: "11 hours 58 minutes",
    inclination: "55°",
    eccentricity: "0.010",
    launchDate: "23 July 1997",
    status: "Active",
    purpose: "Navigation",
  },
  {
    name: "GOES 16",
    noradId: "41866",
    orbit: "GEO",
    altitude: "35,786 km",
    period: "23 hours 56 minutes",
    inclination: "0.05°",
    eccentricity: "0.0001",
    launchDate: "19 November 2016",
    status: "Active",
    purpose: "Weather monitoring",
  },
  {
    name: "GOES 18",
    noradId: "51850",
    orbit: "GEO",
    altitude: "35,786 km",
    period: "23 hours 56 minutes",
    inclination: "0.05°",
    eccentricity: "0.0001",
    launchDate: "1 March 2022",
    status: "Active",
    purpose: "Weather monitoring",
  },
];

const filters = ["ALL", "LEO", "MEO", "GEO"];

function Tracking() {
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [selectedSatellite, setSelectedSatellite] = useState(null);

  const filteredSatellites = satellites.filter((satellite) => {
    const matchesSearch =
      satellite.name.toLowerCase().includes(search.toLowerCase()) ||
      satellite.noradId.includes(search);

    const matchesOrbit =
      activeFilter === "ALL" || satellite.orbit === activeFilter;

    return matchesSearch && matchesOrbit;
  });

  return (
    <div className="tracking-page">
      <div className="tracking-header">
        <p className="section-eyebrow">MISSION CONTROL / CATALOGUE</p>
        <h1>Satellite Tracking</h1>
        <p>
          Search, explore and inspect objects in Earth's orbital environment.
        </p>
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
              className={`orbit-filter ${
                activeFilter === filter ? "active" : ""
              }`}
              onClick={() => setActiveFilter(filter)}
            >
              {filter}
            </button>
          ))}
        </div>
      </div>

      <div className="tracking-layout">
        <div className="satellite-table-wrapper">
          <table className="satellite-table">
            <thead>
              <tr>
                <th>SATELLITE</th>
                <th>NORAD ID</th>
                <th>ORBIT</th>
                <th>ALTITUDE</th>
                <th>STATUS</th>
              </tr>
            </thead>

            <tbody>
              {filteredSatellites.map((satellite) => (
                <tr
                  key={satellite.noradId}
                  className={
                    selectedSatellite?.noradId === satellite.noradId
                      ? "selected-satellite"
                      : ""
                  }
                  onClick={() => setSelectedSatellite(satellite)}
                >
                  <td>
                    <span className="satellite-name">
                      <Satellite
                        size={14}
                        style={{
                          display: "inline",
                          marginRight: "9px",
                          color: "#65b9ff",
                        }}
                      />
                      {satellite.name}
                    </span>
                  </td>
                  <td>{satellite.noradId}</td>
                  <td>
                    <span className="tracking-badge">
                      {satellite.orbit}
                    </span>
                  </td>
                  <td>{satellite.altitude}</td>
                  <td>
                    <span className="satellite-status">
                      ● {satellite.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredSatellites.length === 0 && (
            <div className="no-satellites">
              No satellites found. Try another search or filter.
            </div>
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
                <p>NORAD ID: {selectedSatellite.noradId}</p>
              </div>
            </div>

            <div className="details-status-row">
              <span className="tracking-badge">
                {selectedSatellite.orbit}
              </span>
              <span className="satellite-status">
                ● {selectedSatellite.status}
              </span>
            </div>

            <div className="details-divider"></div>

            <p className="details-section-label">ORBITAL PARAMETERS</p>

            <div className="orbital-parameter-grid">
              <div className="parameter-card">
                <Orbit size={17} />
                <span>Altitude</span>
                <strong>{selectedSatellite.altitude}</strong>
              </div>

              <div className="parameter-card">
                <Gauge size={17} />
                <span>Orbital Period</span>
                <strong>{selectedSatellite.period}</strong>
              </div>

              <div className="parameter-card">
                <Crosshair size={17} />
                <span>Inclination</span>
                <strong>{selectedSatellite.inclination}</strong>
              </div>

              <div className="parameter-card">
                <Radio size={17} />
                <span>Eccentricity</span>
                <strong>{selectedSatellite.eccentricity}</strong>
              </div>
            </div>

            <div className="details-divider"></div>

            <p className="details-section-label">MISSION INFORMATION</p>

            <div className="mission-detail">
              <Calendar size={17} />
              <div>
                <span>Launch Date</span>
                <strong>{selectedSatellite.launchDate}</strong>
              </div>
            </div>

            <div className="mission-detail">
              <Satellite size={17} />
              <div>
                <span>Mission Type</span>
                <strong>{selectedSatellite.purpose}</strong>
              </div>
            </div>

            <p className="details-disclaimer">
              Illustrative catalogue values for frontend development.
              Not live orbital measurements.
            </p>
          </aside>
        )}
      </div>

      <p className="section-description" style={{ marginTop: "18px" }}>
        Showing {filteredSatellites.length} of {satellites.length} sample
        satellite records.
      </p>
    </div>
  );
}

export default Tracking;
