# PHASE 2B — Data Acquisition Report

## Problem Statement ID: 26143
## Incident: SIH-ENNORE-2017

---

## Sentinel-1 SAR

### CDSE Search
- **Platform**: Copernicus Data Space Ecosystem (CDSE)
- **Retired platform avoided**: ESA SciHub / Open Access Hub ✓
- **Script**: `scripts/search_sentinel1_ennore.py`
- **Search window**: 2017-01-23 → 2017-02-02
- **AOI**: 79.8°E–81.0°E, 12.9°N–13.7°N

### Search Results
**4 Sentinel-1A GRD scenes found** covering the incident area:

| Scene | Satellite | Acquisition | Mode | Polarisation | Status |
|---|---|---|---|---|---|
| S1A_IW_GRDH_1SDV_20170129T003107…_COG.SAFE | Sentinel-1A | 2017-01-29T00:31:07Z | IW | VV+VH | Online (1.1 GB) |
| S1A_IW_GRDH_1SDV_20170129T003107…_7843.SAFE | Sentinel-1A | 2017-01-29T00:31:07Z | IW | VV+VH | Online (1.7 GB) |
| S1A_IW_GRDH_1SDV_20170129T003132…_COG.SAFE | Sentinel-1A | 2017-01-29T00:31:32Z | IW | VV+VH | Online (1.2 GB) |
| S1A_IW_GRDH_1SDV_20170129T003132…_6D04.SAFE | Sentinel-1A | 2017-01-29T00:31:32Z | IW | VV+VH | Online (1.7 GB) |

### Verified Footprint
The scenes' footprints cover the Ennore coast:
- Westernmost: ~78.2°E
- Easternmost: ~81.1°E
- Southernmost: ~11.9°N
- Northernmost: ~15.3°N
- **Incident point (13.28°N, 80.33°E) is within all footprints ✓**

### Raster Download
- **Script**: `scripts/fetch_sentinel1_ennore.py`
- **Status**: NOT DOWNLOADED (requires CDSE account credentials)
- **Detection**: No oil detection has been performed (ILLUSTRATIVE polygon retained)

---

## ERA5 Historical Wind

- **Script**: `scripts/fetch_era5_wind.py`
- **Dataset**: ERA5 reanalysis-era5-single-levels
- **Provider**: Copernicus Climate Change Service / ECMWF
- **Variables**: 10m_u_component_of_wind, 10m_v_component_of_wind
- **Temporal resolution**: Hourly
- **Spatial resolution**: 0.25°
- **Time window**: 2017-01-27T00:00:00Z → 2017-01-30T23:00:00Z
- **Bounding box**: 12.5°N–14.0°N, 79.5°E–81.0°E
- **Status**: NOT_LOADED (requires CDS API key in ~/.cdsapirc)
- **Provenance**: REANALYSIS
- **Fallback**: None — refuses to substitute constants

### Output Schema (when loaded)
```json
{
  "timestamp": "ISO 8601",
  "latitude": "float",
  "longitude": "float",
  "u10": "float m/s",
  "v10": "float m/s",
  "wind_speed": "float m/s",
  "wind_direction": "float degrees"
}
```

---

## CMEMS Historical Currents

- **Script**: `scripts/fetch_cmems_currents.py`
- **Product**: GLOBAL_MULTIYEAR_PHY_001_030
- **Dataset**: cmems_mod_glo_phy_my_0.083deg_P1D-m
- **Provider**: Copernicus Marine Service
- **Variables**: uo (eastward velocity), vo (northward velocity)
- **Temporal resolution**: Daily mean
- **Spatial resolution**: 0.083°
- **Time window**: 2017-01-27T00:00:00Z → 2017-01-31T00:00:00Z
- **Depth**: 0–1 m (near-surface)
- **Bounding box**: 12.5°N–14.0°N, 79.5°E–81.0°E
- **Status**: NOT_LOADED (requires CMEMS credentials)
- **Provenance**: REANALYSIS
- **Fallback**: None — refuses to substitute constants

### Output Schema (when loaded)
```json
{
  "timestamp": "ISO 8601",
  "latitude": "float",
  "longitude": "float",
  "depth_m": "float",
  "uo": "float m/s",
  "vo": "float m/s",
  "current_speed": "float m/s",
  "current_direction": "float degrees"
}
```

---

## AIS — Historical Vessel Tracks

### BW Maple (IMO 9346537)
- **Status**: Training AIS reconstruction
- **Provenance**: TRAINING
- **Is synthetic**: true
- **Observed track**: Not obtained

### Dawn Kancheepuram (IMO 9368730)
- **Status**: Training AIS reconstruction
- **Provenance**: TRAINING
- **Is synthetic**: true
- **Observed track**: Not obtained

### Retrieval Documentation
- **Guide**: `data/demo/ennore-2017/ais/HISTORICAL_AIS_RETRIEVAL.md`
- **Sources documented**: Global Fishing Watch, MarineTraffic, VesselFinder, DGS India, INCOIS
- **Search aliases**: BW MAPLE, DAWN KANCHIPURAM, DAWN KANCHEEPURAM

---

## Scripts Created

| Script | Purpose | Status |
|---|---|---|
| `scripts/search_sentinel1_ennore.py` | Search CDSE for Sentinel-1 scenes | ✓ Working |
| `scripts/fetch_sentinel1_ennore.py` | Download Sentinel-1 raster from CDSE | ✓ Ready (needs credentials) |
| `scripts/fetch_era5_wind.py` | Download ERA5 wind reanalysis | ✓ Ready (needs CDS API key) |
| `scripts/fetch_cmems_currents.py` | Download CMEMS surface currents | ✓ Ready (needs CMEMS credentials) |

---

## Data Files Updated

| File | Change |
|---|---|
| `sar/scene_metadata.json` | Updated source from retired SciHub to CDSE; verified scene ID |
| `sar/sentinel1_search_results.json` | **NEW** — CDSE search results with 4 scenes |
| `sar/README.md` | Updated acquisition instructions for CDSE |
| `ais/HISTORICAL_AIS_RETRIEVAL.md` | **NEW** — AIS retrieval documentation |
| `provenance_manifest.json` | **NEW** — Full provenance manifest |
| `manifest.json` | Updated with new files and verified SAR status |
