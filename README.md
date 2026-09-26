# PALEGIC — SIH 2026 Final Release

**Problem Statement ID:** 26143  
**Problem Statement:** Leveraging satellite imagery to determine Oil spills at sea along with AIS data correlations to identify vessel responsible for the spill.  
**Team:** Ekatva  
**Live Demo:** LIVE DEMO: <URL>  
**Local Demo Origin:** `http://127.0.0.1:3000/?demo=true`  

---

## 1. Executive Summary

PALEGIC is an explainable maritime intelligence platform engineered to detect, backtrack, and attribute marine oil spills to responsible vessels. Unlike simplistic proximity models or opaque black-box classifiers, PALEGIC fuses Synthetic Aperture Radar (SAR) observations from Sentinel-1 with Automatic Identification System (AIS) vessel trajectories, origin reconstruction modeling, and comprehensive uncertainty tracking.

Every candidate attribution score is mathematically computed and accompanied by transparent factual evidence explaining **"WHY IS THIS VESSEL RANKED FIRST?"**

---

## 2. Key Features

* **Dual-Trigger Architecture:**
  * **SAR-First:** Detects surface slicks via satellite overpasses and backtracks candidate vessels within the temporal release window.
  * **AIS-First:** Investigates vessel maneuvers, transmission gaps, and speed anomalies to identify potential discharges.
* **Deterministic Benchmark Case (`SIH-ENNORE-2017`):**
  * Real-world January 2017 collision between *BW Maple* and *Dawn Kancheepuram* off Kamarajar Port (Ennore), Chennai.
  * Verified Sentinel-1A SAR scene metadata from Copernicus Data Space Ecosystem (CDSE).
  * Ranked attribution surfacing *BW Maple* (#1, score 51) and *Dawn Kancheepuram* (#2, score 50).
* **Geospatial Map Workspace (MapLibre GL):**
  * Layer toggles for surface slick, AIS trajectories, reception gaps (>45 min), Sentinel-1 footprint, and collision origin zone.
  * Distinct color-coded vector styling.
* **Synchronized Investigation Replay:**
  * Interactive playback (0.5x, 1x, 2x, 4x), backward scrubbing, and deterministic event-synchronized state updates.
* **Court-Defensible 14-Section Report:**
  * One-click compilation of official **Marine Pollution Investigation Reports** with browser PDF export and JSON export.
* **Zero-Friction Demo Mode:**
  * Self-contained cached benchmark requiring zero external API keys, third-party network connectivity, or judge authentication.

---

## 3. System Architecture

```
[ Next.js 15 Frontend (Port 3100) ]
        │  ▲
        │  │  Reverse proxy /api rewrites & cookie handling
        ▼  │
[ FastAPI Python Backend (Port 8100) ]
        │  ▲
        │  │  SQL & GeoJSON queries
        ▼  │
[ PostgreSQL 17 + PostGIS 3.5 (Port 5432) ]
        ▲
        │  In-process scientific analytics
[ pelagic.analytics Engine ]
```

* **Frontend:** Next.js 15 (App Router, React 19, TypeScript), Vanilla CSS design system, dark-mode maritime aesthetic.
* **Geospatial Engine:** MapLibre GL with WebGL polygon and line rendering.
* **Backend API:** FastAPI (Python 3.12), RESTful endpoints, CORS/origin checking, and role-based access control.
* **Database:** PostgreSQL 17 with PostGIS spatial extension.
* **Scientific Core:** Pure Python scientific analytics module (`pelagic.analytics`) calculating spatial proximity, temporal overlap, and AIS anomaly metrics.

---

## 4. Scientific Provenance Integrity

PALEGIC enforces strict provenance separation across all ingested datasets:

| Data Layer | Canonical Classification | Provenance Source & Integrity |
|---|---|---|
| **Satellite Radar (Catalogue)** | `OBSERVED` | Genuine ESA Sentinel-1A scene metadata verified via Copernicus Data Space Ecosystem (CDSE). |
| **Satellite Radar (Raster)** | `METADATA_ONLY` | Catalogue metadata cached; raw SAR backscatter raster is not downloaded to avoid false classification claims. |
| **Slick Geometry** | `ILLUSTRATIVE` | Polygon outline digitized from official published casualty investigation reports, not synthetic AI hallucination. |
| **AIS Vessel Trajectories** | `TRAINING` | High-fidelity trajectories reconstructed from published incident times and coordinates; labeled as training data. |
| **Collision Origin** | `DERIVED` / `RECORDED` | Documented collision coordinates (13.2530°N, 80.3350°E) from Directorate General of Shipping India. |
| **ERA5 Wind Reanalysis** | `NOT_LOADED` | Real ECMWF reanalysis pipeline structured; physical backtracking withheld to prevent false precision. |
| **CMEMS Ocean Currents** | `NOT_LOADED` | Copernicus Marine reanalysis pipeline structured; physical simulation withheld without validated fields. |

---

## 5. Local Setup & Execution

### Prerequisites
* Python 3.11+
* Node.js 22+
* PostgreSQL 15+ with PostGIS

### Quickstart

1. **Clone repository and configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your local PostgreSQL DATABASE_URL
   ```

2. **Backend Setup:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   python scripts/bootstrap.py
   ```

3. **Frontend Setup:**
   ```bash
   npm --prefix apps/web ci
   npm --prefix apps/web run build
   ```

4. **Launch Servers:**
   ```bash
   # Terminal 1: Backend
   .venv/bin/python -m uvicorn pelagic.main:app --app-dir api --host 127.0.0.1 --port 8100

   # Terminal 2: Frontend
   npm --prefix apps/web run start
   ```

5. **Open Demo:**
   Navigate to [http://127.0.0.1:3000/?demo=true](http://127.0.0.1:3000/?demo=true) and click **RUN SIH DEMO**.

---

## 6. Production Deployment

PALEGIC is deployed on a unified production host using Docker Compose and an Nginx reverse proxy:

* **LIVE DEMO:** `<URL>`
* **Production Runbook:** Refer to [SIH_PRODUCTION_RUNBOOK.md](SIH_PRODUCTION_RUNBOOK.md) for server hardware sizing, Docker installation, database initialization, TLS/HTTPS domain setup, and operational recovery.
* **Validation Report:** Refer to [DEPLOYMENT_VALIDATION.md](DEPLOYMENT_VALIDATION.md) for component-level pass/fail audit.

### Quick Production Launch

```bash
# 1. Copy environment template
cp .env.example .env
# Edit .env with secure passwords and production domain

# 2. Build containers from scratch
docker compose build --no-cache

# 3. Deterministic DB schema bootstrap & canonical seed
docker compose run --rm init-db

# 4. Start production stack
docker compose up -d

# 5. Verify health
curl -s http://localhost/healthz
curl -s http://localhost/api/health
```

---

## 7. Automated Testing & Verification

The codebase includes an extensive automated test suite:

```bash
# 1. Run Python unit & scientific tests (121 tests)
.venv/bin/pytest tests/

# 2. Run TypeScript typechecking
npm --prefix apps/web run typecheck

# 3. Run End-to-End Playwright Smoke Test (17 automated checks)
node apps/web/scripts/smoke_test_e2e.mjs
```

### Smoke Test Results (100% Pass)
* Landing Page: **PASS**
* Canonical Case Loaded: **PASS**
* Map Layers Present: **PASS**
* Layer Toggles Work: **PASS**
* Candidate Ranking: **PASS**
* Explainable Attribution: **PASS**
* Replay Controls (Play, Pause, Speed, Scrub, Restart): **PASS**
* Timeline Events (13 events with provenance): **PASS**
* Evidence & Uncertainty Panel: **PASS**
* Report Modal & 14 Sections: **PASS**
* Hard Refresh `/ ?demo=true`: **PASS**

---

## 7. Known Limitations & Research Roadmap

* **Raster Segmentation:** Live radar backscatter segmentation requires local GPU instances and Copernicus credentials; currently catalogue metadata is verified with illustrative geometry.
* **Hydrodynamic Drift:** Metocean reanalysis (ERA5/CMEMS) is cached/unloaded; numerical backtracking is withheld in demo mode to maintain strict scientific honesty.
* **AIS Feed:** In production, AIS will connect directly to DGLL coastal receiver networks; currently using verified incident reconstructions.

---

## 8. Team & Credits

**Team Ekatva** — Smart India Hackathon 2026  
*Problem Statement 26143: Maritime Oil Spill Detection & AIS Vessel Attribution*
