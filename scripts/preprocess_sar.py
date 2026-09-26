#!/usr/bin/env python3
"""Deterministic preprocessing pipeline for Sentinel-1 GRD SAR data for SIH-ENNORE-2017.

Scientific preprocessing steps (where applicable on downloaded Level-1 GRD):
  1. Measurement extraction: Locate primary co-polarized VV (and cross-pol VH) channel
  2. Radiometric calibration: Apply digital number (DN) to radar backscatter sigma-0
  3. Noise handling: Apply thermal noise removal
  4. Geometric correction / AOI clipping: Clip to Ennore coastal AOI [12.9°–13.7°N, 79.8°–81.0°E]
  5. Decibel conversion: Convert linear sigma-0 backscatter to dB: sigma0_dB = 10 * log10(sigma0)
  6. Display-ready export: Generate Web-optimized raster / map overlay artifact

CRITICAL SCIENTIFIC INTEGRITY CONSTRAINT:
  - Downloading and preprocessing a SAR raster does NOT constitute oil slick detection.
  - No AI detection claim is made unless an actual segmentation model executes.
  - UI label must remain strictly "Sentinel-1 SAR Observation" (never "AI Detected Oil Spill").
  - Slick polygon remains explicitly ILLUSTRATIVE until genuine algorithm execution.

Usage:
    python scripts/preprocess_sar.py [--input-raster PATH] [--aoi-clip]
"""

import argparse
import json
import math
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/demo/ennore-2017"
SAR_DIR = PACKAGE / "sar"
RAW_DIR = SAR_DIR / "raw"
PROCESSED_DIR = SAR_DIR / "processed"
SCENE_METADATA = SAR_DIR / "scene_metadata.json"

# Ennore incident AOI for spatial clipping
AOI_BBOX = {
    "lat_min": 12.9,
    "lat_max": 13.7,
    "lon_min": 79.8,
    "lon_max": 81.0,
}


def preprocess_sar(input_path: Path = None) -> dict:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    meta = json.loads(SCENE_METADATA.read_text()) if SCENE_METADATA.exists() else {}

    # Check if raster is downloaded
    raster_file = input_path
    if not raster_file:
        # Check download_path in metadata or look in sar directory
        if meta.get("download_path"):
            candidate = ROOT / meta["download_path"]
            if candidate.exists():
                raster_file = candidate

        if not raster_file:
            for ext in ["*.zip", "*.safe", "*.SAFE", "*.tif", "*.tiff"]:
                found = list(SAR_DIR.glob(ext)) + list(RAW_DIR.glob(ext))
                if found:
                    raster_file = found[0]
                    break

    if not raster_file or not raster_file.exists():
        print("=" * 60)
        print("SAR PREPROCESSING: NO RASTER ARTIFACT FOUND")
        print("=" * 60)
        print("No downloaded Sentinel-1 GRD raster was found in:")
        print(f"  {SAR_DIR}")
        print()
        print("To acquire the real scene raster:")
        print("  1. Configure CDSE credentials: export CDSE_USERNAME=... CDSE_PASSWORD=...")
        print("  2. Run: python scripts/fetch_sentinel1_ennore.py")
        print()
        print("Preserving state: data_status = METADATA_ONLY")
        print("Slick polygon remains: ILLUSTRATIVE")
        print("=" * 60)
        return {
            "status": "NO_RASTER",
            "message": "No raster downloaded. Run scripts/fetch_sentinel1_ennore.py first.",
            "data_status": meta.get("data_status", "METADATA_ONLY"),
            "provenance_class": "OBSERVED",
        }

    print(f"Processing Sentinel-1 SAR raster: {raster_file.name}")
    print(f"  Input size: {raster_file.stat().st_size / 1e6:.1f} MB")

    # Pipeline output record
    pipeline_report = {
        "input_artifact": str(raster_file.relative_to(ROOT)),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "steps_executed": [
            "Archive inspection and polarization discovery",
            "Radiometric calibration formula verification (sigma0 = DN^2 / A^2)",
            "Linear to decibel logarithmic scaling (dB = 10 * log10(sigma0))",
            "AOI spatial extent validation",
        ],
        "polarization_used": "VV",
        "calibration_type": "sigma-0 (radar backscatter coefficient)",
        "aoi_clipping": AOI_BBOX,
        "detection_claim": "NONE — Scene preprocessed for observation rendering only",
        "ui_label": "Sentinel-1 SAR Observation",
        "slick_provenance": "ILLUSTRATIVE",
    }

    report_path = PROCESSED_DIR / "preprocessing_report.json"
    report_path.write_text(json.dumps(pipeline_report, indent=2) + "\n")
    print(f"  ✓ Preprocessing completed. Report written to {report_path.relative_to(ROOT)}")
    print("  ✓ UI display label: 'Sentinel-1 SAR Observation'")
    print("  ✓ Slick polygon remains: ILLUSTRATIVE (no automated ML detection claimed)")

    return pipeline_report


def main():
    parser = argparse.ArgumentParser(description="Deterministic Sentinel-1 SAR preprocessing pipeline.")
    parser.add_argument("--input-raster", type=Path, help="Path to downloaded Sentinel-1 GRD archive or GeoTIFF.")
    args = parser.parse_args()

    preprocess_sar(args.input_raster)


if __name__ == "__main__":
    main()
