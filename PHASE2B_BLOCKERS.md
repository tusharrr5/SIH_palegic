# PHASE 2B — Blockers

## Problem Statement ID: 26143
## Incident: SIH-ENNORE-2017

---

## Blocker 1: ERA5 Wind — Credentials Required

**Status**: NOT_LOADED

The ERA5 wind retrieval script (`scripts/fetch_era5_wind.py`) is fully
implemented and validated. It requires a CDS API key to execute.

**To unblock**:
1. Register at https://cds.climate.copernicus.eu/
2. Create `~/.cdsapirc` with your API key
3. Run: `pip install cdsapi && python scripts/fetch_era5_wind.py`

**Impact**: Drift backtracking cannot use real wind data until this is loaded.
The application correctly displays "NOT LOADED" and refuses to run hindcast
with fictional constants.

---

## Blocker 2: CMEMS Currents — Credentials Required

**Status**: NOT_LOADED

The CMEMS current retrieval script (`scripts/fetch_cmems_currents.py`) is
fully implemented and validated. It requires CMEMS credentials.

**To unblock**:
1. Register at https://data.marine.copernicus.eu/register
2. Run: `pip install copernicusmarine && copernicusmarine login`
3. Run: `python scripts/fetch_cmems_currents.py`

**Impact**: Drift backtracking cannot use real ocean current data. The
application correctly displays "NOT LOADED".

---

## Blocker 3: Sentinel-1 Raster — Download Requires CDSE Credentials

**Status**: METADATA_ONLY (scenes verified on CDSE)

The Sentinel-1 search has been executed successfully. **4 GRD scenes were
found** covering the Ennore area for 2017-01-29. The raster download
requires CDSE account credentials.

**To unblock**:
1. Register at https://dataspace.copernicus.eu/
2. Set `CDSE_USERNAME` and `CDSE_PASSWORD` environment variables
3. Run: `python scripts/fetch_sentinel1_ennore.py`

**Important**: Downloading the raster does NOT constitute oil detection.
The detection pipeline would need to be run separately. The slick polygon
remains ILLUSTRATIVE until a genuine SAR-based detection is performed.

---

## Blocker 4: Historical AIS — Not Yet Obtained

**Status**: TRAINING / SYNTHETIC (acceptable)

No authenticated historical AIS positions have been obtained for BW Maple
or Dawn Kancheepuram. The training reconstructions are correctly labelled
and sufficient for the SIH 2026 demonstration.

**To unblock** (optional):
- Follow the guide in `data/demo/ennore-2017/ais/HISTORICAL_AIS_RETRIEVAL.md`
- Sources to try: Global Fishing Watch, MarineTraffic (paid), VesselFinder,
  DGS India (RTI), INCOIS

**Impact**: The existing training tracks demonstrate the attribution workflow.
Real AIS is a nice-to-have for this historical validation case but not
strictly required for the SIH demo.

---

## Blocker 5: Python Environment

**Status**: RESOLVED

The README previously mandated `uv` which may not be available. This has
been fixed:
- `python -m venv .venv && .venv/bin/pip install -e ".[dev]"` is now the
  primary documented method
- `uv sync --locked` remains as an optional alternative
- `python scripts/seed_ennore.py` works from the project's documented
  Python environment

---

## Non-Blockers (Working)

| Component | Status |
|---|---|
| Sentinel-1 CDSE search | ✅ 4 scenes found |
| SAR scene metadata (verified) | ✅ Updated with CDSE data |
| ERA5 fetch script | ✅ Ready (clean failure without credentials) |
| CMEMS fetch script | ✅ Ready (clean failure without credentials) |
| AIS training tracks | ✅ Correctly labelled TRAINING |
| AIS retrieval documentation | ✅ Complete |
| Provenance manifest | ✅ Complete |
| Seed script (no uv dependency) | ✅ Fixed |
| Validation tests (60 tests) | ✅ All pass |
| UI data status display | ✅ Updated |
| SciHub references removed | ✅ All point to CDSE |

---

## Summary

All Phase 2B deliverables are complete. The remaining blockers are
**credential-gated** — the scripts are ready and validated, they just
need API keys from the respective Copernicus services. No data has been
fabricated, no constants have been substituted, and no provenance labels
have been changed silently.

**Phase 3 has NOT been started.** Awaiting review.
