import { useEffect, useMemo, useRef, useState } from "react";
import { Viewer } from "resium";
import {
  Ion,
  Cartesian3,
  Color,
  ImageryLayer,
  OpenStreetMapImageryProvider,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
} from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";
import { ORBIT_COLORS } from "../utils/format";

const token = import.meta.env.VITE_CESIUM_ION_TOKEN;
if (token) Ion.defaultAccessToken = token;

/**
 * satellites: [{ norad_id, name, latitude, longitude, altitude_km, orbit }]
 * track: [{ latitude, longitude, altitude_km }] ground track of the selected object
 */
function OrbitalGlobe({ satellites = [], selectedId = null, track = [], onSatelliteSelect }) {
  const viewerRef = useRef(null);
  const onSelectRef = useRef(onSatelliteSelect);
  const flewRef = useRef(false);
  const [viewer, setViewer] = useState(null);

  useEffect(() => {
    onSelectRef.current = onSatelliteSelect;
  });

  // Without an Ion token the default Earth imagery cannot load, so fall back to OpenStreetMap.
  const baseLayer = useMemo(
    () =>
      token
        ? undefined
        : new ImageryLayer(
            new OpenStreetMapImageryProvider({ url: "https://tile.openstreetmap.org/" })
          ),
    []
  );

  // Grab the Cesium viewer once Resium has created it.
  useEffect(() => {
    const instance = viewerRef.current?.cesiumElement;
    if (instance && !instance.isDestroyed() && instance !== viewer) setViewer(instance);
  });

  // Click picking.
  useEffect(() => {
    if (!viewer) return undefined;
    const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction((event) => {
      const entityId = viewer.scene.pick(event.position)?.id?.id;
      if (typeof entityId === "string" && entityId.startsWith("sat-")) {
        onSelectRef.current?.(Number(entityId.slice(4)));
      }
    }, ScreenSpaceEventType.LEFT_CLICK);
    return () => handler.destroy();
  }, [viewer]);

  // Satellite markers (rebuilt when positions refresh or selection changes).
  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return undefined;

    viewer.entities.suspendEvents();
    const created = satellites.map((satellite) => {
      const selected = satellite.norad_id === selectedId;
      return viewer.entities.add({
        id: `sat-${satellite.norad_id}`,
        name: satellite.name,
        position: Cartesian3.fromDegrees(
          satellite.longitude,
          satellite.latitude,
          Math.max(satellite.altitude_km, 0) * 1000
        ),
        point: {
          pixelSize: selected ? 14 : 5,
          color: Color.fromCssColorString(ORBIT_COLORS[satellite.orbit] || "#ffffff"),
          outlineColor: Color.WHITE,
          outlineWidth: selected ? 2 : 0,
          disableDepthTestDistance: selected ? Number.POSITIVE_INFINITY : 0,
        },
        label: selected
          ? {
              text: satellite.name,
              font: "bold 13px sans-serif",
              fillColor: Color.WHITE,
              showBackground: true,
              backgroundColor: Color.BLACK.withAlpha(0.7),
              pixelOffset: new Cartesian3(0, -24, 0),
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
            }
          : undefined,
      });
    });
    viewer.entities.resumeEvents();

    if (!flewRef.current && satellites.length > 0) {
      flewRef.current = true;
      viewer.camera.flyTo({
        destination: Cartesian3.fromDegrees(20, 15, 22000000),
        duration: 1.5,
      });
    }

    return () => {
      if (viewer.isDestroyed()) return;
      created.forEach((entity) => viewer.entities.remove(entity));
    };
  }, [viewer, satellites, selectedId]);

  // Ground track polyline for the selected object.
  useEffect(() => {
    if (!viewer || viewer.isDestroyed() || track.length < 2) return undefined;

    const entity = viewer.entities.add({
      id: "ground-track",
      polyline: {
        positions: Cartesian3.fromDegreesArrayHeights(
          track.flatMap((p) => [p.longitude, p.latitude, Math.max(p.altitude_km, 0) * 1000])
        ),
        width: 2,
        material: Color.fromCssColorString("#65b9ff").withAlpha(0.9),
      },
    });

    return () => {
      if (!viewer.isDestroyed()) viewer.entities.remove(entity);
    };
  }, [viewer, track]);

  return (
    <div className="cesium-container">
      <Viewer
        ref={viewerRef}
        full={false}
        animation={false}
        timeline={false}
        baseLayerPicker={false}
        baseLayer={baseLayer}
        geocoder={false}
        homeButton={false}
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
