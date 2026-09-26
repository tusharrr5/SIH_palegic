"use client";
import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import { Map as GLMap, GeoJSONSource, Marker } from "maplibre-gl";
import type { FeatureCollection, Feature, Geometry } from "geojson";
import "maplibre-gl/dist/maplibre-gl.css";
import { LocateFixed, Plus, Minus, Layers, Navigation } from "lucide-react";
import type { MapDetail, Reconstruction } from "@/lib/types";
type Position = { lon: number; lat: number; quality: string };
type Props = {
  detail: MapDetail | null;
  time: number;
  positions: Record<string, Position | null>;
  showTracks: boolean;
  showSlick: boolean;
  showFootprint?: boolean;
  showOrigin?: boolean;
  showGaps?: boolean;
  reconstruction: Reconstruction | null;
  driftFrame: number;
  onSelectTrack: (id: string) => void;
  selectedTrack: string | null;
};
maplibregl.setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");
const empty: FeatureCollection = { type: "FeatureCollection", features: [] };
const COLORS = ["#f97316", "#38bdf8", "#a78bfa"];
function collection(features: Feature[]): FeatureCollection {
  return { type: "FeatureCollection", features };
}
function geoBounds(geometry: Geometry): maplibregl.LngLatBounds {
  const b = new maplibregl.LngLatBounds();
  const walk = (coords: unknown) => {
    if (!Array.isArray(coords)) return;
    if (typeof coords[0] === "number") b.extend(coords as [number, number]);
    else coords.forEach(walk);
  };
  if ("coordinates" in geometry) walk(geometry.coordinates);
  return b;
}
export default function OceanMap({
  detail,
  time,
  positions,
  showTracks,
  showSlick,
  showFootprint = true,
  showOrigin = true,
  showGaps = true,
  reconstruction,
  driftFrame,
  onSelectTrack,
  selectedTrack,
}: Props) {
  const container = useRef<HTMLDivElement>(null),
    map = useRef<GLMap | null>(null),
    markers = useRef<Marker[]>([]);
  const [ready, setReady] = useState(false),
    [failed, setFailed] = useState(false);
  useEffect(() => {
    if (!container.current) return;
    let m: GLMap;
    try {
      m = new maplibregl.Map({
        container: container.current,
        style: {
          version: 8,
          sources: { land: { type: "geojson", data: "/data/land.geojson" } },
          layers: [
            {
              id: "ocean",
              type: "background",
              paint: { "background-color": "#0b222d" },
            },
            {
              id: "land",
              type: "fill",
              source: "land",
              paint: { "fill-color": "#233b40" },
            },
            {
              id: "coast",
              type: "line",
              source: "land",
              paint: {
                "line-color": "#55706d",
                "line-width": 0.8,
                "line-opacity": 0.6,
              },
            },
          ],
        },
        center: [-88.4, 28.6],
        zoom: 6,
        attributionControl: false,
        maxZoom: 14,
        minZoom: 2,
        renderWorldCopies: false,
      });
    } catch {
      setFailed(true);
      return;
    }
    map.current = m;
    m.addControl(
      new maplibregl.AttributionControl({
        compact: true,
        customAttribution:
          "Natural Earth · evidence providers shown in source details",
      }),
      "bottom-right",
    );
    m.addControl(
      new maplibregl.ScaleControl({ unit: "metric" }),
      "bottom-left",
    );
    m.on("load", () => {
      const grid: Feature[] = [];
      for (let x = -180; x <= 180; x += 2)
        grid.push({
          type: "Feature",
          properties: {},
          geometry: {
            type: "LineString",
            coordinates: [
              [x, -80],
              [x, 80],
            ],
          },
        });
      for (let y = -80; y <= 80; y += 2)
        grid.push({
          type: "Feature",
          properties: {},
          geometry: {
            type: "LineString",
            coordinates: [
              [-180, y],
              [180, y],
            ],
          },
        });
      m.addSource("grid", { type: "geojson", data: collection(grid) });
      m.addLayer({
        id: "grid",
        type: "line",
        source: "grid",
        paint: {
          "line-color": "#75969c",
          "line-opacity": 0.09,
          "line-width": 1,
        },
      });
      [
        "slick",
        "tracks",
        "envelope",
        "particles",
        "sar-footprint",
        "origin-region",
        "gaps",
      ].forEach((id) => m.addSource(id, { type: "geojson", data: empty }));

      // SAR Footprint (Cyan)
      m.addLayer({
        id: "sar-footprint-fill",
        type: "fill",
        source: "sar-footprint",
        paint: { "fill-color": "#06b6d4", "fill-opacity": 0.03 },
      });
      m.addLayer({
        id: "sar-footprint-line",
        type: "line",
        source: "sar-footprint",
        paint: {
          "line-color": "#06b6d4",
          "line-width": 1.5,
          "line-dasharray": [4, 2],
          "line-opacity": 0.85,
        },
      });

      // Origin Region / Uncertainty Halo (Purple)
      m.addLayer({
        id: "origin-region-fill",
        type: "fill",
        source: "origin-region",
        paint: { "fill-color": "#a855f7", "fill-opacity": 0.12 },
      });
      m.addLayer({
        id: "origin-region-line",
        type: "line",
        source: "origin-region",
        paint: {
          "line-color": "#c084fc",
          "line-width": 1.8,
          "line-dasharray": [3, 2],
          "line-opacity": 0.9,
        },
      });

      // Slick Fill and Outline (Orange)
      m.addLayer({
        id: "slick-fill",
        type: "fill",
        source: "slick",
        paint: { "fill-color": "#f97316", "fill-opacity": 0.35 },
      });
      m.addLayer({
        id: "slick-glow",
        type: "line",
        source: "slick",
        paint: {
          "line-color": "#fb923c",
          "line-width": 6,
          "line-opacity": 0.25,
        },
      });
      m.addLayer({
        id: "slick-line",
        type: "line",
        source: "slick",
        paint: {
          "line-color": "#ea580c",
          "line-width": 2,
          "line-opacity": 0.95,
        },
      });

      // Envelope and particles
      m.addLayer({
        id: "envelope-fill",
        type: "fill",
        source: "envelope",
        paint: { "fill-color": "#b5a4ff", "fill-opacity": 0.09 },
      });
      m.addLayer({
        id: "envelope-line",
        type: "line",
        source: "envelope",
        paint: {
          "line-color": "#cbbaff",
          "line-dasharray": [3, 3],
          "line-width": 1,
        },
      });

      // AIS Gaps (Dashed Red Line)
      m.addLayer({
        id: "gaps-line",
        type: "line",
        source: "gaps",
        paint: {
          "line-color": "#ef4444",
          "line-width": 2.5,
          "line-dasharray": [2, 2],
          "line-opacity": 0.95,
        },
      });

      // AIS Tracks
      m.addLayer({
        id: "tracks-line",
        type: "line",
        source: "tracks",
        paint: {
          "line-color": ["get", "color"],
          "line-width": 2.5,
          "line-opacity": 0.85,
        },
      });
      m.addLayer({
        id: "particles",
        type: "circle",
        source: "particles",
        paint: {
          "circle-color": "#cbbaff",
          "circle-radius": 2,
          "circle-opacity": 0.7,
        },
      });
      for (const [label, lon, lat, cls] of [
        ["NEW ORLEANS", -90.08, 29.96, "geo-label"],
        ["LOUISIANA", -91.0, 30.4, "geo-label"],
        ["MISSISSIPPI", -89.35, 30.7, "geo-label"],
        ["FLORIDA", -85.2, 30.3, "geo-label"],
        ["GULF OF MEXICO", -88.5, 27.1, "geo-label sea-label"],
        ["GOTHENBURG", 11.97, 57.72, "geo-label"],
        ["KATTEGAT", 11.4, 57.4, "geo-label sea-label"],
        ["CHENNAI", 80.27, 13.08, "geo-label"],
        ["KAMARAJAR / ENNORE PORT", 80.34, 13.26, "geo-label"],
        ["BAY OF BENGAL", 80.8, 12.5, "geo-label sea-label"],
        ["TAMIL NADU", 79.8, 12.8, "geo-label"],
      ] as [string, number, number, string][]) {
        const el = document.createElement("div");
        el.className = cls;
        el.textContent = label;
        new Marker({ element: el }).setLngLat([lon, lat]).addTo(m);
      }
      setReady(true);
    });
    const observer = new ResizeObserver(() => m.resize());
    observer.observe(container.current);
    return () => {
      observer.disconnect();
      m.remove();
      map.current = null;
    };
  }, []);
  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    (m.getSource("slick") as GeoJSONSource).setData(
      detail?.observation
        ? collection([
            {
              type: "Feature",
              properties: {},
              geometry: detail.observation.geometry,
            },
          ])
        : empty,
    );

    // SAR footprint polygon
    const fp = detail?.findings?.sar_footprint;
    const footprintSource = m.getSource("sar-footprint") as GeoJSONSource;
    if (footprintSource) {
      footprintSource.setData(
        showFootprint && fp
          ? collection([{ type: "Feature", properties: {}, geometry: fp }])
          : empty,
      );
    }

    // Origin uncertainty region (radius ~1.5 km circle around collision site)
    const col = detail?.findings?.collision_site;
    const originSource = m.getSource("origin-region") as GeoJSONSource;
    if (originSource) {
      if (showOrigin && col) {
        const r = 0.014;
        const steps = 36;
        const coords: number[][] = [];
        for (let i = 0; i <= steps; i++) {
          const theta = (i / steps) * 2 * Math.PI;
          coords.push([
            col.lon + r * Math.cos(theta),
            col.lat + r * 0.9 * Math.sin(theta),
          ]);
        }
        originSource.setData(
          collection([
            {
              type: "Feature",
              properties: {},
              geometry: { type: "Polygon", coordinates: [coords] },
            },
          ]),
        );
      } else {
        originSource.setData(empty);
      }
    }

    if (detail?.id === "SIH-ENNORE-2017") {
      const b = new maplibregl.LngLatBounds();
      b.extend([80.26, 13.18]);
      b.extend([80.45, 13.32]);
      if (col) b.extend([col.lon, col.lat]);
      if (detail.observation?.geometry) {
        const ob = geoBounds(detail.observation.geometry);
        b.extend(ob.getSouthWest());
        b.extend(ob.getNorthEast());
      }
      m.fitBounds(b, {
        padding: { top: 80, bottom: 80, left: 80, right: 80 },
        duration: 900,
        maxZoom: 12,
      });
    } else if (detail?.trigger === "ais" && detail?.tracks?.length) {
      const b = new maplibregl.LngLatBounds();
      detail.tracks[0].points.forEach((p) => b.extend([p.lon, p.lat]));
      m.fitBounds(b, {
        padding: { top: 80, bottom: 80, left: 80, right: 80 },
        duration: 900,
        maxZoom: 10,
      });
    } else if (detail?.observation) {
      m.fitBounds(geoBounds(detail.observation.geometry), {
        padding: { top: 90, bottom: 70, left: 70, right: 70 },
        duration: 900,
        maxZoom: 8,
      });
    } else if (detail?.tracks?.length) {
      const b = new maplibregl.LngLatBounds();
      detail.tracks.forEach((t) =>
        t.points.forEach((p) => b.extend([p.lon, p.lat])),
      );
      m.fitBounds(b, { padding: 80, maxZoom: 11 });
    }
  }, [detail?.id, detail?.trigger, ready, showFootprint, showOrigin]); // View changes when selecting a case or toggling layers.
  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;

    const isAisFirst = detail?.trigger === "ais";
    const SAR_REVEAL_TIME = new Date("2010-05-17T08:15:00Z").getTime();
    const SAR_SEARCH_TIME = new Date("2010-05-17T07:02:00Z").getTime();
    const ANOMALY_TIME = new Date("2010-05-17T07:00:00Z").getTime();

    const isSlickRevealed = !isAisFirst || time >= SAR_REVEAL_TIME;
    const effectiveShowSlick = showSlick && isSlickRevealed;
    const isSarSearchActive = isAisFirst && time >= SAR_SEARCH_TIME;

    ["slick-fill", "slick-line", "slick-glow"].forEach((id) =>
      m.setLayoutProperty(id, "visibility", effectiveShowSlick ? "visible" : "none"),
    );
    ["sar-footprint-fill", "sar-footprint-line"].forEach((id) =>
      m.setLayoutProperty(id, "visibility", showFootprint && (!isAisFirst || time >= SAR_SEARCH_TIME) ? "visible" : "none"),
    );

    // Update origin uncertainty / targeted search region dynamically with replay time
    const col = detail?.findings?.collision_site;
    const originSource = m.getSource("origin-region") as GeoJSONSource;
    if (originSource) {
      if (showOrigin && col) {
        const r = 0.014;
        const steps = 36;
        const coords: number[][] = [];
        for (let i = 0; i <= steps; i++) {
          const theta = (i / steps) * 2 * Math.PI;
          coords.push([
            col.lon + r * Math.cos(theta),
            col.lat + r * 0.9 * Math.sin(theta),
          ]);
        }
        originSource.setData(
          collection([
            {
              type: "Feature",
              properties: {},
              geometry: { type: "Polygon", coordinates: [coords] },
            },
          ]),
        );
      } else if (showOrigin && isSarSearchActive) {
        // Targeted SAR investigation radius (25 km circle around anomaly coordinates)
        const centerLon = -89.2800;
        const centerLat = 28.4770;
        const rDeg = 0.23;
        const steps = 48;
        const coords: number[][] = [];
        for (let i = 0; i <= steps; i++) {
          const theta = (i / steps) * 2 * Math.PI;
          coords.push([
            centerLon + rDeg * Math.cos(theta),
            centerLat + rDeg * 0.88 * Math.sin(theta),
          ]);
        }
        originSource.setData(
          collection([
            {
              type: "Feature",
              properties: { label: "TARGETED SAR SEARCH AREA" },
              geometry: { type: "Polygon", coordinates: [coords] },
            },
          ]),
        );
      } else {
        originSource.setData(empty);
      }
    }

    m.setLayoutProperty(
      "origin-region-fill",
      "visibility",
      showOrigin && (Boolean(col) || isSarSearchActive) ? "visible" : "none",
    );
    m.setLayoutProperty(
      "origin-region-line",
      "visibility",
      showOrigin && (Boolean(col) || isSarSearchActive) ? "visible" : "none",
    );
    m.setLayoutProperty(
      "gaps-line",
      "visibility",
      showGaps ? "visible" : "none",
    );

    const features: Feature[] = [];
    const gapFeatures: Feature[] = [];

    if (showTracks)
      detail?.tracks?.forEach((t, i) => {
        if (isAisFirst) {
          // Color-coded AIS trajectory for investigated vessel:
          // Green: Normal (06:00-06:42, >07:00)
          // Amber: Unusual speed reduction (06:42-06:48)
          // Red: Course loitering anomaly (06:48-07:00)
          const pts = t.points.filter((p) => new Date(p.time).getTime() <= time);
          const T_AMBER = new Date("2010-05-17T06:42:00Z").getTime();
          const T_RED = new Date("2010-05-17T06:48:00Z").getTime();
          const T_RECOVERY = new Date("2010-05-17T07:00:00Z").getTime();

          for (let j = 1; j < pts.length; j++) {
            const pPrev = pts[j - 1];
            const pCurr = pts[j];
            const tCurr = new Date(pCurr.time).getTime();
            const tPrev = new Date(pPrev.time).getTime();

            if (tCurr - tPrev > 45 * 60000) {
              if (showGaps) {
                gapFeatures.push({
                  type: "Feature",
                  properties: {},
                  geometry: {
                    type: "LineString",
                    coordinates: [
                      [pPrev.lon, pPrev.lat],
                      [pCurr.lon, pCurr.lat],
                    ],
                  },
                });
              }
              continue;
            }

            let color = "#14b8a6"; // Normal teal/green
            if (tCurr >= T_AMBER && tCurr < T_RED) {
              color = "#f59e0b"; // Amber: deceleration
            } else if (tCurr >= T_RED && tCurr <= T_RECOVERY) {
              color = "#ef4444"; // Red: anomalous loitering
            }

            features.push({
              type: "Feature",
              properties: { color },
              geometry: {
                type: "LineString",
                coordinates: [
                  [pPrev.lon, pPrev.lat],
                  [pCurr.lon, pCurr.lat],
                ],
              },
            });
          }

          const pos = positions[t.id];
          if (pos && pos.quality === "interpolated" && pts.length > 0) {
            const lastP = pts[pts.length - 1];
            let color = "#14b8a6";
            if (time >= T_AMBER && time < T_RED) color = "#f59e0b";
            else if (time >= T_RED && time <= T_RECOVERY) color = "#ef4444";

            features.push({
              type: "Feature",
              properties: { color },
              geometry: {
                type: "LineString",
                coordinates: [
                  [lastP.lon, lastP.lat],
                  [pos.lon, pos.lat],
                ],
              },
            });
          }
        } else {
          let segment: number[][] = [];
          const flush = () => {
            if (segment.length > 1)
              features.push({
                type: "Feature",
                properties: { color: COLORS[i % 3] },
                geometry: { type: "LineString", coordinates: segment },
              });
            segment = [];
          };
          t.points.forEach((p, j) => {
            if (new Date(p.time).getTime() > time) return;
            if (
              j > 0 &&
              new Date(p.time).getTime() -
                new Date(t.points[j - 1].time).getTime() >
                45 * 60000
            ) {
              // Gap identified
              if (showGaps) {
                gapFeatures.push({
                  type: "Feature",
                  properties: {},
                  geometry: {
                    type: "LineString",
                    coordinates: [
                      [t.points[j - 1].lon, t.points[j - 1].lat],
                      [p.lon, p.lat],
                    ],
                  },
                });
              }
              flush();
            }
            segment.push([p.lon, p.lat]);
          });
          const pos = positions[t.id];
          if (pos && pos.quality === "interpolated")
            segment.push([pos.lon, pos.lat]);
          flush();
        }
      });

    (m.getSource("tracks") as GeoJSONSource).setData(collection(features));
    const gapSource = m.getSource("gaps") as GeoJSONSource;
    if (gapSource) gapSource.setData(collection(gapFeatures));

    markers.current.forEach((marker) => marker.remove());
    markers.current = [];

    // Collision site marker (Ennore)
    const colMarker = detail?.findings?.collision_site;
    if (colMarker && showOrigin) {
      const el = document.createElement("div");
      el.className = "collision-site-marker";
      el.title = `Documented Collision Origin: ${colMarker.lat.toFixed(4)}°N, ${colMarker.lon.toFixed(4)}°E (BW Maple × Dawn Kancheepuram)`;
      el.innerHTML =
        '<span class="collision-halo"></span><span class="collision-pin">⚠️</span><span class="collision-label">COLLISION ORIGIN</span>';
      markers.current.push(
        new Marker({ element: el }).setLngLat([colMarker.lon, colMarker.lat]).addTo(m),
      );
    }

    // ⚠ AIS ANOMALY marker (revealed when time >= 07:00 UTC)
    if (isAisFirst && time >= ANOMALY_TIME) {
      const el = document.createElement("div");
      el.className = "ais-anomaly-marker";
      el.title = "AIS Behavioural Anomaly: Speed drop + Loitering loop (28.4770°N, 89.2800°W)";
      el.innerHTML =
        '<span class="ais-anomaly-halo"></span><span class="ais-anomaly-pin">⚠️</span><span class="ais-anomaly-label">⚠ AIS ANOMALY</span><span class="ais-anomaly-sub">Speed drop + Loitering</span>';
      markers.current.push(
        new Marker({ element: el }).setLngLat([-89.2800, 28.4770]).addTo(m),
      );
    }

    if (showTracks)
      detail?.tracks?.forEach((t, i) => {
        const p = positions[t.id];
        if (!p) return;
        const el = document.createElement("button");
        const isPrimary = i === 0;
        const vesselColor = isAisFirst ? "#14b8a6" : COLORS[i % 3];
        el.className =
          "vessel-marker" +
          (selectedTrack === t.id ? " selected" : "") +
          (isPrimary ? " primary-candidate" : "");
        el.style.setProperty("--vessel-color", vesselColor);
        el.setAttribute("aria-label", `${t.name}, ${p.quality}`);
        el.title = `${t.name} · ${p.quality}`;
        const report = t.points.findLast(
          (report) => Date.parse(report.time) <= time,
        );
        if (report?.cog != null && (report.sog ?? 0) > 0.5) {
          el.style.setProperty("--vessel-course", `${report.cog}deg`);
          el.title += ` · last reported course ${report.cog.toFixed(1)}°`;
        } else el.classList.add("stationary-marker");
        el.innerHTML = "<span></span>";
        el.onclick = () => onSelectTrack(t.id);
        markers.current.push(
          new Marker({ element: el }).setLngLat([p.lon, p.lat]).addTo(m),
        );
      });
    const source = detail?.findings?.historical_source;
    if (source && !colMarker) {
      const el = document.createElement("div");
      el.className = "wellhead-marker";
      el.title = source.name + " · documented historical source";
      el.textContent = "+";
      markers.current.push(
        new Marker({ element: el })
          .setLngLat([source.lon, source.lat])
          .addTo(m),
      );
    }
  }, [
    detail,
    time,
    positions,
    showTracks,
    showSlick,
    showFootprint,
    showOrigin,
    showGaps,
    selectedTrack,
    ready,
    onSelectTrack,
  ]);
  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    const frame = reconstruction?.frames[driftFrame];
    (m.getSource("envelope") as GeoJSONSource).setData(
      frame
        ? collection([
            { type: "Feature", properties: {}, geometry: frame.envelope },
          ])
        : empty,
    );
    (m.getSource("particles") as GeoJSONSource).setData(
      frame
        ? collection(
            frame.particles.map((p) => ({
              type: "Feature",
              properties: {},
              geometry: { type: "Point", coordinates: p },
            })),
          )
        : empty,
    );
  }, [reconstruction, driftFrame, ready]);
  const recenter = () => {
    if (detail?.observation)
      map.current?.fitBounds(geoBounds(detail.observation.geometry), {
        padding: 80,
        maxZoom: 8,
      });
    else if (detail?.tracks?.length) {
      const b = new maplibregl.LngLatBounds();
      detail.tracks.forEach((t) =>
        t.points.forEach((p) => b.extend([p.lon, p.lat])),
      );
      map.current?.fitBounds(b, { padding: 80, maxZoom: 11 });
    }
  };
  return (
    <div className="map-surface">
      <div ref={container} className="map-canvas" />
      {failed && (
        <div className="map-error">
          This browser could not start the map. Enable WebGL and reload. Case
          evidence remains available.
        </div>
      )}
      <div className="map-coordinates">
        <Navigation size={12} />
        <span>
          {detail?.id === "SIH-ENNORE-2017"
            ? "ENNORE / BAY OF BENGAL"
            : detail?.observation
            ? "NORTHERN GULF OF MEXICO"
            : detail?.tracks?.[0]?.provenance.region?.toUpperCase() ||
              "TRAJECTORY REGION"}
        </span>
        {detail?.id === "SIH-ENNORE-2017" && (
          <span className="coordinate-value">13° 17′ N · 80° 20′ E</span>
        )}
        {detail?.observation && detail?.id !== "SIH-ENNORE-2017" && (
          <span className="coordinate-value">28° 44′ N · 88° 22′ W</span>
        )}
      </div>
      <div className="map-controls">
        <button
          title="Zoom in"
          aria-label="Zoom in"
          onClick={() => map.current?.zoomIn()}
        >
          <Plus size={17} />
        </button>
        <button
          title="Zoom out"
          aria-label="Zoom out"
          onClick={() => map.current?.zoomOut()}
        >
          <Minus size={17} />
        </button>
        <button
          title="Fit evidence"
          aria-label="Fit evidence"
          onClick={recenter}
        >
          <LocateFixed size={18} />
        </button>
      </div>
      <div className="map-legend">
        <span className="legend-heading">
          <Layers size={13} /> MAP LEGEND
        </span>
        {showSlick && detail?.observation && (
          <span>
            <i className="legend-slick" />
            Observed surface slick
          </span>
        )}
        {showTracks && detail?.tracks?.length ? (
          <span>
            <i className="legend-track" />
            {detail?.tracks?.every(
              (t) => t.synthetic || t.provenance?.provenance_class === "TRAINING",
            )
              ? "Training AIS tracks"
              : "AIS tracks"}
          </span>
        ) : null}
        {showGaps && (
          <span>
            <i className="legend-gaps" />
            AIS gaps (&gt;45 min)
          </span>
        )}
        {showFootprint && detail?.findings?.sar_footprint && (
          <span>
            <i className="legend-sar-footprint" />
            Sentinel-1 footprint (CDSE)
          </span>
        )}
        {showOrigin && detail?.findings?.collision_site && (
          <span>
            <i className="legend-origin" />
            Documented collision site
          </span>
        )}
        {reconstruction && (
          <span>
            <i className="legend-drift" />
            Illustrative transport
          </span>
        )}
      </div>
      {(detail?.exercise || detail?.id === "SIH-ENNORE-2017") && (
        <div className="map-training">
          {detail?.id === "SIH-ENNORE-2017" ? (
            <>
              HISTORICAL VALIDATION{" "}
              <span>Training AIS · Illustrative slick · PALEGIC SIH 2026</span>
            </>
          ) : (
            <>
              TRAINING EXERCISE{" "}
              <span>Fictional AIS · historical slick geometry</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
