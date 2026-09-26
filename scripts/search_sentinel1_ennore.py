#!/usr/bin/env python3
"""Search Sentinel-1 scenes covering the Ennore / Kamarajar Port area
around the 28 January 2017 oil spill incident.

Uses the Copernicus Data Space Ecosystem (CDSE) OData catalogue.
The retired ESA SciHub / Open Access Hub is NOT used.

Usage:
    python scripts/search_sentinel1_ennore.py [--days-before 5] [--days-after 5]

Output:
    data/demo/ennore-2017/sar/sentinel1_search_results.json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/demo/ennore-2017"
OUTPUT = PACKAGE / "sar/sentinel1_search_results.json"

# Incident parameters
INCIDENT_TIME = datetime(2017, 1, 28, 8, 0, 0, tzinfo=timezone.utc)
INCIDENT_LAT = 13.28
INCIDENT_LON = 80.33

# Bounding box around the incident area
# (lon_min, lat_min, lon_max, lat_max)
AOI_BBOX = (79.8, 12.9, 81.0, 13.7)

# CDSE OData catalogue endpoint
CDSE_ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"


def build_search_url(
    start: datetime,
    end: datetime,
    bbox: tuple[float, float, float, float],
    collection: str = "SENTINEL-1",
    product_type: str = "GRD",
    max_results: int = 50,
) -> str:
    """Build a CDSE OData search URL with spatial/temporal/product filters."""
    lon_min, lat_min, lon_max, lat_max = bbox

    # OData polygon filter (WKT footprint intersect)
    wkt_polygon = (
        f"POLYGON(({lon_min} {lat_min},"
        f"{lon_max} {lat_min},"
        f"{lon_max} {lat_max},"
        f"{lon_min} {lat_max},"
        f"{lon_min} {lat_min}))"
    )

    filters = [
        f"Collection/Name eq '{collection}'",
        f"ContentDate/Start ge {start.strftime('%Y-%m-%dT%H:%M:%S.000Z')}",
        f"ContentDate/Start le {end.strftime('%Y-%m-%dT%H:%M:%S.000Z')}",
        f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt_polygon}')",
        f"contains(Name, '{product_type}')",
    ]

    filter_str = " and ".join(filters)
    # Encode filter and orderby separately to handle spaces properly
    from urllib.parse import urlencode
    params = {
        "$filter": filter_str,
        "$top": str(max_results),
        "$orderby": "ContentDate/Start asc",
    }
    url = f"{CDSE_ODATA_URL}?{urlencode(params)}"
    return url


def search_scenes(days_before: int = 5, days_after: int = 5) -> dict:
    """Execute the CDSE OData search and return structured results."""
    try:
        import urllib.request
        import urllib.error
    except ImportError:
        pass  # Always available in stdlib

    start = INCIDENT_TIME - timedelta(days=days_before)
    end = INCIDENT_TIME + timedelta(days=days_after)

    url = build_search_url(start, end, AOI_BBOX)

    print(f"Searching CDSE catalogue for Sentinel-1 GRD scenes…")
    print(f"  Time window : {start.isoformat()} → {end.isoformat()}")
    print(f"  AOI bbox    : {AOI_BBOX}")
    print(f"  URL         : {url[:120]}…")
    print()

    results = {
        "search_metadata": {
            "incident_id": "SIH-ENNORE-2017",
            "search_platform": "Copernicus Data Space Ecosystem (CDSE)",
            "catalogue_url": "https://catalogue.dataspace.copernicus.eu",
            "odata_endpoint": CDSE_ODATA_URL,
            "search_url": url,
            "time_window_start": start.isoformat(),
            "time_window_end": end.isoformat(),
            "aoi_bbox": {
                "lon_min": AOI_BBOX[0],
                "lat_min": AOI_BBOX[1],
                "lon_max": AOI_BBOX[2],
                "lat_max": AOI_BBOX[3],
            },
            "collection": "SENTINEL-1",
            "product_type_filter": "GRD",
            "searched_at": datetime.now(timezone.utc).isoformat(),
        },
        "scenes": [],
        "search_status": "PENDING",
        "notes": "",
    }

    try:
        import ssl
        import certifi
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    except (ImportError, Exception):
        import ssl
        ssl_ctx = ssl.create_default_context()
        # Fallback: if default context also fails, try unverified
        # (only for CDSE catalogue searches, not for credential-bearing requests)
        try:
            urllib.request.urlopen(
                urllib.request.Request(CDSE_ODATA_URL.split("?")[0],
                                       headers={"Accept": "application/json"}),
                timeout=5, context=ssl_ctx)
        except ssl.SSLCertVerificationError:
            ssl_ctx = ssl._create_unverified_context()

    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "PALEGIC-SIH2026/phase2b",
            },
        )
        with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        results["search_status"] = "SEARCH_FAILED"
        results["notes"] = (
            f"CDSE catalogue query failed: {exc}. "
            "This may be due to network restrictions or the CDSE API "
            "being temporarily unavailable. The search URL is recorded "
            "for manual verification."
        )
        print(f"  ⚠ Search failed: {exc}")
        print(f"  The search URL has been saved for manual verification.")
        _save(results)
        return results

    entries = data.get("value", [])
    print(f"  Found {len(entries)} scene(s) matching filters.")

    for entry in entries:
        scene = _parse_entry(entry)
        results["scenes"].append(scene)
        print(f"    • {scene['product_id']}")
        print(f"      {scene['satellite']} | {scene['acquisition_start']}")
        print(f"      Mode: {scene['instrument_mode']} | Pol: {scene['polarisation']}")

    if entries:
        results["search_status"] = "SCENES_FOUND"
        results["notes"] = (
            f"{len(entries)} Sentinel-1 GRD scene(s) found covering the "
            "Ennore incident area within the search window."
        )
    else:
        results["search_status"] = "NO_SUITABLE_ACQUISITION_CONFIRMED"
        results["notes"] = (
            "No Sentinel-1 GRD scenes found covering the Ennore incident "
            f"area between {start.date()} and {end.date()}. "
            "This may indicate no acquisition was scheduled over this region "
            "during this period, or the scene may be in long-term archive."
        )

    _save(results)
    return results


def _parse_entry(entry: dict) -> dict:
    """Extract structured metadata from a CDSE OData product entry."""
    name = entry.get("Name", "")

    # Attempt to extract satellite from name (e.g., S1A_ or S1B_)
    satellite = "Unknown"
    if name.startswith("S1A"):
        satellite = "Sentinel-1A"
    elif name.startswith("S1B"):
        satellite = "Sentinel-1B"

    # Extract instrument mode from name
    instrument_mode = "Unknown"
    for mode in ["IW", "EW", "SM", "WV"]:
        if f"_{mode}_" in name:
            instrument_mode = mode
            break

    # Extract polarisation from name
    polarisation = "Unknown"
    for pol in ["1SDV", "1SSH", "1SSV", "1SDH"]:
        if pol in name:
            pol_map = {
                "1SDV": "VV+VH",
                "1SSH": "HH",
                "1SSV": "VV",
                "1SDH": "HH+HV",
            }
            polarisation = pol_map.get(pol, pol)
            break

    # Extract processing level from name
    processing_level = "Unknown"
    if "GRDH" in name or "GRDM" in name:
        processing_level = "Level-1 GRD"
    elif "SLC" in name:
        processing_level = "Level-1 SLC"
    elif "OCN" in name:
        processing_level = "Level-2 OCN"

    content_date = entry.get("ContentDate", {})
    footprint_str = entry.get("Footprint", "")

    # Parse footprint geometry if available
    footprint = None
    if "GeoFootprint" in entry:
        footprint = entry["GeoFootprint"]
    elif footprint_str:
        footprint = footprint_str

    return {
        "product_id": entry.get("Id", name),
        "product_name": name,
        "satellite": satellite,
        "acquisition_start": content_date.get("Start", ""),
        "acquisition_end": content_date.get("End", ""),
        "orbit": entry.get("OrbitNumber"),
        "instrument_mode": instrument_mode,
        "polarisation": polarisation,
        "processing_level": processing_level,
        "footprint": footprint,
        "source_platform": "Copernicus Data Space Ecosystem (CDSE)",
        "download_status": "NOT_DOWNLOADED",
        "online_status": entry.get("Online", None),
        "content_length_bytes": entry.get("ContentLength"),
    }


def _save(results: dict):
    """Write search results to the incident package."""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    print(f"\n  Results saved to: {OUTPUT.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(
        description="Search Sentinel-1 scenes on CDSE for the Ennore 2017 incident."
    )
    parser.add_argument(
        "--days-before",
        type=int,
        default=5,
        help="Days before incident to include in search (default: 5)",
    )
    parser.add_argument(
        "--days-after",
        type=int,
        default=5,
        help="Days after incident to include in search (default: 5)",
    )
    args = parser.parse_args()
    search_scenes(days_before=args.days_before, days_after=args.days_after)


if __name__ == "__main__":
    main()
