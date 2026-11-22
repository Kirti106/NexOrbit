
import { useEffect } from "react";
import { Viewer, Entity } from "resium";
import { Cartesian3, Color, Ion } from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

const token = import.meta.env.VITE_CESIUM_ION_TOKEN;

function OrbitalGlobe({ satellites = [], onSatelliteSelect }) {
  const error = token ? "" : "Cesium ion access token is missing.";

  useEffect(() => {
    if (!token) return;

    Ion.defaultAccessToken = token;
  }, []);

  if (error) {
    return <div className="cesium-error">{error}</div>;
  }

  if (!token) {
    return (
      <div className="cesium-loading orbital-fallback">
        <div className="fallback-earth">
          <span className="fallback-orbit orbit-one"></span>
          <span className="fallback-orbit orbit-two"></span>
          <span className="fallback-satellite sat-one"></span>
          <span className="fallback-satellite sat-two"></span>
        </div>
        <span>3D VIEW READY</span>
      </div>
    );
  }

  return (
    <div className="cesium-container">
      <Viewer
        full={false}
        animation={false}
        timeline={false}
        baseLayerPicker={false}
        geocoder={false}
        homeButton={false}
        sceneModePicker={false}
        navigationHelpButton={false}
        fullscreenButton={false}
        infoBox={false}
        selectionIndicator={false}
        shouldAnimate={true}
        scene3DOnly={true}
      >
        {satellites.map((satellite) => (
          <Entity
            key={satellite.noradId}
            name={satellite.name}
            position={Cartesian3.fromDegrees(
              satellite.lon,
              satellite.lat,
              300000
            )}
            point={{
              pixelSize: 7,
              color: Color.fromCssColorString("#65b9ff"),
              outlineColor: Color.fromCssColorString("#dff5ff"),
              outlineWidth: 1,
            }}
            description={satellite.name}
            onClick={() => onSatelliteSelect?.(satellite)}
          />
        ))}
      </Viewer>
    </div>
  );
}

export default OrbitalGlobe;
