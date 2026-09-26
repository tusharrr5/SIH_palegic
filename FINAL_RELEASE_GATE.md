# PALEGIC SIH 2026 — Final Release-Credibility Gate Report

**Date:** 2026-09-26  
**Problem Statement ID:** 26143  
**Product:** PALEGIC — Explainable Oil Spill Investigation & Vessel Attribution  
**Team:** Ekatva  

---

## 1. Files Changed
- [main.py](file:///Users/tusharbhojwani/Downloads/Maritime-main/api/pelagic/main.py): Updated AIS-FIRST ranking payload and timeline events to use honest scientific terminology ("Suspected Surface Anomaly Identified", "Space-Time Correlation Evaluated", "Evidence Score: 76/100", and explicit non-probabilistic decision-support wording).
- [EvidencePanel.tsx](file:///Users/tusharbhojwani/Downloads/Maritime-main/apps/web/components/EvidencePanel.tsx): Corrected Step 5 ("Suspected Surface Anomaly Evidence"), Step 6 ("Space-Time Correlation Evaluated"), and Step 8 candidate assessment card to display **Evidence Score: 76 / 100** with the explanatory note: *"Decision-support score derived from available evidence; not a probability of culpability."*
- [ReportModal.tsx](file:///Users/tusharbhojwani/Downloads/Maritime-main/apps/web/components/ReportModal.tsx): Updated AIS-FIRST report sections 5 & 7 to remove claims of confirmed spills and present the score as Evidence Score: 76 / 100 with the required disclaimer.
- [smoke_test_ais_first.mjs](file:///Users/tusharbhojwani/Downloads/Maritime-main/apps/web/scripts/smoke_test_ais_first.mjs): Added E2E assertions validating the Evidence Score presentation and disclaimer note.
- [audit_browser_journeys.mjs](file:///Users/tusharbhojwani/Downloads/Maritime-main/apps/web/scripts/audit_browser_journeys.mjs): Automated dual-journey Playwright script capturing browser console logs and errors across Journey A (AIS-FIRST) and Journey B (SAR-FIRST).
- [SIH_DEPLOYMENT_PLAN.md](file:///Users/tusharbhojwani/Downloads/Maritime-main/SIH_DEPLOYMENT_PLAN.md): Complete, production-grade deployment specification detailing recommended architecture, CORS, environment variable names, idempotent database seeds, and rollback plans.

---

## 2. Scientific Wording Corrected
- **Eliminated False Confirmation Claims**: Replaced all instances of *"Surface anomaly confirmed"* or *"Confirmed oil spill"* with honest scientific descriptors:
  - *"Suspected surface anomaly identified"*
  - *"Suspected Surface Anomaly (Historical Composite)"*
- **Replay Timeline Sequence**:
  - `08:00 UTC`: SAR Observation Reviewed
  - `08:15 UTC`: Suspected Surface Anomaly Identified
  - `08:20 UTC`: Space-Time Correlation Evaluated
  - `08:30 UTC`: Candidate Assessment Generated
- **Transparent Framing**: Explicitly stated that satellite data for the Gulf of Mexico training case is a historical composite polygon rather than an AI-detected live spill.

---

## 3. Old vs. New Attribution Wording
| Field | Previous Phrasing | Corrected Scientific Phrasing |
|---|---|---|
| **Score Label** | Candidate Attribution Score: 76% | **Evidence Score: 76 / 100** |
| **Probability Disclaimer** | None / Generic disclaimer | *"Decision-support score derived from available evidence; not a probability of culpability."* |
| **Candidate Role** | HIGH-PRIORITY CANDIDATE | **HIGH-PRIORITY CANDIDATE** (Decision-support ranking requiring certified analyst review) |
| **Spatial Coincidence** | Trajectory intersects footprint of detected surface slick | Trajectory intersects spatial footprint of **suspected surface anomaly** |

---

## 4. Provenance Verification
Every demo dataset retains its explicit, honest classification across UI, database, and generated reports:
- **AIS-FIRST Training Vessel A**: `SYNTHETIC AIS · TRAINING DATA`
- **Gulf of Mexico Surface Evidence**: `HISTORICAL / ILLUSTRATIVE SURFACE ANOMALY COMPOSITE`
- **AIS-FIRST Metocean Data**: `NOT_LOADED` (backtracking transport simulation is withheld to avoid false precision)
- **Ennore Sentinel-1 Catalogue Metadata**: `OBSERVED` (Copernicus Data Space Ecosystem verified metadata)
- **Ennore Slick Geometry**: `ILLUSTRATIVE` (Historical incident validation geometry)
- **Ennore Reconstructed AIS**: `TRAINING / SYNTHETIC` (`BW Maple` & `Dawn Kancheepuram` tracks)

---

## 5. AIS-FIRST Result
- **Workflow Integrity**: Begins with maritime surveillance at 06:00 UTC; **no oil slick visible on the map**.
- **Anomaly Progression**: Deceleration at 06:42 UTC $\rightarrow$ loitering loop at 06:48 UTC $\rightarrow$ anomaly threshold crossed at 07:00 UTC (`⚠ AIS ANOMALY` marker pinned).
- **Targeted SAR Verification**: 25 km search area activates at 07:02 UTC.
- **Delayed Surface Anomaly Reveal**: Revealed on map only at 08:15 UTC.
- **Candidate Assessment**: Single investigated vessel focus (`Training Vessel A`), Evidence Score: 76 / 100 with clear explainability bullets.
- **Status**: **PASS**

---

## 6. SAR-FIRST Result
- **Workflow Integrity**: Canonical Ennore 2017 incident ([SIH-ENNORE-2017](file:///Users/tusharbhojwani/Downloads/Maritime-main/data/demo/ennore-2017/manifest.json)).
- **Progression**: Observed SAR slick detected first $\rightarrow$ collision site backtracking $\rightarrow$ multi-candidate search $\rightarrow$ candidate comparative ranking (`BW Maple` vs `Dawn Kancheepuram`).
- **Status**: **PASS**

---

## 7. Pytest Result
```
======================== 131 passed, 1 warning in 5.89s ========================
```
- Total tests: **131**
- Passed: **131**
- Failed: **0**

---

## 8. E2E Results
- **AIS-FIRST E2E Smoke Test (`smoke_test_ais_first.mjs`)**: **PASS** (11/11 assertions pass).
- **SAR-FIRST E2E Smoke Test (`smoke_test_e2e.mjs`)**: **PASS** (17/17 assertions pass).

---

## 9. TypeScript Result
```
> pelagic-web@0.1.0 typecheck
> tsc --noEmit
```
- Status: **PASS** (0 errors).

---

## 10. Production Build Result
```
> pelagic-web@0.1.0 build
> next build

✓ Compiled successfully in 1227ms
✓ Linting and checking validity of types
✓ Collecting page data
✓ Generating static pages (5/5)
✓ Finalizing page optimization
```
- Status: **PASS** (Optimized production build ready).

---

## 11. Browser Console Result
- Evaluated during automated execution of Journey A (AIS-FIRST) and Journey B (SAR-FIRST) in [audit_browser_journeys.mjs](file:///Users/tusharbhojwani/Downloads/Maritime-main/apps/web/scripts/audit_browser_journeys.mjs).
- **Console Errors Caught**: `0` (Zero browser console errors detected).
- **Console Warnings Caught**: `0`.

---

## 12. Deployment Readiness
- Unified containerization stack verified in [compose.yaml](file:///Users/tusharbhojwani/Downloads/Maritime-main/compose.yaml) (PostGIS, FastAPI, Next.js 15, and Nginx reverse proxy).
- Operations runbook documented in [SIH_PRODUCTION_RUNBOOK.md](file:///Users/tusharbhojwani/Downloads/Maritime-main/SIH_PRODUCTION_RUNBOOK.md).
- Component-level verification documented in [DEPLOYMENT_VALIDATION.md](file:///Users/tusharbhojwani/Downloads/Maritime-main/DEPLOYMENT_VALIDATION.md).
- Frontend same-origin proxy eliminates cross-origin cookie and CORS issues.
- Database bootstrap and seeding scripts are completely idempotent (`scripts/bootstrap.py` and `scripts/seed_ennore.py`).

---

## 13. Remaining Blockers
- None.

---

RELEASE GATE: PASS — READY FOR PUBLIC HOST DEPLOYMENT
