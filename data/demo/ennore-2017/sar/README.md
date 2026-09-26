# SAR Data — Ennore 2017

## Status: METADATA ONLY

The Sentinel-1A SAR scene for the 29 January 2017 Ennore acquisition
is **not yet downloaded**. This directory contains only the metadata
contract (`scene_metadata.json`) that describes what the application
expects when the scene is acquired.

## How to acquire the actual scene

**IMPORTANT:** The ESA SciHub / Open Access Hub has been retired.
Use the **Copernicus Data Space Ecosystem (CDSE)** instead.

### Automated search (recommended)

```sh
python scripts/search_sentinel1_ennore.py
```

This searches the CDSE catalogue for Sentinel-1 GRD scenes covering
the Ennore / Kamarajar Port area around 28 January 2017. Results are
saved to `sar/sentinel1_search_results.json`.

### Automated download

```sh
# Set CDSE credentials
export CDSE_USERNAME='your-email@example.com'
export CDSE_PASSWORD='your-password'

python scripts/fetch_sentinel1_ennore.py
```

### Manual search

1. Register at https://dataspace.copernicus.eu/
2. Open the CDSE browser: https://browser.dataspace.copernicus.eu/
3. Search for Sentinel-1 GRD scenes:
   - Area: 13.28°N 80.33°E (Ennore coast)
   - Date: 2017-01-23 to 2017-02-02
   - Collection: Sentinel-1
   - Product type: GRD
4. Download the SAFE product
5. Extract VV sigma-naught as `vv_sigma0.tif` in this directory
6. Update `is_raster_loaded` to `true` in `scene_metadata.json`

## Detection method disclosure

The oil-slick polygon in `../spill/observed_slick.geojson` was
digitised from published incident reports. It is labelled:

```
detection_method: "historical_validation_mask"
provenance_class: "ILLUSTRATIVE"
```

**It is NOT the output of an AI/ML oil detection pipeline.**
The application will update this label if an actual ML model is applied.

Downloading a SAR raster does NOT constitute oil slick detection.
The detection process must produce the result independently.

## Layer support

When `is_raster_loaded: true`, the OceanMap component will display
the SAR image as a raster tile source beneath the slick polygon.
The layer control will expose: **SAR IMAGE | DETECTED SLICK | AIS TRACKS**
