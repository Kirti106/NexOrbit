
import { useEffect, useState } from "react";
import { Viewer } from "resium";
import { Ion } from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

const token = import.meta.env.VITE_CESIUM_ION_TOKEN;

function OrbitalGlobe() {
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setError("Cesium ion access token is missing. Check frontend/.env.local");
      return;
    }

    Ion.defaultAccessToken = token;
  }, []);

  if (error) {
    return <div className="cesium-error">{error}</div>;
  }

  if (!token) {
    return <div className="cesium-loading">Checking Cesium configuration...</div>;
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
      />
    </div>
  );
}

export default OrbitalGlobe;
