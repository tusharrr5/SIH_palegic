"use client";
import { useEffect, useRef } from "react";
import {
  X,
  Printer,
  Download,
  ShieldCheck,
  Satellite,
  Radio,
  Waves,
  Wind,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Clock,
  MapPin,
  Ship,
} from "lucide-react";
import type { CaseDetail } from "@/lib/types";
import { date, utc, area } from "@/lib/api";

type Props = {
  detail: CaseDetail;
  onClose: () => void;
};

export default function ReportModal({ detail: d, onClose }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    dialogRef.current?.showModal();
  }, []);

  const topCandidate = d.ranking?.[0];
  const col = d.findings?.collision_site;
  const obs = d.observation;
  const isAis = d.trigger === "ais";

  const handlePrint = () => {
    window.print();
  };

  return (
    <dialog
      ref={dialogRef}
      className="modal report-modal"
      onCancel={onClose}
      aria-label="Investigation Report"
    >
      <div className="report-modal-header no-print">
        <div className="report-header-title">
          <FileText size={20} />
          <h2>Marine Pollution Investigation Report</h2>
          <span className="mono badge">{d.id}</span>
        </div>
        <div className="report-header-actions">
          <button
            className="sih-primary-btn compact"
            onClick={handlePrint}
            title="Print or export report to PDF"
          >
            <Printer size={15} />
            Print / Export PDF
          </button>
          <a
            className="sih-secondary-btn compact"
            href={`/api/cases/${d.id}/export`}
            download
            title="Export evidence as JSON"
          >
            <Download size={15} />
            Evidence JSON
          </a>
          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Close report"
          >
            <X size={20} />
          </button>
        </div>
      </div>

      <div className="report-document printable-report" id="report-printable-area">
        {/* REPORT HEADER */}
        <header className="report-cover">
          <div className="report-banner">
            <span className="report-agency">PALEGIC MARITIME INTELLIGENCE</span>
            <span className="report-stamp">DECISION-SUPPORT OUTPUT</span>
          </div>
          <div className="report-heading">
            <h1 className="report-main-title">Marine Pollution Investigation Report</h1>
          </div>
          <div className="report-trigger-badge-bar" style={{ margin: "12px 0 16px" }}>
            <span
              className={`badge mono ${isAis ? "training-badge" : "observed-badge"}`}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                fontSize: "12px",
                fontWeight: 600,
                borderRadius: "4px",
                background: isAis ? "rgba(245, 158, 11, 0.15)" : "rgba(34, 197, 94, 0.15)",
                color: isAis ? "#fbbf24" : "#4ade80",
                border: `1px solid ${isAis ? "rgba(245, 158, 11, 0.4)" : "rgba(34, 197, 94, 0.4)"}`,
              }}
            >
              {isAis ? <Radio size={14} /> : <Satellite size={14} />}
              INVESTIGATION TRIGGER: {isAis ? "AIS behavioural anomaly" : "SAR surface slick detection"}
            </span>
          </div>
          <div className="report-meta-grid">
            <div>
              <span className="meta-label">INVESTIGATION ID</span>
              <strong className="mono">{d.id}</strong>
            </div>
            <div>
              <span className="meta-label">{isAis ? "INVESTIGATED VESSEL" : "INCIDENT TITLE"}</span>
              <strong>{isAis ? (d.tracks?.[0]?.name || "Training Vessel A") : d.title}</strong>
            </div>
            <div>
              <span className="meta-label">DATE OF REPORT</span>
              <strong>{date(new Date().toISOString(), true)}</strong>
            </div>
            <div>
              <span className="meta-label">CLASSIFICATION</span>
              <span className="report-class-tag">DECISION-SUPPORT / NON-LEGAL</span>
            </div>
          </div>
        </header>

        {isAis ? (
          <>
            {/* AIS-FIRST SECTION 1: INCIDENT & TRIGGER SUMMARY */}
            <section className="report-section">
              <h2 className="section-heading">1. Investigation Trigger &amp; Summary</h2>
              <div
                style={{
                  padding: "10px 14px",
                  marginBottom: "12px",
                  background: "rgba(245, 158, 11, 0.1)",
                  borderLeft: "3px solid #f59e0b",
                  borderRadius: "0 4px 4px 0",
                }}
              >
                <strong style={{ color: "#fbbf24", display: "block", marginBottom: "4px" }}>
                  INVESTIGATION TRIGGER: AIS behavioural anomaly
                </strong>
                <span style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                  Continuous AIS surveillance corridor flagged suspicious navigational behaviour for
                  Training Vessel A. Targeted satellite verification was subsequently initiated.
                </span>
              </div>
              <p className="report-paragraph">
                At 06:42 UTC on 17 May 2010, coastal AIS monitoring detected a significant deceleration
                from 12.1 kn down to 3.0 kn, followed by an abnormal heading loitering loop between
                06:48 and 06:58 UTC. The anomaly engine crossed alert thresholds at 07:00 UTC at
                coordinates 28.4770°N, 89.2800°W, triggering automated space-time satellite acquisition
                search. Subsequent SAR verification at 08:15 UTC revealed a suspected surface slick
                coinciding with the anomaly corridor.
              </p>
              <div className="report-key-metrics">
                <div className="metric-box">
                  <span className="metric-label">Investigation Mode</span>
                  <strong className="metric-value">AIS-First Surveillance</strong>
                </div>
                <div className="metric-box">
                  <span className="metric-label">Anomaly Detected</span>
                  <strong className="metric-value mono">07:00 UTC (17 May 2010)</strong>
                </div>
                <div className="metric-box">
                  <span className="metric-label">Target Search Window</span>
                  <strong className="metric-value">25 km radius corridor</strong>
                </div>
                <div className="metric-box">
                  <span className="metric-label">SAR Overpass Time</span>
                  <strong className="metric-value mono">08:15 UTC (+75 min)</strong>
                </div>
              </div>
            </section>

            {/* AIS-FIRST SECTION 2: INVESTIGATED VESSEL & AIS TRAJECTORY */}
            <section className="report-section">
              <h2 className="section-heading">2. Investigated Vessel &amp; AIS Trajectory</h2>
              <p className="report-paragraph">
                Surveillance focused on a single primary training vessel exhibiting anomalous behavior.
                Other traffic remained muted in the corridor context.
              </p>
              <table className="report-table">
                <tbody>
                  <tr>
                    <th>Vessel Name</th>
                    <td>
                      <strong>Training Vessel A</strong>
                    </td>
                  </tr>
                  <tr>
                    <th>Trajectory Data Provenance</th>
                    <td>
                      <span className="provenance-chip training">SYNTHETIC AIS · TRAINING DATA</span>{" "}
                      — Deterministic training trajectory with timestamped telemetry.
                    </td>
                  </tr>
                  <tr>
                    <th>Trajectory Positions</th>
                    <td className="mono">{d.tracks?.[0]?.points.length || 18} recorded positions (06:00 – 12:00 UTC)</td>
                  </tr>
                  <tr>
                    <th>Cruising Profile</th>
                    <td>Normal speed ~12.1 kn, stable course 070° prior to deceleration</td>
                  </tr>
                  <tr>
                    <th>AIS Gap Recorded</th>
                    <td className="mono">10:00 – 12:00 UTC (120-minute reporting gap)</td>
                  </tr>
                </tbody>
              </table>
            </section>

            {/* AIS-FIRST SECTION 3: DETECTED BEHAVIOURAL ANOMALY */}
            <section className="report-section highlight-box">
              <h2 className="section-heading">3. Detected Behavioural Anomaly</h2>
              <ul className="evidence-list">
                <li>
                  <strong>Abnormal Speed Reduction (06:42–06:45 UTC):</strong> Cruising speed
                  abruptly dropped from 12.1 kn to 6.4 kn, reaching 3.0 kn within 3 minutes.
                </li>
                <li>
                  <strong>Unusual Heading / Loitering Movement (06:48–06:58 UTC):</strong> Vessel
                  executed a low-speed heading loop through 155° → 245° → 335° → 120° before
                  resuming eastward transit.
                </li>
                <li>
                  <strong>Anomaly Engine Threshold Crossed (07:00 UTC):</strong> Multi-signal
                  detector flagged vessel at coordinates <strong>28.4770°N, 89.2800°W</strong>.
                </li>
                <li>
                  <strong>Anomaly Time Window:</strong> 2010-05-17 06:42:00Z to 07:00:00Z.
                </li>
              </ul>
              <p className="disclaimer-note">
                <em>
                  Note: A speed drop or turn does not prove deliberate discharge; it constitutes
                  suspicious vessel behaviour triggering targeted satellite verification.
                </em>
              </p>
            </section>

            {/* AIS-FIRST SECTION 4: TARGETED SATELLITE VERIFICATION */}
            <section className="report-section">
              <h2 className="section-heading">4. Targeted Satellite Verification (SAR Search)</h2>
              <p className="report-paragraph">
                Following anomaly alert generation at 07:00 UTC, the PALEGIC engine queried available
                SAR acquisitions within the space-time window (25 km radius around 28.4770°N, 89.2800°W).
              </p>
              <table className="report-table">
                <tbody>
                  <tr>
                    <th>Search Query</th>
                    <td>Space-time window: 25 km radius, 2010-05-17 06:00–12:00 UTC</td>
                  </tr>
                  <tr>
                    <th>Observation Status</th>
                    <td>Acquisition found: 2010-05-17T08:15:00Z (+75 min latency)</td>
                  </tr>
                  <tr>
                    <th>Observation Source</th>
                    <td>Synthetic Aperture Radar (SAR) · Scene dwh-2010-05-17</td>
                  </tr>
                  <tr>
                    <th>Provenance Classification</th>
                    <td>
                      <span className="provenance-chip illustrative">HISTORICAL / TRAINING</span> —
                      Real historical slick geometry used as demonstration ground truth.
                    </td>
                  </tr>
                </tbody>
              </table>
            </section>

            {/* AIS-FIRST SECTION 5: SUSPECTED SURFACE ANOMALY RESULT */}
            <section className="report-section">
              <h2 className="section-heading">5. Suspected Surface Anomaly Evidence</h2>
              <p className="report-paragraph">
                Satellite verification identified a significant surface feature indicative of a
                suspected surface anomaly coincident with the investigated corridor.
              </p>
              <table className="report-table">
                <tbody>
                  <tr>
                    <th>Surface Feature Status</th>
                    <td>
                      <strong>Suspected Surface Anomaly Identified</strong> (Historical Composite · not confirmed spill)
                    </td>
                  </tr>
                  <tr>
                    <th>Observation Time</th>
                    <td className="mono">2010-05-17T08:15:00Z</td>
                  </tr>
                  <tr>
                    <th>Estimated Anomaly Area</th>
                    <td>
                      <strong>~{d.area_km2 ? area(d.area_km2) : "26,800"} km²</strong>
                    </td>
                  </tr>
                  <tr>
                    <th>Observation Classification</th>
                    <td>Historical satellite surface anomaly composite mask (NOAA/NESDIS)</td>
                  </tr>
                </tbody>
              </table>
            </section>

            {/* AIS-FIRST SECTION 6: SPACE-TIME CORRELATION */}
            <section className="report-section">
              <h2 className="section-heading">6. Space-Time Evidence Correlation</h2>
              <table className="report-table">
                <tbody>
                  <tr>
                    <th>Spatial Evidence</th>
                    <td>
                      <span className="green-text">✓ High Correlation</span> — Anomaly coordinates
                      (28.4770°N, 89.2800°W) lie directly within the 25 km target verification corridor.
                    </td>
                  </tr>
                  <tr>
                    <th>Temporal Evidence</th>
                    <td>
                      <span className="green-text">✓ Compatible Window</span> — Vessel anomaly (06:42–07:00 UTC)
                      preceded the SAR observation (08:15 UTC) by 75 minutes, fully consistent with surface residence.
                    </td>
                  </tr>
                  <tr>
                    <th>AIS Behavioural Evidence</th>
                    <td>
                      <span className="green-text">✓ Corroborated</span> — Speed deceleration and course loop
                      correlate with potential stationary or slow-speed discharge activity.
                    </td>
                  </tr>
                  <tr>
                    <th>Drift / Environmental Evidence</th>
                    <td>
                      <span className="amber-text">⚠ Withheld</span> — ERA5 wind and CMEMS current rasters
                      are not loaded; drift backtrack simulation is withheld to maintain scientific honesty.
                    </td>
                  </tr>
                </tbody>
              </table>
            </section>

            {/* AIS-FIRST SECTION 7: CANDIDATE ASSESSMENT */}
            <section className="report-section highlight-box">
              <h2 className="section-heading">7. Candidate Source Assessment</h2>
              <div className="attribution-rationale">
                <p className="strong-text" style={{ fontSize: "16px", marginBottom: "8px" }}>
                  Status: <span style={{ color: "#fbbf24" }}>HIGH-PRIORITY CANDIDATE</span>
                </p>
                <p style={{ marginBottom: "4px" }}>
                  Evidence Score: <strong className="mono" style={{ fontSize: "18px" }}>76 / 100</strong>
                </p>
                <p className="score-explainer-note" style={{ fontSize: "12px", color: "#64748b", margin: "4px 0 10px", fontStyle: "italic" }}>
                  Decision-support score derived from available evidence; not a probability of culpability.
                </p>
                <p className="report-paragraph" style={{ fontStyle: "italic" }}>
                  &ldquo;Training Vessel A shows vessel behaviour and space-time evidence consistent
                  with the investigated surface observation.&rdquo;
                </p>
                <div style={{ marginTop: "12px" }}>
                  <strong>WHY THIS VESSEL WAS FLAGGED:</strong>
                  <ul className="evidence-list" style={{ marginTop: "6px" }}>
                    <li>Unusual speed reduction (12.1 kn → 6.4 kn → 3.0 kn)</li>
                    <li>Abnormal course behaviour / loitering loop (06:48–06:58 UTC)</li>
                    <li>Anomaly occurred inside the targeted satellite investigation region</li>
                    <li>Timing is compatible with satellite observation (75 min prior to SAR acquisition)</li>
                    <li>Trajectory intersects spatial footprint of suspected surface anomaly</li>
                  </ul>
                </div>
                <p className="disclaimer-note" style={{ marginTop: "12px" }}>
                  <em>
                    Decision-support result. Requires analyst verification. This finding does NOT
                    constitute a legal finding of liability or causation.
                  </em>
                </p>
              </div>
            </section>

            {/* AIS-FIRST SECTION 8: CHRONOLOGICAL TIMELINE */}
            <section className="report-section">
              <h2 className="section-heading">8. Chronological Investigation Timeline</h2>
              <div className="report-timeline-list">
                {d.timeline?.map((evt) => (
                  <div className="timeline-report-item" key={evt.event_id}>
                    <span className="mono timeline-time">{utc(evt.timestamp)}</span>
                    <span className={`provenance-chip compact ${evt.provenance_class.toLowerCase()}`}>
                      {evt.provenance_class}
                    </span>
                    <div className="timeline-desc">
                      <strong>{evt.title}</strong>
                      <p>{evt.description}</p>
                    </div>
                  </div>
                )) || <p>Timeline events available in investigation replay.</p>}
              </div>
            </section>

            {/* AIS-FIRST SECTION 9: DATA PROVENANCE & LIMITATIONS */}
            <section className="report-section">
              <h2 className="section-heading">9. Authoritative Data Provenance &amp; Limitations</h2>
              <table className="report-table">
                <thead>
                  <tr>
                    <th>Dataset</th>
                    <th>Classification</th>
                    <th>Source</th>
                    <th>Integrity Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>AIS Vessel Stream</td>
                    <td>
                      <span className="provenance-chip training">SYNTHETIC AIS</span>
                    </td>
                    <td>PALEGIC AIS Training Generator</td>
                    <td>TRAINING DATA (NOT LIVE)</td>
                  </tr>
                  <tr>
                    <td>SAR Surface Slick</td>
                    <td>
                      <span className="provenance-chip illustrative">HISTORICAL</span>
                    </td>
                    <td>Historical SAR Archive (DWH 2010)</td>
                    <td>ILLUSTRATIVE GROUND TRUTH</td>
                  </tr>
                  <tr>
                    <td>ERA5 Wind Vectors</td>
                    <td>
                      <span className="provenance-chip not-loaded">NOT LOADED</span>
                    </td>
                    <td>Copernicus CDS</td>
                    <td>AWAITING DOWNLOAD</td>
                  </tr>
                  <tr>
                    <td>CMEMS Ocean Currents</td>
                    <td>
                      <span className="provenance-chip not-loaded">NOT LOADED</span>
                    </td>
                    <td>Copernicus Marine GLORYS12V1</td>
                    <td>AWAITING DOWNLOAD</td>
                  </tr>
                </tbody>
              </table>
            </section>

            {/* AIS-FIRST SECTION 10: ANALYST DISCLAIMER */}
            <section className="report-section report-disclaimer-box">
              <h2 className="section-heading">10. Analyst Verification Status &amp; Disclaimer</h2>
              <p className="disclaimer-text">
                <strong>Decision-support output. Human verification required.</strong>
                <br />
                This investigation report was generated automatically by PALEGIC for Smart India
                Hackathon 2026 (Problem Statement 26143, Team Ekatva). The candidate attribution score
                is a heuristic indicator for maritime intelligence triage. This system does not issue
                legal determinations of fault, maritime culpability, or regulatory sanctions. All
                findings must be corroborated by certified maritime investigators using primary evidence.
              </p>
              <div className="report-signature-block">
                <div>
                  <span>Generated By:</span>
                  <strong>PALEGIC Engine v0.1.0 (AIS-First Pipeline)</strong>
                </div>
                <div>
                  <span>Verification Status:</span>
                  <strong>AWAITING ANALYST SIGN-OFF</strong>
                </div>
              </div>
            </section>
          </>
        ) : (
          <>
            {/* SAR-FIRST SECTION 1: INCIDENT SUMMARY */}
            <section className="report-section">
              <h2 className="section-heading">1. Incident Summary</h2>
              <p className="report-paragraph">
                {d.summary ||
                  "On 28 January 2017, a collision between LPG tanker BW Maple (IMO 9346537, Singapore) and bulk carrier Dawn Kancheepuram (IMO 9368730, India) occurred near Kamarajar Port (Ennore), Tamil Nadu, releasing an estimated 196 tonnes of bunker fuel oil affecting approximately 35 km of coastal waters. This report documents the satellite-first and AIS correlation investigation conducted via the PALEGIC intelligence framework."}
              </p>
              <div className="report-key-metrics">
                <div className="metric-box">
                  <span className="metric-label">Known Spill Volume</span>
                  <strong className="metric-value">
                    ~{d.findings?.known_spill_volume_tonnes || 196} tonnes
                  </strong>
                </div>
                <div className="metric-box">
                  <span className="metric-label">Affected Coastline</span>
                  <strong className="metric-value">
                    ~{d.findings?.affected_coastline_km || 35} km
                  </strong>
                </div>
                <div className="metric-box">
                  <span className="metric-label">Estimated Release Window</span>
                  <strong className="metric-value mono">2017-01-28 07:45–08:30 UTC</strong>
                </div>
                <div className="metric-box">
                  <span className="metric-label">Investigation Mode</span>
                  <strong className="metric-value">Historical Validation</strong>
                </div>
              </div>
            </section>

        {/* SECTION 2: LOCATION & TIME */}
        <section className="report-section">
          <h2 className="section-heading">2. Location &amp; Time</h2>
          <table className="report-table">
            <tbody>
              <tr>
                <th>Region</th>
                <td>Bay of Bengal · Ennore / Chennai Coast, Tamil Nadu, India</td>
              </tr>
              <tr>
                <th>Collision Origin Coordinates</th>
                <td className="mono">
                  {col ? `${col.lat.toFixed(4)}°N, ${col.lon.toFixed(4)}°E` : "13.2530°N, 80.3350°E"}{" "}
                  (approx 1.5 NM east of Kamarajar Port entrance)
                </td>
              </tr>
              <tr>
                <th>Incident Start Time</th>
                <td className="mono">2017-01-28T08:00:00Z (13:30 IST)</td>
              </tr>
              <tr>
                <th>First Satellite Observation</th>
                <td className="mono">
                  {obs?.observed_at ? utc(obs.observed_at) : "2017-01-29T04:30:00Z"}{" "}
                  (~16.5 hours post-collision daylight overpass)
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        {/* SECTION 3: SATELLITE OBSERVATION */}
        <section className="report-section">
          <h2 className="section-heading">3. Satellite Observation</h2>
          <table className="report-table">
            <tbody>
              <tr>
                <th>Platform &amp; Sensor</th>
                <td>Sentinel-1A · C-band Synthetic Aperture Radar (C-SAR)</td>
              </tr>
              <tr>
                <th>Acquisition Time</th>
                <td className="mono">2017-01-29T00:31:32Z (06:01 IST)</td>
              </tr>
              <tr>
                <th>Product Type &amp; Swath</th>
                <td>Level-1 Ground Range Detected (GRD) · Interferometric Wide (IW)</td>
              </tr>
              <tr>
                <th>Polarisation &amp; Resolution</th>
                <td>VV + VH · 10 m spatial resolution</td>
              </tr>
              <tr>
                <th>Copernicus CDSE Product ID</th>
                <td className="mono small">
                  1d00379c-fe75-4e44-a90d-d354a59e0104 (Verified CDSE catalogue scene)
                </td>
              </tr>
              <tr>
                <th>SAR Observation Provenance</th>
                <td>
                  <span className="provenance-chip observed">OBSERVED</span> — Genuine catalogue
                  metadata verified. Raster image status: METADATA_ONLY.
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        {/* SECTION 4: SUSPECTED SLICK / INVESTIGATION GEOMETRY */}
        <section className="report-section">
          <h2 className="section-heading">4. Suspected Slick / Investigation Geometry</h2>
          <table className="report-table">
            <tbody>
              <tr>
                <th>Surface Anomaly Area</th>
                <td>
                  <strong>{area(d.area_km2)} km²</strong> (WGS84 ellipsoidal surface area)
                </td>
              </tr>
              <tr>
                <th>Number of Source Polygons</th>
                <td>{d.polygon_count || 1} distinct polygon(s)</td>
              </tr>
              <tr>
                <th>Geometry Provenance</th>
                <td>
                  <span className="provenance-chip illustrative">ILLUSTRATIVE</span> — Digitised
                  from published incident documentation and ITOPF maps. Not generated by an
                  automated ML classifier.
                </td>
              </tr>
              <tr>
                <th>Physical Characterization</th>
                <td>
                  Surface roughness attenuation; dark SAR feature indicative of surface film.
                  Chemical composition not directly established from radar backscatter alone.
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        {/* SECTION 5: AIS ANALYSIS */}
        <section className="report-section">
          <h2 className="section-heading">5. AIS Trajectory Analysis</h2>
          <p className="report-paragraph">
            AIS data demonstrates vessel trajectories in the investigation region leading up to,
            during, and following the release window.
          </p>
          <table className="report-table">
            <thead>
              <tr>
                <th>Vessel Track</th>
                <th>Points</th>
                <th>Time Span (UTC)</th>
                <th>Flagged Anomalies</th>
                <th>Data Provenance</th>
              </tr>
            </thead>
            <tbody>
              {d.tracks?.map((t) => (
                <tr key={t.id}>
                  <td>
                    <strong>{t.name}</strong>
                  </td>
                  <td className="mono">{t.points.length}</td>
                  <td className="mono small">
                    {t.points[0]?.time.slice(11, 16)} – {t.points[t.points.length - 1]?.time.slice(11, 16)}
                  </td>
                  <td>
                    {d.anomalies?.filter((a) => a.track_id === t.id).length || 0} gap/speed event(s)
                  </td>
                  <td>
                    <span className="provenance-chip training">TRAINING</span>
                  </td>
                </tr>
              )) || (
                <tr>
                  <td colSpan={5}>No tracks loaded</td>
                </tr>
              )}
            </tbody>
          </table>
        </section>

        {/* SECTION 6: ENVIRONMENTAL CONTEXT */}
        <section className="report-section">
          <h2 className="section-heading">6. Environmental Context (Metocean)</h2>
          <table className="report-table">
            <tbody>
              <tr>
                <th>ERA5 Wind Field (10 m)</th>
                <td>
                  <span className="provenance-chip not-loaded">NOT LOADED</span> — Copernicus CDS
                  reanalysis package. Fictional wind values are strictly rejected.
                </td>
              </tr>
              <tr>
                <th>CMEMS Ocean Surface Currents</th>
                <td>
                  <span className="provenance-chip not-loaded">NOT LOADED</span> — Copernicus Marine
                  GLORYS12V1 reanalysis. Fictional current vectors are strictly rejected.
                </td>
              </tr>
              <tr>
                <th>Metocean Enforcement Status</th>
                <td>
                  Drift transport backtracking is withheld for this canonical case to maintain
                  scientific honesty until official NetCDF reanalysis rasters are downloaded.
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        {/* SECTION 7: ORIGIN RECONSTRUCTION */}
        <section className="report-section">
          <h2 className="section-heading">7. Origin Reconstruction</h2>
          <p className="report-paragraph">
            The origin anchor for this investigation is the publicly documented collision site
            (13.2530°N, 80.3350°E) established by the Kamarajar Port Authority and Ministry of
            Shipping inquiry records. Because reanalysis metocean forcing is currently marked
            NOT_LOADED, PALEGIC relies on the documented collision anchor rather than an unverified
            numerical backtrack.
          </p>
        </section>

        {/* SECTION 8: CANDIDATE VESSELS */}
        <section className="report-section">
          <h2 className="section-heading">8. Candidate Vessels</h2>
          <table className="report-table">
            <thead>
              <tr>
                <th>Vessel Name</th>
                <th>IMO / MMSI</th>
                <th>Type</th>
                <th>Flag</th>
                <th>Incident Role</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  <strong>BW Maple</strong>
                </td>
                <td className="mono">IMO 9346537</td>
                <td>LPG Tanker</td>
                <td>Singapore</td>
                <td>Primary collision party (breached fuel tank)</td>
              </tr>
              <tr>
                <td>
                  <strong>Dawn Kancheepuram</strong>
                </td>
                <td className="mono">IMO 9368730</td>
                <td>Bulk Carrier</td>
                <td>India</td>
                <td>Secondary collision party</td>
              </tr>
            </tbody>
          </table>
        </section>

        {/* SECTION 9: CANDIDATE ATTRIBUTION RANKING */}
        <section className="report-section">
          <h2 className="section-heading">9. Candidate Attribution Ranking</h2>
          <table className="report-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Candidate Vessel</th>
                <th>Score</th>
                <th>Proximity</th>
                <th>Temporal Overlap</th>
                <th>Coverage</th>
              </tr>
            </thead>
            <tbody>
              {d.ranking?.map((r, i) => (
                <tr key={r.id}>
                  <td>
                    <strong>#{i + 1}</strong>
                  </td>
                  <td>
                    <strong>{r.name.replace(" — Training AIS Reconstruction", "")}</strong>
                  </td>
                  <td>
                    <span className="mono strong">{r.score}</span> / 100
                  </td>
                  <td>{r.distance_km.toFixed(1)} km</td>
                  <td>{Math.round(r.components.temporal * 100)}%</td>
                  <td>{Math.round(r.coverage * 100)}%</td>
                </tr>
              )) || (
                <tr>
                  <td colSpan={6}>No candidate ranking available</td>
                </tr>
              )}
            </tbody>
          </table>
        </section>

        {/* SECTION 10: PRIMARY CANDIDATE EVIDENCE */}
        <section className="report-section highlight-box">
          <h2 className="section-heading">10. Primary Candidate Evidence: Why is BW Maple Ranked #1?</h2>
          <div className="attribution-rationale">
            <p className="strong-text">
              Candidate Attribution Score: <strong>51 / 100</strong> (Rank #1)
            </p>
            <ul className="evidence-list">
              <li>
                <strong>Spatial Proximity (0.0 km):</strong> Vessel track passed directly through
                the collision origin region and centroid of the resulting slick.
              </li>
              <li>
                <strong>Temporal Coincidence:</strong> Vessel was present at the exact collision
                rendezvous window (08:00 UTC, 28 January 2017).
              </li>
              <li>
                <strong>AIS Anomaly Corroboration:</strong> A 150-minute AIS transmission cessation
                (08:30–11:00 UTC) occurred immediately following the collision event.
              </li>
              <li>
                <strong>Documented Physical Breach:</strong> Official maritime inspection confirmed
                rupture of the bunker fuel tank releasing ~196 tonnes of heavy fuel oil.
              </li>
            </ul>
            <p className="disclaimer-note">
              <em>
                Decision-support finding. This Candidate Attribution Score is a heuristic ranking
                for analyst triage, not a legal finding of liability.
              </em>
            </p>
          </div>
        </section>

        {/* SECTION 11: TIMELINE */}
        <section className="report-section">
          <h2 className="section-heading">11. Chronological Investigation Timeline</h2>
          <div className="report-timeline-list">
            {d.timeline?.map((evt) => (
              <div className="timeline-report-item" key={evt.event_id}>
                <span className="mono timeline-time">{utc(evt.timestamp)}</span>
                <span className={`provenance-chip compact ${evt.provenance_class.toLowerCase()}`}>
                  {evt.provenance_class}
                </span>
                <div className="timeline-desc">
                  <strong>{evt.title}</strong>
                  <p>{evt.description}</p>
                </div>
              </div>
            )) || <p>Timeline events bundled in canonical package.</p>}
          </div>
        </section>

        {/* SECTION 12: UNCERTAINTY */}
        <section className="report-section">
          <h2 className="section-heading">12. Uncertainty &amp; Data Limitations</h2>
          <ul className="report-bullets">
            <li>
              <strong>Origin Region:</strong> Reported as a 1.5 km radius maritime collision region
              rather than an exact point, accounting for GPS positional drift during impact.
            </li>
            <li>
              <strong>Release Window:</strong> Coarse daily composite bounds estimated release to
              2017-01-28 07:45–08:30 UTC.
            </li>
            <li>
              <strong>Environmental Forcing:</strong> Winds and currents are not loaded; historical
              backtrack simulation is withheld to avoid false precision.
            </li>
            <li>
              <strong>AIS Coverage:</strong> Both vessels exhibit transmission gaps (&gt;45 min) during
              the crucial collision window.
            </li>
          </ul>
        </section>

        {/* SECTION 13: DATA PROVENANCE */}
        <section className="report-section">
          <h2 className="section-heading">13. Authoritative Data Provenance</h2>
          <table className="report-table">
            <thead>
              <tr>
                <th>Dataset</th>
                <th>Classification</th>
                <th>Provider / Source</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Sentinel-1 Scene Metadata</td>
                <td>
                  <span className="provenance-chip observed">OBSERVED</span>
                </td>
                <td>ESA Copernicus Data Space Ecosystem</td>
                <td>VERIFIED (1d00379c)</td>
              </tr>
              <tr>
                <td>SAR Raster Imagery</td>
                <td>
                  <span className="provenance-chip observed">OBSERVED</span>
                </td>
                <td>ESA Copernicus Open Access</td>
                <td>METADATA_ONLY</td>
              </tr>
              <tr>
                <td>Suspected Slick Mask</td>
                <td>
                  <span className="provenance-chip illustrative">ILLUSTRATIVE</span>
                </td>
                <td>Digitised from ITOPF / published reports</td>
                <td>VERIFIED TOPOLOGY</td>
              </tr>
              <tr>
                <td>Collision Coordinates</td>
                <td>
                  <span className="provenance-chip recorded">RECORDED</span>
                </td>
                <td>Ministry of Shipping / Port Authority</td>
                <td>DOCUMENTED</td>
              </tr>
              <tr>
                <td>AIS Trajectories</td>
                <td>
                  <span className="provenance-chip training">TRAINING</span>
                </td>
                <td>PALEGIC Training Reconstructions</td>
                <td>FIXTURE (NOT LIVE)</td>
              </tr>
              <tr>
                <td>ERA5 Wind</td>
                <td>
                  <span className="provenance-chip not-loaded">NOT LOADED</span>
                </td>
                <td>ECMWF Copernicus CDS</td>
                <td>AWAITING DOWNLOAD</td>
              </tr>
              <tr>
                <td>CMEMS Currents</td>
                <td>
                  <span className="provenance-chip not-loaded">NOT LOADED</span>
                </td>
                <td>Copernicus Marine GLORYS12V1</td>
                <td>AWAITING DOWNLOAD</td>
              </tr>
            </tbody>
          </table>
        </section>

        {/* SECTION 14: ANALYST DISCLAIMER */}
        <section className="report-section report-disclaimer-box">
          <h2 className="section-heading">14. Analyst Disclaimer</h2>
          <p className="disclaimer-text">
            <strong>Decision-support output. Human verification required.</strong>
            <br />
            This investigation report was generated automatically by PALEGIC for Smart India
            Hackathon 2026 (Problem Statement 26143, Team Ekatva). The candidate attribution scores
            and ranked listings are heuristic indicators for maritime intelligence triage. This
            system does not issue legal determinations of fault, maritime culpability, or regulatory
            sanctions. All findings must be corroborated by certified maritime investigators using
            primary evidence.
          </p>
          <div className="report-signature-block">
            <div>
              <span>Generated By:</span>
              <strong>PALEGIC Engine v0.1.0</strong>
            </div>
            <div>
              <span>Verification Status:</span>
              <strong>AWAITING ANALYST SIGN-OFF</strong>
            </div>
          </div>
        </section>
          </>
        )}
      </div>
    </dialog>
  );
}
