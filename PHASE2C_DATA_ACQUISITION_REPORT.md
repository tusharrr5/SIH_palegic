# PHASE 2C — Data Acquisition & Validation Gate Report

**Project**: PALEGIC SIH 2026  
**Problem Statement ID**: 26143  
**Canonical Incident**: `SIH-ENNORE-2017`  
**Execution Date**: 2026-09-26  

---

## SENTINEL-1
* **Catalogue**: OBSERVED (Copernicus Data Space Ecosystem verified)
* **Raster**: METADATA_ONLY (download script ready; requires CDSE credentials)
* **Selected product**: `S1A_IW_GRDH_1SDV_20170129T003132_20170129T003157_015039_01892E_8B05_COG.SAFE` (Product ID: `1d00379c-fe75-4e44-a90d-d354a59e0104`)
* **Acquisition**: 2017-01-29T00:31:32Z (~16.5 hours post-collision, first daylight overpass)
* **Raw size**: 1.18 GB (online on CDSE)
* **Processed artifact**: Awaiting download for radiometric calibration ($\sigma_0$ in dB) and AOI clipping (`scripts/preprocess_sar.py` implemented)
* **Provenance**: OBSERVED (metadata and footprint verified)
* **Slick provenance**: ILLUSTRATIVE (strictly maintained; no false AI detection claimed)

---

## ERA5
* **Status**: NOT_LOADED
* **Dataset**: `reanalysis-era5-single-levels` (ECMWF Copernicus Climate Data Store)
* **Variables**: `10m_u_component_of_wind` (u10), `10m_v_component_of_wind` (v10)
* **Records**: 0 (fails closed cleanly; zero fictional/constant fallbacks permitted)
* **Time range**: 2017-01-27T00:00:00Z → 2017-01-31T23:00:00Z (hourly)
* **Spatial range**: 12.5°N–14.0°N, 79.5°E–81.0°E (0.25° grid)
* **Min/max wind speed**: N/A (NOT_LOADED)
* **Provenance**: REANALYSIS

---

## CMEMS
* **Status**: NOT_LOADED
* **Product**: `GLOBAL_MULTIYEAR_PHY_001_030` (GLORYS12V1 Global Ocean Physics Reanalysis)
* **Dataset**: `cmems_mod_glo_phy_my_0.083deg_P1D-m`
* **Variables**: `uo` (eastward current), `vo` (northward current)
* **Depth**: 0.0 m to 1.0 m (near-surface model level, shallowest at 0.49 m)
* **Records**: 0 (fails closed cleanly; zero fictional/constant fallbacks permitted)
* **Time range**: 2017-01-27T00:00:00Z → 2017-01-31T00:00:00Z (daily mean)
* **Spatial range**: 12.5°N–14.0°N, 79.5°E–81.0°E (0.083° grid)
* **Min/max current speed**: N/A (NOT_LOADED)
* **Provenance**: REANALYSIS

---

## AIS
* **Status**: TRAINING (Inquiry-reconstructed tracks for BW MAPLE IMO 9346537 and DAWN KANCHIPURAM IMO 9368730)
* **Provenance**: TRAINING / SYNTHETIC (`is_synthetic: true`; strictly protected against promotion to OBSERVED; external retrieval protocols documented in `ais/HISTORICAL_AIS_RETRIEVAL.md`)

---

## TESTS
* **Passed**: 88
* **Failed**: 0
* **Breakdown**:
  * `tests/test_phase2b_validation.py`: 60 passed
  * `tests/test_phase2c_validation.py`: 28 passed

---

## PREFLIGHT
* **CDSE**: CREDENTIALS_MISSING
* **ERA5**: CREDENTIALS_MISSING
* **CMEMS**: CREDENTIALS_MISSING

---

## BLOCKERS

1. **CDS API Key**:
   * Required to download `reanalysis-era5-single-levels`.
   * Action: Register at `https://cds.climate.copernicus.eu/`, accept dataset terms, and place credentials in `~/.cdsapirc`.
   * Command: `python scripts/fetch_era5_wind.py`

2. **Copernicus Marine Credentials**:
   * Required to download `cmems_mod_glo_phy_my_0.083deg_P1D-m`.
   * Action: Register at `https://data.marine.copernicus.eu/register` and run `copernicusmarine login`.
   * Command: `python scripts/fetch_cmems_currents.py`

3. **Copernicus Data Space Ecosystem (CDSE) Credentials**:
   * Required to download `1d00379c-fe75-4e44-a90d-d354a59e0104` (1.18 GB).
   * Action: Register at `https://dataspace.copernicus.eu/` and export `CDSE_USERNAME` and `CDSE_PASSWORD`.
   * Command: `python scripts/fetch_sentinel1_ennore.py`

---

## PHASE 3 READINESS:

**NOT READY**

**Readiness Criteria Assessment**:
- Canonical case reproducible: **READY** (PostgreSQL/PostGIS initialized and seeded; Next.js frontend and FastAPI backend running)
- Provenance tests pass: **READY** (88/88 automated validation tests passing)
- ERA5 is genuinely LOADED: **NOT READY** (Preserved as `NOT_LOADED` awaiting CDS API key)
- CMEMS is genuinely LOADED: **NOT READY** (Preserved as `NOT_LOADED` awaiting CMEMS credentials)
- No fake environmental fallbacks exist: **READY** (Strictly fails closed with 0 records when uncredentialled)

*Phase 3 must remain gated until credentials are provided and genuine reanalysis data is downloaded.*
