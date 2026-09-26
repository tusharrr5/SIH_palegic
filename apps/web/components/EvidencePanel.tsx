"use client";
import { useState } from "react";
import {
  ArrowUpRight,
  ShieldCheck,
  Radio,
  Satellite,
  FileText,
  ArrowRight,
  Check,
  Download,
  AlertCircle,
  Wind,
  Waves,
  LoaderCircle,
  Clock,
} from "lucide-react";
import type { CaseDetail, Reconstruction } from "@/lib/types";
import { api, date, utc, area, statusLabel } from "@/lib/api";
type Props = {
  detail: CaseDetail;
  authority: boolean;
  tab: string;
  setTab: (tab: string) => void;
  selectedTrack: string | null;
  onSelectTrack: (id: string) => void;
  onLogin: () => void;
  onRefresh: () => void;
  reconstruction: Reconstruction | null;
  onReconstruction: (r: Reconstruction | null) => void;
  driftFrame: number;
  setDriftFrame: (n: number) => void;
  onOpenReport?: () => void;
};
export default function EvidencePanel({
  detail: d,
  authority,
  tab,
  setTab,
  selectedTrack,
  onSelectTrack,
  onLogin,
  onRefresh,
  reconstruction,
  onReconstruction,
  driftFrame,
  setDriftFrame,
  onOpenReport,
}: Props) {
  const [note, setNote] = useState(""),
    [status, setStatus] = useState(d.status),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [saved, setSaved] = useState(false);
  const obs = d.observation;
  return (
    <aside className="evidence-panel">
      <div className="panel-kicker">
        <span className={"tiny-dot " + (d.exercise ? "amber" : d.id === "SIH-ENNORE-2017" ? "amber" : "")} />
        {d.exercise
          ? "TRAINING CASE"
          : d.id === "SIH-ENNORE-2017"
          ? "HISTORICAL VALIDATION · SIH-ENNORE-2017"
          : "HISTORICAL OBSERVATION"}
        <span className="mono">{d.id === "SIH-ENNORE-2017" ? "" : d.id}</span>
      </div>
      <div className="evidence-title">
        <h2>{d.title}</h2>
        <span className={"status-tag " + d.status}>
          {statusLabel(d.status)}
        </span>
      </div>
      {authority ? (
        <div
          className="detail-tabs"
          role="tablist"
          aria-label="Investigation details"
        >
          {["Evidence", "Sources", "Timeline", "Transport", "Review"].map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              className={tab === t ? "active" : ""}
              onClick={() => {
                setTab(t);
                setError("");
                setSaved(false);
              }}
            >
              {t}
            </button>
          ))}
        </div>
      ) : (
        <div className="public-record-tag">
          <ShieldCheck size={14} /> Public archive · source attributed
        </div>
      )}
      <div className="panel-body">
        {(tab === "Evidence" || !authority) && (
          <>
            {d.trigger === "ais" ? (
              /* AIS-FIRST 10-STEP INVESTIGATION CHAIN */
              <div className="ais-first-chain">
                {/* 1. AIS Anomaly */}
                <div className="section-title">
                  <span>1. AIS ANOMALY TRIGGER</span>
                  <span className="count-tag amber">ALERT</span>
                </div>
                <div className="observation-stat">
                  <div>
                    <span className="eyebrow">TRIGGER: AIS BEHAVIOURAL ANOMALY</span>
                    <div>
                      <strong style={{ fontSize: "1.2rem", color: "#fbbf24" }}>⚠ Anomaly Detected</strong>
                    </div>
                  </div>
                  <div className="mini-slick" style={{ color: "#fbbf24" }}>
                    <Radio size={28} />
                  </div>
                </div>
                <p className="stat-note">
                  Surveillance engine flagged statistically anomalous deceleration and course loitering.
                </p>

                {/* 2. Vessel Behaviour */}
                <div className="section-title">
                  <span>2. VESSEL BEHAVIOUR PROFILE</span>
                </div>
                <div className="facts-grid">
                  <div>
                    <span>Investigated Vessel</span>
                    <strong>{d.ranking?.[0]?.name || "Training Vessel A"}</strong>
                  </div>
                  <div>
                    <span>Cruising Speed</span>
                    <strong>12.1 kn (Normal)</strong>
                  </div>
                  <div>
                    <span>Deceleration</span>
                    <strong style={{ color: "#fbbf24" }}>12.1 → 3.2 kn (Amber)</strong>
                  </div>
                  <div>
                    <span>Course Anomaly</span>
                    <strong style={{ color: "#f87171" }}>135° → 315° loop (Red)</strong>
                  </div>
                </div>

                {/* 3. Anomaly Location / Time */}
                <div className="section-title">
                  <span>3. ANOMALY LOCATION &amp; TIME</span>
                </div>
                <div className="facts-grid">
                  <div>
                    <span>Coordinates</span>
                    <strong className="mono">28.4770°N, 89.2800°W</strong>
                  </div>
                  <div>
                    <span>Time Window</span>
                    <strong className="mono">06:42–07:00 UTC</strong>
                  </div>
                  <div>
                    <span>Surveillance Zone</span>
                    <strong>Northern Gulf Monitored Sector</strong>
                  </div>
                  <div>
                    <span>Anomaly Threshold</span>
                    <strong>Crossed at 07:00 UTC</strong>
                  </div>
                </div>

                {/* 4. SAR Observation Availability */}
                <div className="section-title">
                  <span>4. TARGETED SATELLITE VERIFICATION</span>
                  <span className="mono">POST-ANOMALY</span>
                </div>
                <div className="evidence-chain">
                  <div className="chain-item">
                    <span className="chain-icon">
                      <Satellite size={16} />
                    </span>
                    <div>
                      <strong>Searching available SAR acquisitions</strong>
                      <p>Window: 06:42–12:00 UTC · 25 km investigation radius</p>
                    </div>
                    <Check size={14} />
                  </div>
                  <div className="chain-item">
                    <span className="chain-icon">
                      <FileText size={16} />
                    </span>
                    <div>
                      <strong>Observation Matched: NOAA/NESDIS Composite</strong>
                      <p>Sensor: Satellite Radar / Optical Composite (2010-05-17)</p>
                    </div>
                    <Check size={14} />
                  </div>
                </div>

                {/* 5. Surface Anomaly Evidence */}
                <div className="section-title">
                  <span>5. SUSPECTED SURFACE ANOMALY EVIDENCE</span>
                </div>
                <div className="facts-grid">
                  <div>
                    <span>Surface Feature</span>
                    <strong>Suspected Surface Anomaly</strong>
                  </div>
                  <div>
                    <span>Mapped Extent</span>
                    <strong>{area(d.area_km2)} km²</strong>
                  </div>
                  <div>
                    <span>SAR Reveal Stage</span>
                    <strong>08:15 UTC (Post-Verification)</strong>
                  </div>
                  <div>
                    <span>Source Classification</span>
                    <strong>Historical composite mask</strong>
                  </div>
                </div>

                {/* 6. Space-Time Correlation */}
                <div className="section-title">
                  <span>6. SPACE-TIME CORRELATION EVALUATED</span>
                </div>
                <div className="facts-grid">
                  <div>
                    <span>Spatial Evidence</span>
                    <strong style={{ color: "#34d399" }}>✓ Inside Anomaly Boundary</strong>
                  </div>
                  <div>
                    <span>Temporal Evidence</span>
                    <strong style={{ color: "#34d399" }}>✓ Compatible Window</strong>
                  </div>
                  <div>
                    <span>AIS Coverage</span>
                    <strong style={{ color: "#34d399" }}>✓ Monitored Corridor</strong>
                  </div>
                  <div>
                    <span>Correlation Status</span>
                    <strong style={{ color: "#34d399" }}>COMPATIBLE</strong>
                  </div>
                </div>

                {/* 7. Drift / Environmental Evidence */}
                <div className="section-title">
                  <span>7. DRIFT &amp; ENVIRONMENTAL EVIDENCE</span>
                </div>
                <div className="warning-note">
                  <strong>Metocean data status: NOT LOADED</strong>
                  <p>
                    ERA5 wind and CMEMS ocean current reanalysis are not loaded for this training scenario.
                    Numerical backtracking simulation is truthfully withheld to avoid false precision.
                  </p>
                </div>

                {/* 8. Candidate Assessment */}
                <div className="section-title">
                  <span>8. CANDIDATE SOURCE ASSESSMENT</span>
                </div>
                <div className="primary-candidate-card">
                  <div className="candidate-badge-row">
                    <span className="candidate-rank-badge">HIGH-PRIORITY CANDIDATE</span>
                    <span className="candidate-score-pill">
                      Evidence Score: {d.ranking?.[0]?.score || 76} / 100
                    </span>
                  </div>
                  <p className="score-explainer-note" style={{ fontSize: "11px", color: "#64748b", margin: "4px 0 8px", fontStyle: "italic" }}>
                    Decision-support score derived from available evidence; not a probability of culpability.
                  </p>
                  <h3>Training Vessel A</h3>
                  <p className="body-copy" style={{ margin: "6px 0 10px 0" }}>
                    Training Vessel A shows vessel behaviour and space-time evidence consistent with the investigated surface observation.
                  </p>
                  <div className="why-first-section">
                    <strong>WHY THIS VESSEL WAS FLAGGED:</strong>
                    <ul>
                      <li>
                        <strong>Unusual speed reduction:</strong> Deceleration from 12.1 kn → 6.4 kn → 3.2 kn at 06:42 UTC.
                      </li>
                      <li>
                        <strong>Abnormal course behaviour:</strong> Loitering loop and repeated heading fluctuations (06:48–06:58 UTC, 135° → 315°).
                      </li>
                      <li>
                        <strong>Investigation region match:</strong> Anomaly occurred inside monitored investigation sector (28.4770°N, 89.2800°W).
                      </li>
                      <li>
                        <strong>Temporal alignment:</strong> Timing is compatible with subsequent satellite observation window.
                      </li>
                      <li>
                        <strong>Spatial coincidence:</strong> Trajectory intersects spatial footprint of suspected surface anomaly.
                      </li>
                    </ul>
                  </div>
                  <div className="analyst-verification-notice">
                    <ShieldCheck size={14} /> Decision-support result. Requires analyst verification. Does not establish legal liability.
                  </div>
                </div>

                {/* 9. Uncertainty & Limitations */}
                <div className="section-title">
                  <span>9. UNCERTAINTY &amp; LIMITATIONS</span>
                </div>
                <div className="uncertainty-box">
                  <div className="uncertainty-item">
                    <span className="uncertainty-bullet">•</span>
                    <div>
                      <strong>Training Data Provenance:</strong> Vessel trajectory is SYNTHETIC AIS · TRAINING DATA. Not historical AIS or evidence of actual responsibility.
                    </div>
                  </div>
                  <div className="uncertainty-item">
                    <span className="uncertainty-bullet">•</span>
                    <div>
                      <strong>Observation Precision:</strong> Satellite surface anomaly is a day-level composite, not an instantaneous radar snapshot.
                    </div>
                  </div>
                  <div className="uncertainty-item">
                    <span className="uncertainty-bullet">•</span>
                    <div>
                      <strong>Decision Support:</strong> High attribution priority indicates evidentiary compatibility, not judicial determination of guilt.
                    </div>
                  </div>
                </div>

                {/* 10. Human Review */}
                <div className="section-title">
                  <span>10. HUMAN REVIEW &amp; REPORT</span>
                </div>
                <div className="info-note">
                  Analyst verification status: <strong>Under Active Review</strong>. Review notes and evidence exports can be generated below.
                </div>
              </div>
            ) : (
              /* SAR-FIRST 10-STEP INVESTIGATION CHAIN (ENNORE CANONICAL) */
              <>
                <div className="observation-stat">
                  <div>
                    <span className="eyebrow">MAPPED SURFACE ANOMALY</span>
                    <div>
                      <strong>{area(d.area_km2)}</strong>
                      <span>km²</span>
                    </div>
                  </div>
                  <div className="mini-slick">
                    <svg viewBox="0 0 80 55" aria-hidden="true">
                      <path d="M8 36 15 23 27 25 38 10 45 19 55 16 68 26 59 31 69 41 53 37 39 45 28 37 19 44Z" />
                      <path d="m18 22 7-9 5 6-4 7Z" />
                    </svg>
                  </div>
                </div>
                <p className="stat-note">
                  Polygon area on WGS84 · not an oil-volume estimate
                </p>
                <div className="facts-grid">
                  <div>
                    <span>Observation date</span>
                    <strong>{date(d.observed_at)}</strong>
                  </div>
                  <div>
                    <span>Source polygons</span>
                    <strong>{d.polygon_count || "—"}</strong>
                  </div>
                  <div>
                    <span>Trigger</span>
                    <strong>SAR first</strong>
                  </div>
                  <div>
                    <span>Time resolution</span>
                    <strong>{obs ? "Level-1 GRD / Single overpass" : "No SAR match"}</strong>
                  </div>
                </div>
                <div className="section-title">
                  <span>Evidence chain</span>
                  <span className="mono">SAR → ORIGIN → CANDIDATES</span>
                </div>
                <div className="evidence-chain">
                  <div className="chain-item">
                    <span className="chain-icon">
                      <Satellite size={16} />
                    </span>
                    <div>
                      <strong>Sentinel-1A SAR observation</strong>
                      <p>C-band radar backscatter detection (2017-01-29T00:31:32Z)</p>
                    </div>
                    <Check size={14} />
                  </div>
                  <div className="chain-item">
                    <span className="chain-icon">
                      <FileText size={16} />
                    </span>
                    <div>
                      <strong>Suspected surface slick geometry</strong>
                      <p>Illustrative slick mask matching verified coastal impact zone</p>
                    </div>
                    {obs ? <Check size={14} /> : <AlertCircle size={14} />}
                  </div>
                  <div className="chain-item">
                    <span className="chain-icon">
                      <Waves size={16} />
                    </span>
                    <div>
                      <strong>Collision origin &amp; candidate search</strong>
                      <p>Kamarajar Port entrance coordinates: 13.2530°N, 80.3350°E</p>
                    </div>
                    <Check size={14} />
                  </div>
                </div>
                <div className="section-title">
                  <span>Analyst context</span>
                </div>
                <p className="body-copy">{d.summary}</p>
                <div className="warning-note">
                  <strong>Data transparency notice.</strong> AIS tracks are{" "}
                  <em>Training AIS reconstructions</em> (provenance: TRAINING).
                  The slick polygon is an <em>Illustrative mask</em> derived
                  from published sources (provenance: ILLUSTRATIVE). No primary
                  SAR classification or live AIS data are used in this case.
                </div>
                {obs && (
                  <div className="source-card">
                    <div>
                      <Satellite size={17} />
                      <strong>Observation provenance</strong>
                    </div>
                    <p>{obs.source.provider}</p>
                    <p>{obs.source.sensor}</p>
                    <a href={obs.source.url} target="_blank" rel="noreferrer">
                      Open original dataset <ArrowUpRight size={14} />
                    </a>
                  </div>
                )}
                <div className="section-title">
                  <span>Uncertainty &amp; Limitations</span>
                </div>
                <div className="uncertainty-box">
                  <div className="uncertainty-item">
                    <span className="uncertainty-bullet">•</span>
                    <div>
                      <strong>Origin Region:</strong> Reported as a ±1.5 km maritime collision zone around documented coordinates (13.2530°N, 80.3350°E), avoiding false-precision points.
                    </div>
                  </div>
                  <div className="uncertainty-item">
                    <span className="uncertainty-bullet">•</span>
                    <div>
                      <strong>Release Window:</strong> Incident release window is bounded to 2017-01-28 07:45–08:30 UTC.
                    </div>
                  </div>
                  <div className="uncertainty-item">
                    <span className="uncertainty-bullet">•</span>
                    <div>
                      <strong>Metocean Status:</strong> Real ERA5 and CMEMS reanalysis not loaded; numerical backtracking is withheld to prevent misleading outputs.
                    </div>
                  </div>
                  <div className="uncertainty-item">
                    <span className="uncertainty-bullet">•</span>
                    <div>
                      <strong>AIS Coverage:</strong> Both vessels exhibit transmission gaps (&gt;45 min) during the critical collision period.
                    </div>
                  </div>
                </div>
                <div className="info-note">
                  Decision-support result — analyst verification required. Priority scores do not establish legal liability.
                </div>
              </>
            )}
            {onOpenReport && (
              <button
                className="primary full"
                style={{ marginTop: "12px", marginBottom: "8px" }}
                onClick={onOpenReport}
              >
                <FileText size={16} />
                Generate Investigation Report
              </button>
            )}
            {!authority && (
              <button className="outline full" onClick={onLogin}>
                <ShieldCheck size={16} /> Authority workspace{" "}
                <ArrowRight size={16} />
              </button>
            )}
          </>
        )}
        {authority && tab === "Sources" && (
          <>
            <div className="section-title">
              <span>{d.trigger === "ais" ? "Candidate source assessment" : "Candidate source ranking"}</span>
              <span className="count-tag">{d.ranking?.length || 0}</span>
            </div>
            <p className="body-copy">
              {d.trigger === "ais"
                ? "Targeted assessment of investigated vessel based on behavioural anomaly signals and space-time correlation with subsequent satellite observation."
                : "Priority combines proximity (60%), temporal overlap (25%), and behavior (15%). Missing AIS coverage reduces the score."}
            </p>
            {d.ranking?.length ? (
              <>
                <div className="warning-note">
                  {d.trigger === "ais"
                    ? "Decision-support result — analyst verification required. Attribution priority does not establish legal liability."
                    : d.id === "SIH-ENNORE-2017"
                    ? "Training AIS candidates · provenance: TRAINING. Heuristic priority score — not a probability of responsibility. Decision-support result — analyst verification required."
                    : "Training candidates · heuristic score, not a probability of responsibility."}
                </div>

                {d.ranking[0] && (
                  <div className="primary-candidate-card">
                    <div className="candidate-badge-row">
                      <span className="candidate-rank-badge">
                        {d.trigger === "ais" ? "HIGH-PRIORITY CANDIDATE" : "RANK #1 CANDIDATE"}
                      </span>
                      <span className="candidate-score-pill">
                        Score {d.ranking[0].score}/100
                      </span>
                    </div>
                    <h3>
                      {d.ranking[0].name
                        .replace(" — Training AIS Reconstruction", "")
                        .replace("Training vessel ", "")}
                    </h3>
                    <div className="candidate-meta-grid">
                      <div>
                        <span>Role</span>
                        <strong>{d.trigger === "ais" ? "Investigated Anomaly Vessel" : "Primary Collision Party"}</strong>
                      </div>
                      <div>
                        <span>Origin Distance</span>
                        <strong>{d.ranking[0].distance_km.toFixed(1)} km</strong>
                      </div>
                      <div>
                        <span>Provenance</span>
                        <strong>{d.trigger === "ais" ? "SYNTHETIC AIS" : d.id === "SIH-ENNORE-2017" ? "TRAINING AIS" : "DEMO AIS"}</strong>
                      </div>
                    </div>
                    <div className="why-first-section">
                      <strong>
                        {d.trigger === "ais" ? "WHY THIS VESSEL WAS FLAGGED" : "WHY IS THIS VESSEL RANKED FIRST?"}
                      </strong>
                      <ul>
                        {d.trigger === "ais" ? (
                          <>
                            <li>
                              <strong>Unusual speed reduction:</strong> Speed fell from 12.1 kn → 6.4 kn → 3.2 kn at 06:42 UTC.
                            </li>
                            <li>
                              <strong>Abnormal course behaviour:</strong> Abnormal heading changes and loitering-like movement (06:48–06:58 UTC, 135° → 315°).
                            </li>
                            <li>
                              <strong>Investigation sector:</strong> Anomaly occurred inside monitored surveillance corridor (28.4770°N, 89.2800°W).
                            </li>
                            <li>
                              <strong>Timing compatibility:</strong> Anomaly window is compatible with subsequent satellite observation.
                            </li>
                            <li>
                              <strong>Trajectory intersection:</strong> Track intersects spatial footprint of detected surface slick.
                            </li>
                          </>
                        ) : (
                          <>
                            <li>
                              <strong>Spatial Proximity (0.0 km):</strong> Track passes directly through the collision origin coordinates (13.2530°N, 80.3350°E).
                            </li>
                            <li>
                              <strong>Temporal Window:</strong> Vessel was present during the collision release window (08:00 UTC, 28 Jan 2017).
                            </li>
                            <li>
                              <strong>AIS Transmission Gap:</strong> 150-minute reporting gap (08:30–11:00 UTC) coincides with the post-collision period.
                            </li>
                            <li>
                              <strong>Documented Vessel Breach:</strong> Official inquiry confirmed ruptured bunker fuel tank releasing ~196 tonnes oil.
                            </li>
                          </>
                        )}
                      </ul>
                    </div>
                    <div className="analyst-verification-notice">
                      <ShieldCheck size={14} /> Decision-support result — analyst verification required.
                    </div>
                  </div>
                )}
                {d.ranking.map((r, i) => (
                  <button
                    className={
                      "source-rank " +
                      (selectedTrack === r.id ? "selected" : "")
                    }
                    key={r.id}
                    onClick={() => onSelectTrack(r.id)}
                  >
                    <div className="rank-top">
                      <span className="rank-number">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <strong>{r.name.replace("Training vessel ", "").replace(" — Training AIS Reconstruction", "")}</strong>
                      <span className="score">
                        {r.score}
                        <small>/100</small>
                      </span>
                    </div>
                    {(d.id === "SIH-ENNORE-2017" || d.exercise) && (
                      <div className="training-ais-badge">
                        {d.id === "SIH-ENNORE-2017" ? "Training AIS reconstruction" : "Synthetic AIS"}
                      </div>
                    )}
                    <div className="score-track">
                      <i style={{ width: r.score + "%" }} />
                    </div>
                    <div className="rank-metrics">
                      <span>{r.distance_km.toFixed(1)} km to slick</span>
                      <span>{Math.round(r.coverage * 100)}% coverage</span>
                    </div>
                    {selectedTrack === r.id && (
                      <div className="rank-breakdown">
                        <span>
                          Proximity{" "}
                          <b>{Math.round(r.components.proximity * 100)}</b>
                        </span>
                        <span>
                          Time overlap{" "}
                          <b>{Math.round(r.components.temporal * 100)}</b>
                        </span>
                        <span>
                          Behavior{" "}
                          <b>{Math.round(r.components.behavior * 100)}</b>
                        </span>
                      </div>
                    )}
                  </button>
                ))}
              </>
            ) : (
              <div className="empty-state">
                <Radio size={28} />
                <h3>No matching recorded AIS</h3>
                <p>
                  No candidate attribution can be made from this cached pack.
                  Start a training exercise to inspect the ranking workflow.
                </p>
              </div>
            )}
            {d.findings?.historical_source && (
              <div className="source-card">
                <strong>Documented historical source</strong>
                <h3>{d.findings.historical_source.name}</h3>
                <p>{d.findings.historical_source.status}</p>
                <a
                  href={d.findings.historical_source.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  NOAA incident record <ArrowUpRight size={14} />
                </a>
              </div>
            )}
            <div className="section-title">
              <span>Trajectory events</span>
            </div>
            {d.anomalies?.slice(0, 8).map((e, i) => (
              <div className="event-row" key={i}>
                <span className="event-dot" />
                <div>
                  <strong>{e.label}</strong>
                  <p>
                    {utc(e.time)} · {e.track_id}
                  </p>
                  <small>{e.meaning}</small>
                </div>
              </div>
            ))}
          </>
        )}
        {authority && tab === "Timeline" && (
          <>
            <div className="section-title">
              <span>Chronological investigation events</span>
              <span className="count-tag">
                {d.timeline?.length || d.anomalies?.length || 0}
              </span>
            </div>
            <p className="body-copy">
              Timestamped sequence connecting vessel arrival, collision incident, AIS gaps, satellite overpass, and candidate attribution.
            </p>
            <div className="timeline-event-list">
              {(d.timeline || []).map((evt) => (
                <div className="timeline-card-item" key={evt.event_id}>
                  <div className="timeline-card-top">
                    <span className="mono timeline-timestamp">
                      <Clock size={12} /> {utc(evt.timestamp)}
                    </span>
                    <span
                      className={`provenance-chip ${evt.provenance_class?.toLowerCase() || "derived"}`}
                    >
                      {evt.provenance_class || "DERIVED"}
                    </span>
                  </div>
                  <h4>{evt.title}</h4>
                  <p>{evt.description}</p>
                  {evt.ui_warning && (
                    <small className="timeline-warning">{evt.ui_warning}</small>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
        {authority && tab === "Transport" && (
          <>
            <div className="transport-heading">
              <Waves size={25} />
              <h3>Trace the possible origin</h3>
            </div>
            <div className="warning-note">
              <strong>Historical reconstruction unavailable</strong>
              <p>
                {d.findings?.reason ||
                  "Verified, time-matched ocean currents and wind fields are not included in this cached pack."}
              </p>
            </div>
            <div className="section-title">
              <span>Environmental data status</span>
            </div>
            <div className="required-row">
              <Satellite size={16} />
              <span>SAR image</span>
              <b>{d.findings?.metocean_status?.sar_status
                || (d.findings?.sar_search?.matched ? "OBSERVED" : "NOT AVAILABLE")}</b>
            </div>
            <div className="required-row">
              <Wind size={16} />
              <span>Wind field</span>
              <b>{d.findings?.metocean_status?.wind?.includes("NOT_LOADED")
                ? "NOT LOADED"
                : d.findings?.metocean_status?.wind?.includes("LOADED")
                  ? "ERA5 REANALYSIS"
                  : "NOT LOADED"}</b>
            </div>
            <div className="required-row">
              <Waves size={16} />
              <span>Ocean current</span>
              <b>{d.findings?.metocean_status?.currents?.includes("NOT_LOADED")
                ? "NOT LOADED"
                : d.findings?.metocean_status?.currents?.includes("LOADED")
                  ? "CMEMS REANALYSIS"
                  : "NOT LOADED"}</b>
            </div>
            <div className="required-row">
              <Radio size={16} />
              <span>AIS tracks</span>
              <b>{d.findings?.ais_status?.includes("TRAINING")
                ? "TRAINING / SYNTHETIC"
                : d.findings?.ais_status?.includes("OBSERVED")
                  ? "OBSERVED"
                  : "TRAINING / SYNTHETIC"}</b>
            </div>
            <div className="required-row">
              <Satellite size={16} />
              <span>Oil slick geometry</span>
              <b>{obs?.source?.certainty?.includes("ILLUSTRATIVE")
                || d.findings?.slick_provenance === "ILLUSTRATIVE"
                ? "ILLUSTRATIVE"
                : obs ? "OBSERVED" : "ILLUSTRATIVE"}</b>
            </div>
            {d.exercise && (
              <>
                <div className="section-title">
                  <span>Transport sandbox</span>
                  <span className="badge">ILLUSTRATIVE</span>
                </div>
                <p className="body-copy">
                  Explore a seeded particle ensemble under explicit constant
                  current and wind assumptions. This is a physics demonstration,
                  not a reconstruction of this incident.
                </p>
                <div className="equation">
                  v = u<sub>current</sub> + 0.03 u<sub>wind</sub> + diffusion
                </div>
                <button
                  className="primary full"
                  disabled={busy || !obs}
                  onClick={async () => {
                    setBusy(true);
                    setError("");
                    try {
                      const r = await api<Reconstruction>(
                        `/cases/${d.id}/reconstruction`,
                        {
                          method: "POST",
                          body: JSON.stringify({
                            mode: "illustrative",
                            hours: 6,
                          }),
                        },
                      );
                      onReconstruction(r);
                      setDriftFrame(6);
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  {busy ? (
                    <LoaderCircle size={16} className="spin" />
                  ) : (
                    <Waves size={16} />
                  )}
                  Run illustrative backtrack
                </button>
                {reconstruction && (
                  <>
                    <label className="drift-slider">
                      {driftFrame} hours before observation
                      <input
                        aria-label="Hours before observation"
                        type="range"
                        min="0"
                        max={reconstruction.frames.length - 1}
                        value={driftFrame}
                        onChange={(e) => setDriftFrame(Number(e.target.value))}
                      />
                    </label>
                    <div className="facts-grid">
                      <div>
                        <span>Windage</span>
                        <strong>3%</strong>
                      </div>
                      <div>
                        <span>Diffusivity</span>
                        <strong>8 m²/s</strong>
                      </div>
                      <div>
                        <span>Current (east, north)</span>
                        <strong>0.12, −0.06 m/s</strong>
                      </div>
                      <div>
                        <span>Wind (east, north)</span>
                        <strong>4, 2 m/s</strong>
                      </div>
                    </div>
                    <p className="stat-note">
                      Envelope = ensemble spread; no calibrated confidence
                      level.
                    </p>
                    <button
                      className="text-button"
                      onClick={() => onReconstruction(null)}
                    >
                      Clear transport layer
                    </button>
                  </>
                )}
              </>
            )}
            <p className="body-copy small">
              Backward advection does not reverse weathering. This prototype
              does not infer oil age or reverse oil chemistry.
            </p>
          </>
        )}
        {authority && tab === "Review" && (
          <>
            <div className="section-title">
              <span>Record an assessment</span>
              <span className="mono">v{d.version}</span>
            </div>
            <p className="body-copy">
              Keep the decision and its supporting evidence together. Reviews
              are stored with your identity and timestamp.
            </p>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                setBusy(true);
                setError("");
                setSaved(false);
                try {
                  await api(`/cases/${d.id}/reviews`, {
                    method: "POST",
                    body: JSON.stringify({
                      note,
                      status,
                      expected_version: d.version,
                    }),
                  });
                  setNote("");
                  setSaved(true);
                  onRefresh();
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              <label>
                Assessment status
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  <option value="under_review">Under review</option>
                  <option value="needs_evidence">Needs evidence</option>
                  <option value="closed">Closed</option>
                </select>
              </label>
              <label>
                Review note
                <textarea
                  placeholder="Describe what the evidence supports and what remains uncertain…"
                  rows={5}
                  minLength={10}
                  maxLength={4000}
                  required
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                />
              </label>
              <button className="primary full" disabled={busy}>
                <Check size={16} />
                Save assessment
              </button>
            </form>
            {saved && (
              <p className="success-note" role="status">
                Assessment saved to the audit trail.
              </p>
            )}
            <div className="section-title">
              <span>Review history</span>
              <span className="count-tag">{d.reviews?.length || 0}</span>
            </div>
            {d.reviews?.length ? (
              d.reviews.map((r) => (
                <div className="review-entry" key={r.id}>
                  <strong>{r.author}</strong>
                  <span>{statusLabel(r.status)}</span>
                  <p>{r.note}</p>
                  <small>
                    {date(r.created_at)} · {utc(r.created_at)}
                  </small>
                </div>
              ))
            ) : (
              <p className="body-copy">No assessments recorded yet.</p>
            )}
          </>
        )}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
      </div>
      {authority && (
        <div className="panel-footer">
          {onOpenReport && (
            <button
              className="primary full"
              onClick={onOpenReport}
              style={{ marginBottom: "8px" }}
            >
              <FileText size={15} />
              Generate Investigation Report
            </button>
          )}
          <a
            className="outline full"
            href={`/api/cases/${d.id}/export`}
            download
          >
            <Download size={15} />
            Export evidence <span>JSON</span>
          </a>
        </div>
      )}
    </aside>
  );
}
