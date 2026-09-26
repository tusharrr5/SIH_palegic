#!/usr/bin/env python3
"""Retrieve ERA5 10 m wind reanalysis for the Ennore 2017 incident.

Uses the Copernicus Climate Data Store (CDS) API.

Usage:
    python scripts/fetch_era5_wind.py [--incident SIH-ENNORE-2017]

Requires:
    pip install cdsapi

Credentials:
    A CDS API key must be configured in ~/.cdsapirc or via environment
    variables (CDSAPI_URL, CDSAPI_KEY).

    Register at: https://cds.climate.copernicus.eu/

If credentials are unavailable, the script fails clearly with:
    data_status = NOT_LOADED

Wind data is NOT hardcoded. If the download fails, the incident package
retains data_status = NOT_LOADED and the application must refuse to run
drift backtracking.
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
WIND_FILE = PACKAGE / "metocean/wind.json"
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

# Temporal window — sufficient for hindcasting (2017-01-27 through 2017-01-31)
TIME_START = datetime(2017, 1, 27, 0, 0, 0, tzinfo=timezone.utc)
TIME_END = datetime(2017, 1, 31, 23, 0, 0, tzinfo=timezone.utc)


def fetch_era5_wind() -> dict:
    """Download ERA5 10 m wind components and store in incident package."""

    # ── Check CDS API availability ──────────────────────────────────────
    try:
        import cdsapi
    except ImportError:
        print("=" * 60)
        print("ERROR: cdsapi package not installed.")
        print()
        print("Install with:")
        print("  pip install cdsapi")
        print()
        print("data_status = NOT_LOADED")
        print("=" * 60)
        _write_not_loaded("cdsapi package not installed. Run: pip install cdsapi")
        return {"data_status": "NOT_LOADED"}

    # ── Check credentials ───────────────────────────────────────────────
    cdsapirc = Path.home() / ".cdsapirc"
    has_env = os.environ.get("CDSAPI_URL") and os.environ.get("CDSAPI_KEY")
    if not cdsapirc.exists() and not has_env:
        print("=" * 60)
        print("ERROR: CDS API credentials not found.")
        print()
        print("Option 1: Create ~/.cdsapirc with:")
        print("  url: https://cds.climate.copernicus.eu/api")
        print("  key: <YOUR-UID>:<YOUR-API-KEY>")
        print()
        print("Option 2: Set environment variables:")
        print("  export CDSAPI_URL=https://cds.climate.copernicus.eu/api")
        print("  export CDSAPI_KEY=<YOUR-UID>:<YOUR-API-KEY>")
        print()
        print("Register at: https://cds.climate.copernicus.eu/")
        print("=" * 60)
        print()
        print("data_status = NOT_LOADED")
        _write_not_loaded("CDS API credentials not found. See ~/.cdsapirc or CDSAPI_URL/CDSAPI_KEY env vars.")
        return {"data_status": "NOT_LOADED"}

    # ── Build retrieval request ─────────────────────────────────────────
    # Generate all dates and hours in the window
    dates = set()
    hours = set()
    current = TIME_START
    while current <= TIME_END:
        dates.add(current.strftime("%Y-%m-%d"))
        hours.add(current.strftime("%H:%M"))
        current += timedelta(hours=1)

    dates_sorted = sorted(dates)
    hours_sorted = sorted(hours)

    # CDS API area format: [lat_max, lon_min, lat_min, lon_max]
    area = [BBOX["lat_max"], BBOX["lon_min"], BBOX["lat_min"], BBOX["lon_max"]]

    output_nc = PACKAGE / "metocean/raw/era5_wind.nc"
    output_nc.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching ERA5 10 m wind reanalysis from CDS…")
    print(f"  Variables    : 10m_u_component_of_wind, 10m_v_component_of_wind")
    print(f"  Time window  : {TIME_START.isoformat()} → {TIME_END.isoformat()}")
    print(f"  Bounding box : {BBOX}")
    print(f"  Resolution   : 0.25° hourly")
    print(f"  Output       : {output_nc.relative_to(ROOT)}")
    print()

    try:
        c = cdsapi.Client()
        c.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "variable": [
                    "10m_u_component_of_wind",
                    "10m_v_component_of_wind",
                ],
                "year": "2017",
                "month": "01",
                "day": dates_sorted,
                "time": hours_sorted,
                "area": area,
                "format": "netcdf",
            },
            str(output_nc),
        )
    except Exception as exc:
        print(f"  ✗ CDS retrieval failed: {exc}")
        print()
        print("data_status = NOT_LOADED")
        _write_not_loaded(f"CDS retrieval failed: {exc}")
        return {"data_status": "NOT_LOADED"}

    # ── Parse NetCDF and extract samples ────────────────────────────────
    print("  ✓ Download complete. Parsing NetCDF…")
    return _parse_netcdf(output_nc)


def _parse_netcdf(nc_path: Path) -> dict:
    """Parse ERA5 NetCDF and write structured JSON to the incident package."""
    try:
        import numpy as np
    except ImportError:
        print("  ✗ numpy not available for parsing.")
        _write_not_loaded("numpy not available for NetCDF parsing")
        return {"data_status": "NOT_LOADED"}

    try:
        # Try netCDF4 first, fall back to scipy
        try:
            from netCDF4 import Dataset as NCDataset
            ds = NCDataset(str(nc_path), "r")
            use_netcdf4 = True
        except ImportError:
            from scipy.io import netcdf_file
            ds = netcdf_file(str(nc_path), "r", mmap=False)
            use_netcdf4 = False

        # Extract coordinate arrays
        if use_netcdf4:
            import cftime
            time_var = ds.variables["time"]
            time_units = time_var.units
            time_calendar = getattr(time_var, "calendar", "standard")
            times_raw = time_var[:]
            # Convert to datetime
            times = cftime.num2date(times_raw, time_units, time_calendar)
            times = [datetime(t.year, t.month, t.day, t.hour, t.minute, t.second,
                             tzinfo=timezone.utc) for t in times]
            lats = ds.variables["latitude"][:].tolist()
            lons = ds.variables["longitude"][:].tolist()
            u10 = ds.variables["u10"][:]
            v10 = ds.variables["v10"][:]
        else:
            # scipy fallback
            time_var = ds.variables["time"]
            times_raw = time_var.data.copy()
            lats = ds.variables["latitude"].data.copy().tolist()
            lons = ds.variables["longitude"].data.copy().tolist()
            u10 = ds.variables["u10"].data.copy()
            v10 = ds.variables["v10"].data.copy()
            # ERA5 time: hours since 1900-01-01
            epoch = datetime(1900, 1, 1, tzinfo=timezone.utc)
            times = [epoch + timedelta(hours=float(h)) for h in times_raw]

        ds.close()

    except Exception as exc:
        print(f"  ✗ NetCDF parsing failed: {exc}")
        _write_not_loaded(f"NetCDF parsing failed: {exc}")
        return {"data_status": "NOT_LOADED"}

    # ── Build samples ───────────────────────────────────────────────────
    samples = []
    nan_count = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    for ti, t in enumerate(times):
        for li, lat in enumerate(lats):
            for lo, lon in enumerate(lons):
                u_val = float(u10[ti, li, lo])
                v_val = float(v10[ti, li, lo])

                if math.isnan(u_val) or math.isnan(v_val):
                    nan_count += 1
                    continue

                speed = math.sqrt(u_val ** 2 + v_val ** 2)
                direction = (math.degrees(math.atan2(-u_val, -v_val)) + 360) % 360

                samples.append({
                    "timestamp": t.isoformat(),
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "u10": round(u_val, 4),
                    "v10": round(v_val, 4),
                    "u10_mps": round(u_val, 4),
                    "v10_mps": round(v_val, 4),
                    "wind_speed": round(speed, 4),
                    "wind_speed_mps": round(speed, 4),
                    "wind_direction": round(direction, 2),
                    "wind_direction_deg": round(direction, 2),
                    "units": "m/s",
                    "source": "ECMWF Copernicus Climate Data Store (CDS)",
                    "dataset": "reanalysis-era5-single-levels",
                    "retrieval_time": now_iso,
                    "provenance_class": "REANALYSIS",
                    "data_status": "LOADED",
                })

    # ── Validation ──────────────────────────────────────────────────────
    validation = _validate_wind(samples, times, lats, lons, nan_count)

    # ── Write to incident package ───────────────────────────────────────
    wind_data = json.loads(WIND_FILE.read_text())
    wind_data["data_status"] = "LOADED"
    wind_data["status_message"] = (
        f"ERA5 10 m wind reanalysis downloaded and parsed. "
        f"{len(samples)} samples, {nan_count} NaN values excluded."
    )
    wind_data["samples"] = samples
    wind_data["retrieval_metadata"] = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_file": "era5_wind.nc",
        "time_range": [times[0].isoformat(), times[-1].isoformat()],
        "grid_points": len(lats) * len(lons),
        "timesteps": len(times),
        "total_samples": len(samples),
        "nan_count": nan_count,
        "latitudes": lats if isinstance(lats[0], float) else [float(x) for x in lats],
        "longitudes": lons if isinstance(lons[0], float) else [float(x) for x in lons],
    }
    wind_data["validation"] = validation

    WIND_FILE.write_text(json.dumps(wind_data, indent=2, ensure_ascii=False) + "\n")

    # Update provenance
    _update_provenance("wind", "LOADED")

    print(f"  ✓ {len(samples)} samples written to {WIND_FILE.relative_to(ROOT)}")
    print(f"    Time range : {times[0].isoformat()} → {times[-1].isoformat()}")
    print(f"    Grid points: {len(lats)} × {len(lons)} = {len(lats) * len(lons)}")
    print(f"    NaN count  : {nan_count}")
    print(f"    Provenance : REANALYSIS")
    print()
    print("data_status = LOADED")

    return {
        "data_status": "LOADED",
        "samples_count": len(samples),
        "nan_count": nan_count,
        "time_range": [times[0].isoformat(), times[-1].isoformat()],
    }


def _validate_wind(samples, times, lats, lons, nan_count) -> dict:
    """Run data quality checks on retrieved wind data."""
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

    # Wind magnitude validation (u/v → speed)
    magnitude_ok = True
    for s in samples[:100]:
        expected = math.sqrt(s["u10"] ** 2 + s["v10"] ** 2)
        if abs(s["wind_speed"] - expected) > 0.01:
            magnitude_ok = False
            break
    checks["wind_magnitude_correct"] = magnitude_ok

    # Incident time overlap
    if times:
        incident_covered = (
            times[0] <= INCIDENT_TIME <= times[-1]
        )
        checks["incident_time_covered"] = incident_covered
    else:
        checks["incident_time_covered"] = False

    return checks


def _write_not_loaded(reason: str):
    """Update wind.json to clearly indicate NOT_LOADED status."""
    wind_data = json.loads(WIND_FILE.read_text())
    wind_data["data_status"] = "NOT_LOADED"
    wind_data["status_message"] = f"Historical environmental forcing not loaded — {reason}"
    wind_data["samples"] = []
    WIND_FILE.write_text(json.dumps(wind_data, indent=2, ensure_ascii=False) + "\n")


def _update_provenance(field: str, status: str):
    """Update the metocean provenance file."""
    prov = json.loads(PROVENANCE_FILE.read_text())
    prov[field]["status"] = status
    PROVENANCE_FILE.write_text(json.dumps(prov, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch ERA5 10 m wind reanalysis for the Ennore 2017 incident."
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

    fetch_era5_wind()


if __name__ == "__main__":
    main()
