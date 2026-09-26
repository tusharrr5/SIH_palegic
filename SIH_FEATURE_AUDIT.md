# PALEGIC — Smart India Hackathon 2026 (Problem 26143)
# Comprehensive Feature Audit Matrix

**Problem Statement ID:** 26143  
**Problem Statement:** Leveraging satellite imagery to determine oil spills at sea along with AIS data correlations to identify the vessel responsible for the spill.  
**Repository Name:** PALEGIC (v2 Prototype)  
**Audit Date:** 2026-09-25  

---

## Executive Feature Summary

Every major feature requested in the SIH problem statement has been analyzed against the current codebase and classified into one of the following states:
- **WORKING:** Production-grade or complete prototype implementation that functions reliably as intended.
- **PARTIALLY WORKING:** Functional within tightly constrained demo parameters, but lacking core capabilities required for real-world or hackathon evaluation.
- **MOCKED:** UI presentation backed by artificial data, fixed generators, or simulated placeholders.
- **HARDCODED:** Fixed values, magic numbers, or static strings compiled directly into code.
- **BROKEN:** Code paths that crash, reject valid requests, or fail during execution.
- **MISSING:** Features that do not exist anywhere in the repository.

| # | Feature | Status | Primary Code Reference | Critical Gap for SIH 2026 |
|---|---|---|---|---|
| 1 | Oil Spill Detection | **HARDCODED / MOCKED** | `scripts/bootstrap.py:74-128`, `api/pelagic/main.py:223-331` | No real-time or raster-based detection; only loads 3 static NOAA polygons from 2010. |
| 2 | SAR Imagery | **MISSING** | `docs/limitations.md:8`, `apps/web/components/OceanMap.tsx:150-175` | Zero raster SAR imagery (GeoTIFFs, PNG overlays, or backscatter amplitudes); only vector line/fill outlines. |
| 3 | Sentinel-1 Integration | **MISSING** | `docs/sources.md:15`, `docs/limitations.md:8` | No Copernicus Data Space / ESA API client, no GRD ingestion, no calibration, no speckle filtering. |
| 4 | AIS Vessel Data | **PARTIALLY WORKING** | `scripts/bootstrap.py:129-182`, `api/pelagic/main.py:609-674` | Bundles 3 synthetic Gulf tracks + 3 Gothenburg 2017 tracks. Admin JSON import works. No live AIS stream. |
| 5 | AIS Vessel Tracks | **WORKING** | `apps/web/components/OceanMap.tsx:192-201, 271-300`, `api/pelagic/main.py:83-100` | Renders GeoJSON LineStrings on MapLibre, splits tracks around gaps, colors distinct voyages. |
| 6 | AIS Anomaly Detection | **PARTIALLY WORKING** | `api/pelagic/analytics.py:26-70` | Rule-based heuristics (gap >45m, speed drop >=8 to <=3 kn, turn >70°). No statistical or ML anomaly detection. |
| 7 | AIS Gaps | **WORKING** | `api/pelagic/analytics.py:32-41, 73-90`, `apps/web/components/ReplayWorkspace.tsx:128-137` | Detects gaps >45m, breaks track rendering, skips interpolation, and offers clickable jump buttons in UI. |
| 8 | Vessel Information | **PARTIALLY WORKING / HARDCODED** | `scripts/bootstrap.py:130-132`, `api/pelagic/main.py:431-438` | Synthetic tracks only have names ("ALPHA"). Recorded Gothenburg tracks have MMSI/ShipType. No registry or IMO lookups. |
| 9 | Wind Data | **MISSING** | `api/pelagic/analytics.py:188`, `apps/web/components/EvidencePanel.tsx:349-352` | No live or historical wind API (ECMWF/ERA5/NOAA GFS). Hardcoded constant `[4.0, 2.0]` m/s used in sandbox. |
| 10 | Ocean-Current Data | **MISSING** | `api/pelagic/analytics.py:187`, `apps/web/components/EvidencePanel.tsx:353-357` | No ocean current feeds (CMEMS/HYCOM/OSCAR). Hardcoded constant `[0.12, -0.06]` m/s used in sandbox. |
| 11 | Drift Simulation | **PARTIALLY WORKING (Sandbox Only)** | `api/pelagic/analytics.py:161-224` | 2D kinematic Lagrangian particle forward/backward stepping with fixed seed 42. Pure toy model; no physical oceanography. |
| 12 | Hindcasting | **BROKEN / MISSING** | `api/pelagic/main.py:382-386` | Historical hindcast endpoint intentionally throws `HTTPException(409)`. Operational hindcasting is completely blocked. |
| 13 | Origin Reconstruction | **MISSING / MOCKED** | `api/pelagic/analytics.py:196-197`, `docs/scientific-method.md:36-38` | Does not find release origin or time. Only draws convex hull around backtracked particles under constant forcing. |
| 14 | Vessel Attribution | **MOCKED / HARDCODED** | `api/pelagic/analytics.py:93-159` | No legal or causal attribution. Vessels are simply sorted by an ad-hoc heuristic score. |
| 15 | Candidate Vessel Ranking | **WORKING (Heuristic Only)** | `api/pelagic/analytics.py:138-140` | Scores nearby vessels using proximity (60%), time (25%), behavior (15%), and coverage penalty. |
| 16 | Confidence Scoring | **MOCKED / HARDCODED HEURISTIC** | `api/pelagic/analytics.py:138-156` | Returns an arbitrary score out of 100. UI and code explicitly disclaim it is not a probability. |
| 17 | Evidence Correlation | **PARTIALLY WORKING** | `api/pelagic/main.py:254-265`, `apps/web/components/EvidencePanel.tsx:138-186` | Spatio-temporal matching within 100 km and ±24 hours links cases and tracks. No multi-sensor cross-validation. |
| 18 | Investigation Timeline | **WORKING** | `apps/web/app/page.tsx:554-653`, `apps/web/components/ReplayWorkspace.tsx:238-316` | Full timeline UI with play/pause, time scrubber, UTC clock, and 3-day public archive switcher. |
| 19 | Replay Functionality | **WORKING** | `api/pelagic/analytics.py:73-90`, `apps/web/app/page.tsx:150-183`, `ReplayWorkspace.tsx` | Server-side WGS84 geodesic interpolation accurately animates vessels along track paths at variable speeds. |
| 20 | Demo Functionality | **WORKING** | `scripts/demo.py`, `scripts/preflight.py`, `docs/demo-script.md` | Single-command launch (`scripts/demo.py`) with pre-seeded Gulf and Gothenburg scenarios running 100% offline. |
| 21 | Report Generation | **PARTIALLY WORKING** | `api/pelagic/main.py:454-494` | Downloads JSON evidence package (`pelagic-evidence/1`). No PDF report, executive summary, or visual export. |
| 22 | Alerts | **MISSING** | Entire repository | No alert system, notification center, Webhook, SMS, or automated background slick monitors. |
| 23 | Map Layers | **PARTIALLY WORKING** | `apps/web/components/OceanMap.tsx:147-202` | Toggles for Surface Anomaly, AIS tracks, particle clouds, convex hull. Missing SAR raster, bathymetry, wind, currents. |
| 24 | Case Management | **WORKING** | `api/pelagic/main.py:197-208, 307-331, 347-370` | Full CRUD lifecycle: creation (AIS/SAR), review notes with optimistic locking, status updates, audit log. |
| 25 | Historical Incidents | **HARDCODED** | `scripts/bootstrap.py:74-128` | Deepwater Horizon (May 2010, 3 daily composites). No Indian maritime incidents or other global spills. |

---

## Detailed Audit of the 25 Critical Features

### 1. Oil Spill Detection
- **Classification:** HARDCODED / MOCKED
- **Evidence:** `scripts/bootstrap.py` lines 74–128 reads pre-packaged GeoJSON files (`dwh-2010-05-17.geojson`, `dwh-2010-05-19.geojson`, `dwh-2010-05-20.geojson`) downloaded from NOAA/NESDIS via GCOOS.
- **Implementation Reality:** When a user creates a "SAR first" detection in `api/pelagic/main.py:265-271`, the backend simply selects an existing row from the `observations` table. No satellite pixels are parsed, no dark spot detection algorithm runs, and no thresholding or clustering is performed.
- **Hackathon Gap:** Evaluators will expect an AI/ML or image processing pipeline that takes raw or preprocessed satellite images and outputs detected spill masks.

### 2. SAR Imagery
- **Classification:** MISSING
- **Evidence:** `apps/web/components/OceanMap.tsx` lines 59–85 initializes MapLibre with vector land fill and coast lines. Lines 150–175 add layers for `"slick-fill"`, `"slick-glow"`, and `"slick-line"`.
- **Implementation Reality:** There is NO raster SAR imagery anywhere in the project. The slicks are displayed strictly as semi-transparent orange vector polygons (`fill-color: "#f5b56f"`).
- **Hackathon Gap:** The problem statement specifically mentions "leveraging satellite imagery". The app does not display any satellite imagery at all—only vector shapes.

### 3. Sentinel-1 Integration
- **Classification:** MISSING
- **Evidence:** `docs/sources.md` line 15 explicitly notes: *"Do not describe these as Sentinel-1 imagery or newly detected oil."* and `docs/limitations.md` line 8 notes: *"Sentinel-1 retrieval, calibration, segmentation, validation and look-alike rejection: Deferred / required for operational use"*.
- **Implementation Reality:** There are no APIs or scripts connecting to Copernicus Data Space Ecosystem (CDSE), Copernicus Open Access Hub, ASF DAAC, or Google Earth Engine.
- **Hackathon Gap:** Sentinel-1 Synthetic Aperture Radar is the primary free, operational sensor for maritime oil detection globally and in Indian waters.

### 4. AIS Vessel Data
- **Classification:** PARTIALLY WORKING
- **Evidence:** `scripts/bootstrap.py:129-182` and `api/pelagic/main.py:609-674`.
- **Implementation Reality:** Ingestion of static AIS data is fully supported. Admin users can upload custom JSON trajectories via `POST /api/admin/ais`. 3 synthetic training tracks and 3 real recorded Danish Maritime Authority tracks are pre-seeded. However, there is no real-time stream ingestion (NMEA 0183/2000, WebSockets, or AIS aggregator APIs).
- **Hackathon Gap:** Demonstrations cannot stream live AIS feeds from coastal Indian waters.

### 5. AIS Vessel Tracks
- **Classification:** WORKING
- **Evidence:** `apps/web/components/OceanMap.tsx:271-300`, `api/pelagic/analytics.py:17-20`.
- **Implementation Reality:** The map renders LineString trajectories with color-coded styling. When time scrubs forward, tracks grow dynamically. Gaps over 45 minutes correctly sever the line into discontinuous segments rather than drawing false lines across the ocean.

### 6. AIS Anomaly Detection
- **Classification:** PARTIALLY WORKING / HARDCODED HEURISTICS
- **Evidence:** `api/pelagic/analytics.py:26-70`.
- **Implementation Reality:** Evaluates three hardcoded thresholds:
  1. Reporting gap: `(t_b - t_a) > 45` minutes.
  2. Sudden slowdown: Speed drops from $\ge 8.0$ kn to $\le 3.0$ kn within 45 minutes.
  3. Sharp course alteration: Course change $>70^\circ$ within 45 minutes.
  These events are tagged and displayed in the UI ("Speed fell to 1.8 kn", "70° course change").
- **Hackathon Gap:** These are simple `if` statements. There is no clustering (DBSCAN), no trajectory modeling, no loitering detection, and no dark vessel / AIS transponder tampering detection.

### 7. AIS Gaps
- **Classification:** WORKING
- **Evidence:** `api/pelagic/analytics.py:32-41`, `apps/web/components/ReplayWorkspace.tsx:373-386`.
- **Implementation Reality:** Replay strictly respects gaps $>45$ minutes: the vessel marker disappears during the gap and reappears upon the next received report. In `ReplayWorkspace.tsx`, dedicated buttons ("Reception gap · 08:32–09:51 UTC") allow the investigator to jump directly into the gap.

### 8. Vessel Information
- **Classification:** PARTIALLY WORKING / HARDCODED
- **Evidence:** `data/source/ais-replay.json`, `apps/web/components/ReplayWorkspace.tsx:321-350`.
- **Implementation Reality:** For Gothenburg tracks, metadata includes MMSI (`265410000`), vessel name (`STENA JUTLANDICA`), ship type (`Passenger`), report count, and data provider. For Gulf training tracks, only names (`Training vessel ALPHA`) exist.
- **Hackathon Gap:** Missing IMO numbers, callsign, country flag / MMSI MID decoding, vessel dimensions, draught, cargo type, and vessel risk profile.

### 9. Wind Data & 10. Ocean-Current Data
- **Classification:** MISSING
- **Evidence:** `api/pelagic/analytics.py:187-188`:
  ```python
  current = np.array([0.12, -0.06])
  wind = np.array([4.0, 2.0])
  ```
  And `apps/web/components/EvidencePanel.tsx:343-357` displays:
  - *Acquisition time: Day-level only*
  - *Wind field: Missing*
  - *Current field: Missing*
- **Implementation Reality:** Zero dynamic metocean forcing data. The app explicitly states: *"Verified, time-matched ocean currents and wind fields are not included in this cached pack."*
- **Hackathon Gap:** Oil drift cannot be accurately modeled or defended without real or simulated hydrodynamic current fields and wind vectors.

### 11. Drift Simulation
- **Classification:** PARTIALLY WORKING (Sandbox Only)
- **Evidence:** `api/pelagic/analytics.py:161-224` (`particle_backtrack()`).
- **Implementation Reality:** Runs a 2D kinematic Lagrangian equation over 160 particles with a constant current vector, 3% wind factor, and random diffusion ($K = 8.0\text{ m}^2/\text{s}$) with seed 42. Output is rendered on MapLibre as purple circles with a convex hull.
- **Hackathon Gap:** It is not connected to OpenDrift, GNOME, or any hydrodynamic physics engine. It ignores oil weathering, evaporation, emulsification, Stokes drift, and coastal boundaries.

### 12. Hindcasting
- **Classification:** BROKEN / MISSING
- **Evidence:** `api/pelagic/main.py:382-386`:
  ```python
  if body.mode == "historical":
      raise HTTPException(
          409,
          "Historical reconstruction unavailable: verified wind/current fields and acquisition timing are required.",
      )
  ```
- **Implementation Reality:** Calling the API to run an incident hindcast intentionally fails with an HTTP 409 error.
- **Hackathon Gap:** The SIH problem statement specifically requires determining which vessel caused a spill, which fundamentally requires hindcasting (backtracking from the observed slick to the candidate track's intersection).

### 13. Origin Reconstruction
- **Classification:** MISSING / MOCKED
- **Evidence:** `docs/scientific-method.md:36-38`, `api/pelagic/analytics.py:196-197`.
- **Implementation Reality:** The system computes the convex hull of backtracked particles under uniform constant drift. It does not solve for an estimated release time or release point $(x, y, t)$.

### 14. Vessel Attribution & 15. Candidate Vessel Ranking
- **Classification:** WORKING (Heuristic Ranking) / MOCKED (Legal Attribution)
- **Evidence:** `api/pelagic/analytics.py:93-159` (`rank_sources()`).
- **Implementation Reality:** Ranks vessels based on proximity ($60\%$), time overlap ($25\%$), and behavior anomalies ($15\%$) scaled by an AIS coverage penalty.
- **Hackathon Gap:** The score is a heuristic priority for human analysts, not a machine-learned attribution or legally defensible causal probability.

### 16. Confidence Scoring
- **Classification:** MOCKED / HARDCODED HEURISTIC
- **Evidence:** `api/pelagic/analytics.py:138-140`.
- **Implementation Reality:** The score is an integer between 0 and 100 calculated by the heuristic formula. The UI includes explicit disclaimers: *"Priority score, not a probability"*.

### 17. Evidence Correlation
- **Classification:** PARTIALLY WORKING
- **Evidence:** `api/pelagic/main.py:254-265`.
- **Implementation Reality:** Queries PostGIS using `ST_DWithin` ($100\text{ km}$) and timestamp filtering ($\pm 24\text{ hours}$) to link AIS anomaly points with observation polygons. Stores the resulting candidates inside the `cases.findings` JSON field.

### 18. Investigation Timeline & 19. Replay Functionality
- **Classification:** WORKING
- **Evidence:** `apps/web/app/page.tsx:150-183, 554-653`, `apps/web/components/ReplayWorkspace.tsx:238-316`, `api/pelagic/analytics.py:73-90`.
- **Implementation Reality:** Both case-level replay and standalone AIS replay are fully implemented and functional. The timeline scrubs through time, triggers backend geodesic interpolation, and smoothly moves vessel markers across the map while respecting AIS gaps.

### 20. Demo Functionality
- **Classification:** WORKING
- **Evidence:** `scripts/demo.py`, `docs/demo-script.md`.
- **Implementation Reality:** `python scripts/demo.py` spins up FastAPI and Next.js, and everything runs offline without third-party dependencies or external network queries.

### 21. Report Generation
- **Classification:** PARTIALLY WORKING
- **Evidence:** `api/pelagic/main.py:454-494` (`GET /api/cases/{case_id}/export`).
- **Implementation Reality:** Generates and downloads a clean JSON file containing all case findings, rankings, review notes, and source SHA-256 manifests.
- **Hackathon Gap:** Hackathon judges and port authorities expect an automated, downloadable PDF dossier with maps, charts, evidence tables, and official executive summaries.

### 22. Alerts
- **Classification:** MISSING
- **Evidence:** Entire codebase. No WebSocket channels, SSE, email triggers, or notification bells exist.

### 23. Map Layers
- **Classification:** PARTIALLY WORKING
- **Evidence:** `apps/web/components/OceanMap.tsx:147-202, 268-270`.
- **Implementation Reality:** Supports toggling slick polygons and AIS tracks, plus rendering particle clouds and bounding envelopes. Lacks raster satellite layers, weather overlays, sea depth/bathymetry, or maritime boundary layers (EEZ).

### 24. Case Management
- **Classification:** WORKING
- **Evidence:** `api/pelagic/main.py:197-208, 307-331, 347-370`.
- **Implementation Reality:** Cases can be created, viewed, filtered, and officially reviewed. Review notes require $\ge 10$ characters, verify the case version to prevent concurrent overwrites, and record the officer's user ID and timestamp in an immutable audit table.

### 25. Historical Incidents
- **Classification:** HARDCODED
- **Evidence:** `scripts/bootstrap.py:74-128`.
- **Implementation Reality:** Only 1 historical incident is present: the Deepwater Horizon disaster in the Gulf of Mexico (3 days in May 2010). No incidents from Indian coastal waters (e.g. Mumbai, Chennai/Ennore, Gulf of Kutch) exist in the system.
