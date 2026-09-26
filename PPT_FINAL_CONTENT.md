# PALEGIC — SIH 2026 Presentation Content (PPT)

**Product:** PALEGIC  
**Problem Statement ID:** 26143  
**Problem Statement:** Leveraging satellite imagery to determine Oil spills at sea along with AIS data correlations to identify vessel responsible for the spill  
**Team:** Ekatva  
**Theme:** Maritime Safety, Environmental Monitoring & Geospatial Intelligence  

---

## SLIDE 1: Title Slide

### Slide Header & Content
* **Product Name:** PALEGIC
* **Tagline:** Explainable Oil Spill Detection, Origin Reconstruction & Vessel Attribution
* **Problem Statement:** 26143 — Smart India Hackathon 2026
* **Team:** Ekatva
* **Core Value Proposition:** Fusing Sentinel-1 Synthetic Aperture Radar (SAR), Automatic Identification System (AIS) vessel trajectories, and hydrodynamic drift modeling to hold maritime polluters accountable.

### Speaker Notes
> "Good morning, respected judges and evaluators. We are Team Ekatva, presenting PALEGIC — an explainable maritime intelligence platform engineered for Problem Statement 26143. PALEGIC leverages satellite imagery and AIS data correlation to identify the vessels responsible for marine oil spills, transforming raw sensor signals into legally defensible, explainable evidence."

---

## SLIDE 2: Problem & Operational Reality

### Key Points
1. **The Surface Paradox:** Where oil is detected on the surface is almost never where it was discharged. Coastal winds, surface currents, and tides rapidly disperse slicks miles from the release point.
2. **The Proximity Fallacy:** Looking for vessels closest to the slick at the time of satellite acquisition yields false positives — the guilty vessel may have cleared port hours earlier while innocent traffic passes over the aged slick.
3. **The Data Gap:** Vessels frequently disable AIS transponders or reduce transmission frequency during intentional discharge or post-collision panic.
4. **Dual Operational Triggers:**
   * **SAR-First:** A satellite overpass captures an unexplained surface anomaly. PALEGIC backtracks the slick to identify candidate vessels.
   * **AIS-First:** An AIS transmission gap, speed anomaly, or distress alert triggers an immediate satellite acquisition tasking and forward-trajectory search.

### Speaker Notes
> "In maritime pollution enforcement, two critical fallacies lead to failed prosecutions. First, surface slicks drift rapidly; the slick you see at 06:00 UTC might have been released 15 nautical miles away at midnight. Second, simple AIS proximity is misleading — ships closest to the slick when the satellite passes are often innocent bystanders. PALEGIC overcomes this with dual-trigger workflows: SAR-First to backtrack surface signals, and AIS-First to investigate suspicious vessel maneuvers."

---

## SLIDE 3: How PALEGIC Works (Investigation Pipeline)

### The 7-Stage End-to-End Investigation Chain
```
[Satellite SAR Imagery]  +  [AIS Vessel Tracking]
          │                        │
          ▼                        ▼
 1. Surface Anomaly        2. Trajectory Ingestion
    Detection / Mask          & Gap Detection
          │                        │
          └───────────┬────────────┘
                      ▼
        3. Multimodal Evidence Fusion
                      ▼
        4. Origin Reconstruction & Release Window
                      ▼
        5. Explainable Candidate Scoring Pipeline
           (Spatial 60% • Temporal 25% • Behavior 15%)
                      ▼
        6. Synchronized Temporal Replay
                      ▼
        7. Official Investigation Report (14 Sections + PDF)
```

### Key Principles
* **Multi-Modal Evidence:** Never attibute based on a single sensor.
* **Deterministic Calculations:** Calibrated Candidate Attribution Scores (0–100) instead of ungrounded black-box "guilt percentages".
* **Court-Ready Transparency:** Every intermediate finding retains strict provenance classifications.

### Speaker Notes
> "PALEGIC functions as a complete end-to-end investigation chain. It ingests Sentinel-1 SAR observations alongside AIS trajectories, correlates spatial and temporal envelopes, reconstructs the origin zone, and runs a multi-factor attribution algorithm. Rather than an opaque black box, every candidate vessel receives a transparent score with an explicit 'Why Ranked First' breakdown."

---

## SLIDE 4: System Architecture

### Engineering Stack (Actual Implemented Architecture)
* **Frontend:** Next.js 15 (App Router, React 19, TypeScript), Vanilla CSS design system, dark-mode maritime aesthetic.
* **Geospatial Mapping:** MapLibre GL with custom WebGL vector layers, polygon rendering, and trajectory rendering.
* **Backend API:** FastAPI (Python 3.12), RESTful endpoints, asynchronous request handling, rate limiting, and role-based session authentication (Officer / Authority).
* **Database & Geospatial Engine:** PostgreSQL 17 + PostGIS 3.5, spatial indexing (`ST_DWithin`, `ST_Centroid`, `ST_AsGeoJSON`).
* **Scientific Analysis Engine:** Custom Python scientific analytics module (`pelagic.analytics`) executing deterministic candidate scoring, gap anomaly detection, and trajectory normalization.
* **Deployment & Demo Architecture:** Zero-dependency Cached / Precomputed Demonstration Mode supporting offline, reliable judging without third-party API rate limits.

### Speaker Notes
> "Our architecture is purpose-built for high-reliability maritime intelligence. We combine a high-performance Next.js 15 frontend and MapLibre GL with a FastAPI and PostgreSQL/PostGIS geospatial backend. All spatial calculations occur in EPSG:4326/WGS84. Crucially for deployment, our system features a deterministic Demo Mode: when external satellite APIs or reanalysis services are unavailable, the canonical investigation operates seamlessly from verified cached packs."

---

## SLIDE 5: Key Innovations & Strategic Impact

### 6 Pillars of Innovation
1. **Explainable Attribution Score:** Answers the judge's exact question: *"Why is this vessel ranked #1?"* with factual statements (proximity, release window overlap, AIS transmission gaps).
2. **Transparent Uncertainty Modeling:** Reports origin regions (±1.5 km) and time envelopes rather than false-precision coordinates.
3. **Synchronized Replay Workspace:** Fully deterministic 0.5x–4x timeline playback synchronizing vessel positions, active events, and candidate rankings.
4. **Dual-Trigger Architecture:** Seamlessly handles both satellite-initiated and AIS-initiated investigations.
5. **Strict Data Provenance:** Every datum is explicitly classified as `OBSERVED`, `REANALYSIS`, `TRAINING`, `ILLUSTRATIVE`, `DERIVED`, or `NOT_LOADED`.
6. **One-Click Formal Reporting:** Generates a complete 14-section Marine Pollution Investigation Report with browser PDF export for maritime law enforcement.

### Speaker Notes
> "Our key innovation is explainability. Maritime law requires legal defensibility, not just AI guesses. PALEGIC reports uncertainty openly — bounding release windows and origin zones honestly. Its synchronized replay lets investigators watch collisions and discharges unfold step by step. And with one click, it produces a court-defensible 14-section investigation report ready for Indian Coast Guard and port command."

---

## SLIDE 6: Prototype, Benchmark & Research Roadmap

### Canonical Benchmark: `SIH-ENNORE-2017`
* **Real Incident:** 28 January 2017 collision between LPG tanker *BW Maple* and bulk carrier *Dawn Kancheepuram* off Kamarajar Port, Chennai.
* **Satellite Scene:** Sentinel-1A IW GRDH scene `S1A_IW_GRDH_1SDV_20170129T003132_20170129T003157_015024_01889C_887A` verified in Copernicus Data Space Ecosystem.
* **Vessel Attribution:** Correctly ranks *BW Maple* (#1, score 51) and *Dawn Kancheepuram* (#2, score 50) based on documented collision coordinates and 150-minute AIS gap.

### Implemented vs. Research Roadmap
| Component | Implemented in Current Build | Planned Phase 3 / Production Roadmap |
|---|---|---|
| **Satellite Imagery** | CDSE Sentinel-1 catalogue metadata (OBSERVED), footprint visualization | Full SNAP/SAR backscatter raster oil segmentation pipeline |
| **Vessel Tracking** | High-fidelity training AIS tracks, gap detection (>45 min), speed anomaly flags | National AIS direct receiver feed integration (DGLL / Navy) |
| **Attribution** | Deterministic 4-factor scoring pipeline with evidence explanations | Bayesian calibrated probability models |
| **Environmental** | Schema & reanalysis ingestion framework (ERA5 / CMEMS) | Live operational OpenDrift / OpenOil numerical modeling |
| **Reporting** | 14-section interactive report with PDF export & JSON data download | Automated multi-agency dispatch & digital signature chain of custody |

### Live Prototype Access
* **Interactive URL:** `https://pelagic-sih-2026.loca.lt` (or `http://127.0.0.1:3100/?demo=true`)
* **QR Code Recommendation:** Place QR code in the bottom right corner of this slide linking directly to the live prototype.
* **Credentials:** Instant Authority 1-click access via `RUN SIH DEMO`.

### Speaker Notes
> "On Slide 6, we demonstrate our benchmark against the historic 2017 Ennore oil spill. PALEGIC successfully correlates the genuine Copernicus Sentinel-1A scene with the vessels' reconstructed tracks, identifying both collision parties and highlighting their AIS gaps. In our roadmap, we outline direct integration with India's DGLL coastal AIS network and live OpenDrift hydrodynamic modeling. You can scan the QR code right now to test the live prototype on your own devices. Thank you!"
