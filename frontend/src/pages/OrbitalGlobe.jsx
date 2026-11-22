
import { useEffect, useRef } from "react";
import { Viewer } from "resium";
import {
  Ion,
  Cartesian3,
  Color,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
} from "cesium";

import "cesium/Build/Cesium/Widgets/widgets.css";

const token = import.meta.env.VITE_CESIUM_ION_TOKEN;

const colors = {
  LEO: Color.fromCssColorString("#65b9ff"),
  MEO: Color.fromCssColorString("#c49aff"),
  GEO: Color.fromCssColorString("#ffca72"),
};

const heights = {
  LEO: 450000,
  MEO: 900000,
  GEO: 1500000,
};

function OrbitalGlobe({ satellites = [], onSatelliteSelect }) {
  const viewerRef = useRef(null);
  const ready = Boolean(token);
  const error = token ? "" : "Cesium ion token is missing.";

  useEffect(() => {
    if (!token) return;
    Ion.defaultAccessToken = token;
  }, []);

  useEffect(() => {
    const viewer = viewerRef.current?.cesiumElement;

    if (!viewer || viewer.isDestroyed()) return;

    // Focus the globe on the demo satellite positions
    viewer.camera.flyTo({
        destination: Cartesian3.fromDegrees(-90, 20, 18000000),
        duration: 1.5,
    });

    const createdEntities = [];

    // Temporary diagnostic marker: large red marker over North America.
    const testMarker = viewer.entities.add({
      name: "TEST SATELLITE",
      position: Cartesian3.fromDegrees(-90, 20, 1200000),
      point: {
        pixelSize: 24,
        color: Color.RED,
        outlineColor: Color.WHITE,
        outlineWidth: 4,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
      label: {
        text: "TEST SATELLITE",
        font: "bold 16px sans-serif",
        fillColor: Color.WHITE,
        showBackground: true,
        backgroundColor: Color.BLACK,
        pixelOffset: new Cartesian3(0, -30, 0),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    });

    createdEntities.push(testMarker);

    satellites.forEach((satellite) => {
      const height = heights[satellite.orbit] || heights.LEO;
      const color = colors[satellite.orbit] || Color.WHITE;

      const marker = viewer.entities.add({
        name: satellite.name,
        position: Cartesian3.fromDegrees(
          satellite.lon,
          satellite.lat,
          height
        ),
        point: {
          pixelSize: 18,
          color,
          outlineColor: Color.WHITE,
          outlineWidth: 3,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        label: {
          text: satellite.name,
          font: "bold 12px sans-serif",
          fillColor: Color.WHITE,
          showBackground: true,
          backgroundColor: Color.BLACK,
          pixelOffset: new Cartesian3(0, -24, 0),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        properties: {
          noradId: satellite.noradId,
        },
      });

      createdEntities.push(marker);
    });

    console.log("Cesium viewer:", viewer);
    console.log("Entities added:", createdEntities.length);
    console.log("Entity collection:", viewer.entities.values.length);

    const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);

    handler.setInputAction((event) => {
      const picked = viewer.scene.pick(event.position);
      const id = picked?.id;

      if (!id?.properties?.noradId) return;

      const noradId = id.properties.noradId.getValue();
      const selected = satellites.find(
        (satellite) => satellite.noradId === noradId
      );

      if (selected) onSatelliteSelect?.(selected);
    }, ScreenSpaceEventType.LEFT_CLICK);

    return () => {
      handler.destroy();
      createdEntities.forEach((entity) => viewer.entities.remove(entity));
    };
  }, [satellites, onSatelliteSelect, ready]);

  if (error) return <div className="cesium-error">{error}</div>;
  if (!ready) return <div className="cesium-loading">Loading Earth...</div>;

  return (
    <div className="cesium-container">
      <Viewer
        ref={viewerRef}
        full={false}
        animation={false}
        timeline={false}
        baseLayerPicker={false}
        geocoder={false}
        homeButton
        sceneModePicker={false}
        navigationHelpButton={false}
        fullscreenButton={false}
        infoBox={false}
        selectionIndicator={false}
        shouldAnimate
      />
    </div>
  );
}

export default OrbitalGlobe;
