#!/usr/bin/env python3
"""Retrieve CMEMS Global Ocean Physics Reanalysis surface currents
for the Ennore 2017 incident.

Product: GLOBAL_MULTIYEAR_PHY_001_030
Dataset: cmems_mod_glo_phy_my_0.083deg_P1D-m

Usage:
    python scripts/fetch_cmems_currents.py [--incident SIH-ENNORE-2017]

Requires:
    pip install copernicusmarine

Credentials:
    CMEMS credentials must be configured via:
    - copernicusmarine login (interactive)
    - Environment variables: COPERNICUSMARINE_SERVICE_USERNAME, COPERNICUSMARINE_SERVICE_PASSWORD

    Register at: https://data.marine.copernicus.eu/register

If credentials are unavailable, the script fails clearly with:
    data_status = NOT_LOADED

Current data is NOT hardcoded. If the download fails, the incident
package retains data_status = NOT_LOADED.
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/demo/ennore-2017"
CURRENTS_FILE = PACKAGE / "metocean/currents.json"
PROVENANCE_FILE = PACKAGE / "metocean/provenance.json"

# Incident parameters
INCIDENT_TIME = datetime(2017, 1, 28, 8, 0, 0, tzinfo=timezone.utc)
INCIDENT_LAT = 13.28
INCIDENT_LON = 80.33

# Retrieval parameters — geographically restricted bounding box
BBOX = {
    "lat_min": 12.5,
    "lat_max": 14.0,
    "lon_min": 79.5,
    "lon_max": 81.0,
}

# Temporal window — sufficient for hindcasting
TIME_START = datetime(2017, 1, 27, 0, 0, 0, tzinfo=timezone.utc)
TIME_END = datetime(2017, 1, 31, 0, 0, 0, tzinfo=timezone.utc)

# Near-surface depth
DEPTH_MIN = 0.0
DEPTH_MAX = 1.0  # metres — near-surface only

# CMEMS product/dataset identifiers
PRODUCT_ID = "GLOBAL_MULTIYEAR_PHY_001_030"
DATASET_ID = "cmems_mod_glo_phy_my_0.083deg_P1D-m"


def fetch_cmems_currents() -> dict:
    """Download CMEMS surface current reanalysis and store in incident package."""

    # ── Check copernicusmarine availability ─────────────────────────────
    try:
        import copernicusmarine
    except ImportError:
        print("=" * 60)
        print("ERROR: copernicusmarine package not installed.")
        print()
        print("Install with:")
        print("  pip install copernicusmarine")
        print()
        print("data_status = NOT_LOADED")
        print("=" * 60)
        _write_not_loaded("copernicusmarine package not installed. Run: pip install copernicusmarine")
        return {"data_status": "NOT_LOADED"}

    # ── Check credentials ───────────────────────────────────────────────
    has_env = (
        os.environ.get("COPERNICUSMARINE_SERVICE_USERNAME")
        and os.environ.get("COPERNICUSMARINE_SERVICE_PASSWORD")
    )
    # copernicusmarine stores credentials in ~/.copernicusmarine/.copernicusmarine-credentials
    cred_file = Path.home() / ".copernicusmarine" / ".copernicusmarine-credentials"
    if not has_env and not cred_file.exists():
        print("=" * 60)
        print("ERROR: CMEMS credentials not found.")
        print()
        print("Option 1: Run interactive login:")
        print("  copernicusmarine login")
        print()
        print("Option 2: Set environment variables:")
        print("  export COPERNICUSMARINE_SERVICE_USERNAME='your-username'")
        print("  export COPERNICUSMARINE_SERVICE_PASSWORD='your-password'")
        print()
        print("Register at: https://data.marine.copernicus.eu/register")
        print("=" * 60)
        print()
        print("data_status = NOT_LOADED")
        _write_not_loaded("CMEMS credentials not found. See copernicusmarine login or env vars.")
        return {"data_status": "NOT_LOADED"}

    output_nc = PACKAGE / "metocean/raw/cmems_currents.nc"
    output_nc.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching CMEMS surface current reanalysis…")
    print(f"  Product     : {PRODUCT_ID}")
    print(f"  Dataset     : {DATASET_ID}")
    print(f"  Variables   : uo, vo")
    print(f"  Time window : {TIME_START.isoformat()} → {TIME_END.isoformat()}")
    print(f"  Bounding box: {BBOX}")
    print(f"  Depth       : {DEPTH_MIN}–{DEPTH_MAX} m (near-surface)")
    print(f"  Output      : {output_nc.relative_to(ROOT)}")
    print()

    try:
        copernicusmarine.subset(
            dataset_id=DATASET_ID,
            variables=["uo", "vo"],
            minimum_longitude=BBOX["lon_min"],
            maximum_longitude=BBOX["lon_max"],
            minimum_latitude=BBOX["lat_min"],
            maximum_latitude=BBOX["lat_max"],
            start_datetime=TIME_START.strftime("%Y-%m-%dT%H:%M:%S"),
            end_datetime=TIME_END.strftime("%Y-%m-%dT%H:%M:%S"),
            minimum_depth=DEPTH_MIN,
            maximum_depth=DEPTH_MAX,
            output_filename=str(output_nc.name),
            output_directory=str(output_nc.parent),
            overwrite_output_data=True,
            force_download=True,
        )
    except Exception as exc:
        print(f"  ✗ CMEMS retrieval failed: {exc}")
        print()
        print("data_status = NOT_LOADED")
        _write_not_loaded(f"CMEMS retrieval failed: {exc}")
        return {"data_status": "NOT_LOADED"}

    if not output_nc.exists():
        print("  ✗ Output file not created.")
        print("data_status = NOT_LOADED")
        _write_not_loaded("Output NetCDF file was not created by copernicusmarine.")
        return {"data_status": "NOT_LOADED"}

    # ── Parse NetCDF and extract samples ────────────────────────────────
    print("  ✓ Download complete. Parsing NetCDF…")
    return _parse_netcdf(output_nc)


def _parse_netcdf(nc_path: Path) -> dict:
    """Parse CMEMS NetCDF and write structured JSON to the incident package."""
    try:
        import numpy as np
    except ImportError:
        print("  ✗ numpy not available for parsing.")
        _write_not_loaded("numpy not available for NetCDF parsing")
        return {"data_status": "NOT_LOADED"}

    try:
        try:
            from netCDF4 import Dataset as NCDataset
            ds = NCDataset(str(nc_path), "r")
            use_netcdf4 = True
        except ImportError:
            from scipy.io import netcdf_file
            ds = netcdf_file(str(nc_path), "r", mmap=False)
            use_netcdf4 = False

        # Extract dimensions
        if use_netcdf4:
            import cftime
            time_var = ds.variables["time"]
            time_units = time_var.units
            time_calendar = getattr(time_var, "calendar", "standard")
            times_raw = time_var[:]
            times = cftime.num2date(times_raw, time_units, time_calendar)
            times = [datetime(t.year, t.month, t.day, t.hour, t.minute, t.second,
                             tzinfo=timezone.utc) for t in times]
            lats = ds.variables["latitude"][:].tolist()
            lons = ds.variables["longitude"][:].tolist()
            depths = ds.variables["depth"][:].tolist() if "depth" in ds.variables else [0.0]
            uo = ds.variables["uo"][:]
            vo = ds.variables["vo"][:]
        else:
            time_var = ds.variables["time"]
            times_raw = time_var.data.copy()
            lats = ds.variables["latitude"].data.copy().tolist()
            lons = ds.variables["longitude"].data.copy().tolist()
            depths = ds.variables["depth"].data.copy().tolist() if "depth" in ds.variables else [0.0]
            uo = ds.variables["uo"].data.copy()
            vo = ds.variables["vo"].data.copy()
            # CMEMS time: hours since 1950-01-01
            epoch = datetime(1950, 1, 1, tzinfo=timezone.utc)
            times = [epoch + timedelta(hours=float(h)) for h in times_raw]

        ds.close()

    except Exception as exc:
        print(f"  ✗ NetCDF parsing failed: {exc}")
        _write_not_loaded(f"NetCDF parsing failed: {exc}")
        return {"data_status": "NOT_LOADED"}

    # ── Build samples ───────────────────────────────────────────────────
    samples = []
    nan_count = 0
    has_depth_dim = len(uo.shape) == 4
    now_iso = datetime.now(timezone.utc).isoformat()

    for ti, t in enumerate(times):
        for di, depth in enumerate(depths):
            for li, lat in enumerate(lats):
                for lo, lon in enumerate(lons):
                    if has_depth_dim:
                        u_val = float(uo[ti, di, li, lo])
                        v_val = float(vo[ti, di, li, lo])
                    else:
                        u_val = float(uo[ti, li, lo])
                        v_val = float(vo[ti, li, lo])

                    if math.isnan(u_val) or math.isnan(v_val):
                        nan_count += 1
                        continue

                    speed = math.sqrt(u_val ** 2 + v_val ** 2)
                    direction = (math.degrees(math.atan2(-u_val, -v_val)) + 360) % 360

                    samples.append({
                        "timestamp": t.isoformat(),
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "depth_m": float(depth),
                        "uo": round(u_val, 6),
                        "vo": round(v_val, 6),
                        "u_current_mps": round(u_val, 6),
                        "v_current_mps": round(v_val, 6),
                        "current_speed": round(speed, 6),
                        "current_speed_mps": round(speed, 6),
                        "current_direction": round(direction, 2),
                        "current_direction_deg": round(direction, 2),
                        "units": "m/s",
                        "source": "Copernicus Marine Service (CMEMS)",
                        "dataset": DATASET_ID,
                        "retrieval_time": now_iso,
                        "provenance_class": "REANALYSIS",
                        "data_status": "LOADED",
                    })

    # ── Validation ──────────────────────────────────────────────────────
    validation = _validate_currents(samples, times, lats, lons, depths, nan_count)

    # ── Write to incident package ───────────────────────────────────────
    currents_data = json.loads(CURRENTS_FILE.read_text())
    currents_data["data_status"] = "LOADED"
    currents_data["status_message"] = (
        f"CMEMS surface current reanalysis downloaded and parsed. "
        f"{len(samples)} samples, {nan_count} NaN values excluded."
    )
    currents_data["samples"] = samples
    currents_data["retrieval_metadata"] = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_file": "cmems_currents.nc",
        "product_id": PRODUCT_ID,
        "dataset_id": DATASET_ID,
        "time_range": [times[0].isoformat(), times[-1].isoformat()],
        "grid_points": len(lats) * len(lons),
        "timesteps": len(times),
        "depth_levels": depths,
        "total_samples": len(samples),
        "nan_count": nan_count,
        "latitudes_range": [min(lats), max(lats)] if lats else [],
        "longitudes_range": [min(lons), max(lons)] if lons else [],
    }
    currents_data["validation"] = validation

    CURRENTS_FILE.write_text(json.dumps(currents_data, indent=2, ensure_ascii=False) + "\n")

    # Update provenance
    _update_provenance("currents", "LOADED")

    print(f"  ✓ {len(samples)} samples written to {CURRENTS_FILE.relative_to(ROOT)}")
    print(f"    Time range  : {times[0].isoformat()} → {times[-1].isoformat()}")
    print(f"    Grid points : {len(lats)} × {len(lons)}")
    print(f"    Depth levels: {depths}")
    print(f"    NaN count   : {nan_count}")
    print(f"    Provenance  : REANALYSIS")
    print()
    print("data_status = LOADED")

    return {
        "data_status": "LOADED",
        "samples_count": len(samples),
        "nan_count": nan_count,
        "time_range": [times[0].isoformat(), times[-1].isoformat()],
    }


def _validate_currents(samples, times, lats, lons, depths, nan_count) -> dict:
    """Run data quality checks on retrieved current data."""
    checks = {}

    # Timestamps parseable
    try:
        for s in samples[:10]:
            datetime.fromisoformat(s["timestamp"])
        checks["timestamps_valid"] = True
    except Exception:
        checks["timestamps_valid"] = False

    # Coordinate bounds
    lat_ok = all(BBOX["lat_min"] <= s["latitude"] <= BBOX["lat_max"] for s in samples)
    lon_ok = all(BBOX["lon_min"] <= s["longitude"] <= BBOX["lon_max"] for s in samples)
    checks["coordinates_within_bounds"] = lat_ok and lon_ok

    # NaN check
    checks["nan_count"] = nan_count
    checks["no_nan_in_samples"] = nan_count == 0

    # Current magnitude validation (uo/vo → speed)
    magnitude_ok = True
    for s in samples[:100]:
        expected = math.sqrt(s["uo"] ** 2 + s["vo"] ** 2)
        if abs(s["current_speed"] - expected) > 0.0001:
            magnitude_ok = False
            break
    checks["current_magnitude_correct"] = magnitude_ok

    # Incident time overlap
    if times:
        incident_covered = times[0] <= INCIDENT_TIME <= times[-1]
        checks["incident_time_covered"] = incident_covered
    else:
        checks["incident_time_covered"] = False

    # Near-surface depth
    if depths:
        checks["near_surface_depth"] = min(depths) <= 1.0
    else:
        checks["near_surface_depth"] = False

    # Spatial coverage of incident
    if lats and lons:
        checks["incident_within_spatial_extent"] = (
            min(lats) <= INCIDENT_LAT <= max(lats)
            and min(lons) <= INCIDENT_LON <= max(lons)
        )
    else:
        checks["incident_within_spatial_extent"] = False

    return checks


def _write_not_loaded(reason: str):
    """Update currents.json to clearly indicate NOT_LOADED status."""
    currents_data = json.loads(CURRENTS_FILE.read_text())
    currents_data["data_status"] = "NOT_LOADED"
    currents_data["status_message"] = f"Historical environmental forcing not loaded — {reason}"
    currents_data["samples"] = []
    CURRENTS_FILE.write_text(json.dumps(currents_data, indent=2, ensure_ascii=False) + "\n")


def _update_provenance(field: str, status: str):
    """Update the metocean provenance file."""
    prov = json.loads(PROVENANCE_FILE.read_text())
    prov[field]["status"] = status
    PROVENANCE_FILE.write_text(json.dumps(prov, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch CMEMS surface current reanalysis for the Ennore 2017 incident."
    )
    parser.add_argument(
        "--incident",
        type=str,
        default="SIH-ENNORE-2017",
        help="Incident ID (default: SIH-ENNORE-2017)",
    )
    args = parser.parse_args()

    if args.incident != "SIH-ENNORE-2017":
        print(f"Only SIH-ENNORE-2017 is currently supported. Got: {args.incident}")
        sys.exit(1)

    fetch_cmems_currents()


if __name__ == "__main__":
    main()
