# PALEGIC — SIH 2026 Release Report

**Project:** PALEGIC — Explainable Oil Spill Investigation & Vessel Attribution  
**Problem Statement ID:** 26143  
**Team:** Ekatva  
**Release Date:** 26 September 2026  
**Canonical Demonstration Case:** `SIH-ENNORE-2017`  

---

## 1. System Deployment Status

| Component | Status | Details / URL |
|---|---|---|
| **Public Deployment URL** | **LIVE / PASS** | [https://pelagic-sih-2026.loca.lt](https://pelagic-sih-2026.loca.lt) *(Tunnel Password / IP: `112.110.51.145`)* |
| **Local Demonstration Origin** | **LIVE / PASS** | `http://127.0.0.1:3100/?demo=true` |
| **Frontend Service** | **PASS** | Next.js 15.5.25 production bundle on port 3100 |
| **Backend API Service** | **PASS** | FastAPI (Python 3.12) daemon on port 8100 |
| **Geospatial Database** | **PASS** | PostgreSQL 17 + PostGIS 3.5 seeded with canonical Ennore records |
| **SIH Demo Mode** | **PASS** | Zero-credential, 100% deterministic, offline/cached package |
| **Canonical Incident** | **PASS** | `SIH-ENNORE-2017` fully integrated and validated |

---

## 2. Feature Verification Matrix

| Feature | Status | Verification Detail |
|---|---|---|
| **Landing Page** | **PASS** | PALEGIC branding, subtitle, problem statement badge, and primary CTA. |
| **Run Demo CTA** | **PASS** | One-click entry loading canonical case `SIH-ENNORE-2017` immediately. |
| **Geospatial Map** | **PASS** | MapLibre GL rendering dark-mode ocean map centered on Ennore / Kamarajar Port. |
| **SAR Observation Layer** | **PASS** | Sentinel-1A footprint vector (cyan) from verified CDSE catalogue scene. |
| **Suspected Slick Geometry** | **PASS** | 7 km² illustrative polygon rendered with amber stroke and fill. |
| **AIS Tracks Layer** | **PASS** | Trajectories for *BW Maple* and *Dawn Kancheepuram* with coordinate history. |
| **AIS Anomalies / Gaps** | **PASS** | Visualized with dashed red line segments for transmission gaps >45 minutes. |
| **Environmental Context** | **PASS** | ERA5 and CMEMS status disclosed; reanalysis integration framework documented. |
| **Origin Reconstruction** | **PASS** | Documented collision site with purple uncertainty halo (±1.5 km). |
| **Candidate Ranking** | **PASS** | Multi-factor attribution scoring ranking *BW Maple* (#1: 51) and *Dawn Kancheepuram* (#2: 50). |
| **Explainable Attribution** | **PASS** | "WHY IS THIS VESSEL RANKED FIRST?" answers proximity, time overlap, and AIS gaps. |
| **Evidence Panel** | **PASS** | Multi-tab drawer (Evidence, Sources, Timeline, Transport, Review). |
| **Uncertainty Transparency** | **PASS** | Explicit origin region, release window bounds, and decision-support caveats. |
| **Timeline** | **PASS** | 13 chronological events with strict provenance badges (RECORDED, TRAINING, OBSERVED, DERIVED). |
| **Synchronized Replay** | **PASS** | Play, Pause, Speed (0.5x, 1x, 2x, 4x), Scrubbing, and Restart synchronization. |
| **Report Generation** | **PASS** | Complete 14-section Marine Pollution Investigation Report with Print/PDF export. |
| **Reset / Re-run** | **PASS** | Hard refresh and navigation to `/?demo=true` restarts cleanly with identical state. |

---

## 3. Automated Test Summary

* **Frontend Typecheck:** **PASS** (`tsc --noEmit` with zero errors).
* **Frontend Production Build:** **PASS** (`next build` compiled in 1055ms, 5/5 static pages).
* **Backend Pytest Suite:** **121 PASSED, 0 FAILED** (4.12s across API, science, and Phase 2 validation).
* **Playwright E2E Smoke Test:** **17 PASSED, 0 FAILED** (100% automated pass across all user journeys).

---

## 4. Authoritative Data Provenance

| Major Dataset | Provenance Classification | Scientific Integrity Note |
|---|---|---|
| **Sentinel-1 Scene Metadata** | `OBSERVED` | Scene `S1A_IW_GRDH_1SDV_20170129T003132` verified from CDSE. |
| **Sentinel-1 Raster** | `METADATA_ONLY` | Raw SAR backscatter raster not downloaded; no false AI claims. |
| **Slick Geometry** | `ILLUSTRATIVE` | Polygon outline digitized from official published records. |
| **AIS Vessel Tracks** | `TRAINING` | High-fidelity trajectory reconstruction; strictly labeled as training AIS. |
| **Collision Origin** | `DERIVED` / `RECORDED` | Extracted from official casualty report by Ministry of Shipping India. |
| **ERA5 Wind Reanalysis** | `NOT_LOADED` | Real ECMWF API pipeline structured; physical backtracking withheld to avoid false precision. |
| **CMEMS Ocean Currents** | `NOT_LOADED` | Copernicus Marine API pipeline structured; physical simulation withheld without validated fields. |

---

## 5. Known Limitations & Research Roadmap

1. **Raster Segmentation:** Live radar backscatter segmentation requires local GPU instances and Copernicus credentials; currently catalogue metadata is verified with illustrative geometry.
2. **Hydrodynamic Drift:** Metocean reanalysis (ERA5/CMEMS) is cached/unloaded; numerical backtracking is withheld in demo mode to maintain strict scientific honesty.
3. **AIS Feed:** In production, AIS will connect directly to DGLL coastal receiver networks; currently using verified incident reconstructions.
