
import { useState } from "react";
import { Orbit, Satellite, Activity } from "lucide-react";
import OrbitalGlobe from "../components/OrbitalGlobe";
import "./OrbitMap.css";


const demoSatellites = [
  { name: "ISS (ZARYA)", noradId: "25544", orbit: "LEO", lat: 20, lon: -90 },
  { name: "NOAA 19", noradId: "33591", orbit: "LEO", lat: 35, lon: -75 },
  { name: "TERRA", noradId: "25994", orbit: "LEO", lat: -20, lon: -100 },
  { name: "GPS BIIR-2", noradId: "24876", orbit: "MEO", lat: 10, lon: -65 },
  { name: "GOES 16", noradId: "41866", orbit: "GEO", lat: 0, lon: -80 },
  { name: "GOES 18", noradId: "51850", orbit: "GEO", lat: 0, lon: -110 },
];

function OrbitMap() {
  const [layers, setLayers] = useState({
    LEO: true,
    MEO: true,
    GEO: true,
  });

  const [selectedSatellite, setSelectedSatellite] = useState(null);

  const visibleSatellites = demoSatellites.filter(
    (satellite) => layers[satellite.orbit]
  );

  function toggleLayer(orbit) {
    setLayers((previous) => ({
      ...previous,
      [orbit]: !previous[orbit],
    }));

    setSelectedSatellite(null);
  }

  return (
    <div className="orbit-map-page">
      <div className="orbit-map-header">
        <div>
          <p className="section-eyebrow">MISSION CONTROL / VISUALISATION</p>
          <h1>Orbital Map</h1>
          <p>Explore satellite objects and orbital environments around Earth.</p>
        </div>

        <div className="orbit-demo-status">
          ● SIMULATED DEMO DATA
        </div>
      </div>

      <div className="orbit-map-legend">
        <span><i className="legend-dot leo-dot"></i> LEO</span>
        <span><i className="legend-dot meo-dot"></i> MEO</span>
        <span><i className="legend-dot geo-dot"></i> GEO</span>
        </div>

      <div className="orbit-map-layout">
        <div className="orbit-globe-panel">
          <OrbitalGlobe
            satellites={visibleSatellites}
            onSatelliteSelect={setSelectedSatellite}
          />
        </div>

        <aside className="orbit-map-sidebar">
          <div className="orbit-control-card">
            <h3>ORBITAL LAYERS</h3>

            {[
              { id: "LEO", label: "Low Earth Orbit", altitude: "160–2,000 km" },
              { id: "MEO", label: "Medium Earth Orbit", altitude: "2,000–35,786 km" },
              { id: "GEO", label: "Geostationary Orbit", altitude: "Approximately 35,786 km" },
            ].map((layer) => (
              <label className="orbit-layer" key={layer.id}>
                <div>
                  {layer.label}
                  <small>{layer.altitude}</small>
                </div>

                <input
                  type="checkbox"
                  checked={layers[layer.id]}
                  onChange={() => toggleLayer(layer.id)}
                />
              </label>
            ))}
          </div>

          <div className="orbit-control-card">
            <h3>VISIBLE OBJECTS</h3>
            <div className="orbit-object-count">
              {visibleSatellites.length}
            </div>
            <p className="orbit-selected-object">
              Demo satellite objects displayed on the globe
            </p>
          </div>

          <div className="orbit-control-card">
            <h3>SELECTED OBJECT</h3>

            {selectedSatellite ? (
              <div className="orbit-selected-object">
                <Satellite size={20} />
                <h4>{selectedSatellite.name}</h4>
                <p>NORAD ID: {selectedSatellite.noradId}</p>
                <p>Orbit: {selectedSatellite.orbit}</p>
              </div>
            ) : (
              <p className="orbit-selected-object">
                <Activity size={17} />
                <br />
                Select a satellite marker on the globe to inspect it.
              </p>
            )}
          </div>
        </aside>
      </div>

      <p className="orbit-map-note">
        <Orbit size={14} /> Demo positions are illustrative and do not
        represent current satellite locations or calculated orbital paths.
      </p>
    </div>
  );
}

export default OrbitMap;
