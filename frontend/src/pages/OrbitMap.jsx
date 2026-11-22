import { useEffect, useMemo, useState } from "react";
import { Orbit, Satellite, Activity } from "lucide-react";
import { getLivePositions } from "../api/client";
import OrbitalGlobe from "../components/OrbitalGlobe";
import "./OrbitMap.css";

function orbitForAltitude(altitudeKm) {
  if (altitudeKm < 2000) return "LEO";
  if (altitudeKm < 35786) return "MEO";
  return "GEO";
}

function OrbitMap() {
  const [layers, setLayers] = useState({ LEO: true, MEO: true, GEO: true });
  const [satellites, setSatellites] = useState([]);
  const [selectedSatellite, setSelectedSatellite] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    getLivePositions(500, { signal: controller.signal })
      .then((response) => {
        setSatellites((response.items || []).map((item) => ({
          ...item,
          noradId: item.norad_id,
          lat: item.latitude,
          lon: item.longitude,
          orbit: orbitForAltitude(item.altitude_km),
        })));
      })
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  const visibleSatellites = useMemo(
    () => satellites.filter((satellite) => layers[satellite.orbit]),
    [satellites, layers],
  );

  function toggleLayer(orbit) {
    setLayers((previous) => ({ ...previous, [orbit]: !previous[orbit] }));
    setSelectedSatellite(null);
  }

  return (
    <div className="orbit-map-page">
      <div className="orbit-map-header">
        <div>
          <p className="section-eyebrow">MISSION CONTROL / VISUALISATION</p>
          <h1>Orbital Map</h1>
          <p>Current propagated positions for objects with available GP elements.</p>
        </div>
        <div className="orbit-demo-status">
          ● {error ? "PROPAGATION OFFLINE" : loading ? "LOADING POSITIONS" : "PROPAGATED POSITIONS"}
        </div>
      </div>

      {error && <p className="orbit-map-note" role="alert">{error}</p>}

      <div className="orbit-map-legend">
        <span><i className="legend-dot leo-dot" /> LEO</span>
        <span><i className="legend-dot meo-dot" /> MEO</span>
        <span><i className="legend-dot geo-dot" /> GEO</span>
      </div>

      <div className="orbit-map-layout">
        <div className="orbit-globe-panel">
          <OrbitalGlobe satellites={visibleSatellites} onSatelliteSelect={setSelectedSatellite} />
        </div>

        <aside className="orbit-map-sidebar">
          <div className="orbit-control-card">
            <h3>ORBITAL LAYERS</h3>
            {[
              { id: "LEO", label: "Low Earth Orbit", altitude: "< 2,000 km" },
              { id: "MEO", label: "Medium Earth Orbit", altitude: "2,000–35,786 km" },
              { id: "GEO", label: "Geostationary region", altitude: "≥ 35,786 km" },
            ].map((layer) => (
              <label className="orbit-layer" key={layer.id}>
                <div>{layer.label}<small>{layer.altitude}</small></div>
                <input type="checkbox" checked={layers[layer.id]} onChange={() => toggleLayer(layer.id)} />
              </label>
            ))}
          </div>

          <div className="orbit-control-card">
            <h3>VISIBLE OBJECTS</h3>
            <div className="orbit-object-count">{visibleSatellites.length.toLocaleString()}</div>
            <p className="orbit-selected-object">
              {loading ? "Loading latest positions…" : "Latest propagated catalogue positions"}
            </p>
          </div>

          <div className="orbit-control-card">
            <h3>SELECTED OBJECT</h3>
            {selectedSatellite ? (
              <div className="orbit-selected-object">
                <Satellite size={20} />
                <h4>{selectedSatellite.name}</h4>
                <p>NORAD ID: {selectedSatellite.norad_id}</p>
                <p>Orbit: {selectedSatellite.orbit}</p>
                <p>Altitude: {selectedSatellite.altitude_km.toFixed(1)} km</p>
              </div>
            ) : (
              <p className="orbit-selected-object">
                <Activity size={17} /><br />
                Select a propagated object marker on the globe.
              </p>
            )}
          </div>
        </aside>
      </div>

      <p className="orbit-map-note">
        <Orbit size={14} /> Positions are propagated from the latest available GP element set and are estimates, not precise state vectors.
      </p>
    </div>
  );
}

export default OrbitMap;
