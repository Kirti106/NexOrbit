import { useCallback, useMemo, useState } from "react";
import { Orbit, Satellite, Activity } from "lucide-react";
import OrbitalGlobe from "../components/OrbitalGlobe";
import { ApiError } from "../components/ApiState";
import { useApi } from "../hooks/useApi";
import { getGroundTrack, getLiveSatellites } from "../api/client";
import { classifyOrbit, fmtKm, fmtUtc } from "../utils/format";
import "./OrbitMap.css";

const LAYERS = [
  { id: "LEO", label: "Low Earth Orbit", altitude: "below 2,000 km" },
  { id: "MEO", label: "Medium Earth Orbit", altitude: "2,000–34,000 km" },
  { id: "GEO", label: "Geostationary / high orbit", altitude: "above ~34,000 km" },
];

function OrbitMap() {
  const [layers, setLayers] = useState({ LEO: true, MEO: true, GEO: true });
  const [selectedId, setSelectedId] = useState(null);

  const live = useApi(() => getLiveSatellites(500), [], { intervalMs: 30000 });
  const trackState = useApi(() => getGroundTrack(selectedId, 3, 60), [selectedId], {
    enabled: selectedId != null,
  });

  const satellites = useMemo(
    () =>
      (live.data?.items || []).map((item) => ({
        ...item,
        orbit: classifyOrbit(item.altitude_km),
      })),
    [live.data]
  );

  const visible = useMemo(
    () => satellites.filter((satellite) => layers[satellite.orbit]),
    [satellites, layers]
  );

  const selected = satellites.find((satellite) => satellite.norad_id === selectedId) || null;
  const track = selectedId != null ? trackState.data?.points || [] : [];

  const handleSelect = useCallback((id) => setSelectedId(id), []);

  function toggleLayer(orbit) {
    setLayers((previous) => ({ ...previous, [orbit]: !previous[orbit] }));
    setSelectedId(null);
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
          {live.error && !live.data
            ? "● BACKEND OFFLINE"
            : live.data
              ? `● LIVE · updated ${fmtUtc(live.data.generated_at)}`
              : "● LOADING..."}
        </div>
      </div>

      <ApiError message={live.error} title="Live positions unavailable" />

      <div className="orbit-map-legend">
        <span><i className="legend-dot leo-dot"></i> LEO</span>
        <span><i className="legend-dot meo-dot"></i> MEO</span>
        <span><i className="legend-dot geo-dot"></i> GEO</span>
      </div>

      <div className="orbit-map-layout">
        <div className="orbit-globe-panel">
          <OrbitalGlobe
            satellites={visible}
            selectedId={selectedId}
            track={track}
            onSatelliteSelect={handleSelect}
          />
        </div>

        <aside className="orbit-map-sidebar">
          <div className="orbit-control-card">
            <h3>ORBITAL LAYERS</h3>
            {LAYERS.map((layer) => (
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
            <div className="orbit-object-count">{visible.length}</div>
            <p className="orbit-selected-object">
              of {satellites.length} objects in the live sample
            </p>
          </div>

          <div className="orbit-control-card">
            <h3>SELECTED OBJECT</h3>
            {selected ? (
              <div className="orbit-selected-object">
                <Satellite size={20} />
                <h4>{selected.name}</h4>
                <p>NORAD ID: {selected.norad_id}</p>
                <p>Type: {selected.object_type}</p>
                <p>Orbit: {selected.orbit}</p>
                <p>Altitude: {fmtKm(selected.altitude_km)}</p>
                <p>
                  Lat / Lon: {selected.latitude.toFixed(2)}°, {selected.longitude.toFixed(2)}°
                </p>
                <p>
                  {trackState.loading
                    ? "Loading 3 h ground track..."
                    : trackState.error
                      ? "Ground track unavailable"
                      : "Showing next 3 h ground track"}
                </p>
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
        <Orbit size={14} /> Positions are SGP4 estimates from CelesTrak mean elements
        (a sample of up to 500 objects, refreshed every 30 s). Accuracy degrades as
        element sets age.
      </p>
    </div>
  );
}

export default OrbitMap;
