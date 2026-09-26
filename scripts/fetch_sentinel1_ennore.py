#!/usr/bin/env python3
"""Download a Sentinel-1 scene from the Copernicus Data Space Ecosystem (CDSE).

Usage:
    python scripts/fetch_sentinel1_ennore.py --product-id <CDSE_PRODUCT_ID>

Requires a CDSE account. Credentials are read from environment variables:
    CDSE_USERNAME  — your Copernicus Data Space email
    CDSE_PASSWORD  — your Copernicus Data Space password

If credentials are unavailable, the script fails clearly with:
    data_status = NOT_LOADED

The script does NOT claim oil slick detection. Downloading a SAR raster
does not constitute detection — that requires a separate processing step.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/demo/ennore-2017"
SEARCH_RESULTS = PACKAGE / "sar/sentinel1_search_results.json"
SCENE_METADATA = PACKAGE / "sar/scene_metadata.json"
SAR_DIR = PACKAGE / "sar"

# CDSE token endpoint
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_DOWNLOAD_URL = "https://zipper.dataspace.copernicus.eu/odata/v1/Products"


def get_access_token(username: str, password: str) -> str:
    """Obtain an OAuth2 access token from CDSE identity service."""
    import urllib.request
    import urllib.parse

    data = urllib.parse.urlencode({
        "client_id": "cdse-public",
        "grant_type": "password",
        "username": username,
        "password": password,
    }).encode("utf-8")

    req = urllib.request.Request(
        CDSE_TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        token_data = json.loads(resp.read().decode("utf-8"))

    return token_data["access_token"]


def download_product(product_id: str, token: str, output_dir: Path) -> Path:
    """Download a product ZIP from CDSE using the product ID."""
    import urllib.request

    url = f"{CDSE_DOWNLOAD_URL}({product_id})/$value"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
        },
    )

    output_path = output_dir / f"{product_id}.zip"
    print(f"  Downloading to: {output_path.name}")

    with urllib.request.urlopen(req, timeout=300) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        with open(output_path, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    print(f"\r  Progress: {pct:.1f}%", end="", flush=True)
        print()

    return output_path


def update_scene_metadata(product_id: str, product_name: str, download_path: Path, scene_data: dict = None):
    """Update the scene metadata file with download status."""
    meta = json.loads(SCENE_METADATA.read_text())
    now_iso = datetime.now(timezone.utc).isoformat()
    meta["raster_status"] = "DOWNLOADED"
    meta["data_status"] = "DOWNLOADED — detection not yet performed"
    meta["is_raster_loaded"] = False  # Still false — raster is downloaded, not yet processed/segmented
    meta["download_path"] = str(download_path.relative_to(ROOT))
    meta["downloaded_at"] = now_iso
    meta["retrieval_timestamp"] = now_iso
    meta["product_id"] = product_id
    meta["product_name"] = product_name or meta.get("product_name", "")
    meta["source"] = "Copernicus Data Space Ecosystem (CDSE) — https://dataspace.copernicus.eu/"
    meta["source_url"] = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({product_id})"
    meta["source_note"] = (
        "Raster downloaded but NOT processed for oil detection. "
        "is_raster_loaded remains false until VV sigma-naught extraction "
        "and oil detection pipeline have been applied."
    )
    if scene_data:
        meta["platform"] = scene_data.get("satellite", meta.get("platform", "Sentinel-1A"))
        meta["instrument"] = "C-SAR (C-band Synthetic Aperture Radar)"
        meta["mode"] = scene_data.get("instrument_mode", "IW")
        meta["product_type"] = "GRD"
        meta["polarization"] = scene_data.get("polarisation", "VV+VH")
        meta["acquisition_timestamp"] = scene_data.get("acquisition_start", meta.get("acquisition_start"))
        meta["footprint"] = scene_data.get("footprint", meta.get("footprint"))

    SCENE_METADATA.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(f"  Updated: {SCENE_METADATA.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(
        description="Download a Sentinel-1 scene from CDSE for the Ennore 2017 incident."
    )
    parser.add_argument(
        "--product-id",
        type=str,
        help="CDSE product ID to download. If omitted, uses scientifically verified scene from scene_metadata.json.",
    )
    args = parser.parse_args()

    # Check credentials
    username = os.environ.get("CDSE_USERNAME", "")
    password = os.environ.get("CDSE_PASSWORD", "")

    if not username or not password:
        print("=" * 60)
        print("ERROR: CDSE credentials not found.")
        print()
        print("Set the following environment variables:")
        print("  export CDSE_USERNAME='your-email@example.com'")
        print("  export CDSE_PASSWORD='your-password'")
        print()
        print("Register at: https://dataspace.copernicus.eu/")
        print("=" * 60)
        print()
        print("data_status = NOT_LOADED")
        print()
        print("The SAR raster has NOT been downloaded.")
        print("The existing scene metadata is preserved with METADATA_ONLY status.")
        sys.exit(1)

    # Determine product ID — default to the scientifically optimal scene
    product_id = args.product_id
    product_name = None
    target_scene = None

    if not product_id and SCENE_METADATA.exists():
        curr_meta = json.loads(SCENE_METADATA.read_text())
        product_id = curr_meta.get("product_id")
        product_name = curr_meta.get("product_name")

    if not product_id and SEARCH_RESULTS.exists():
        search = json.loads(SEARCH_RESULTS.read_text())
        scenes = search.get("scenes", [])
        if scenes:
            # Pick scene covering the incident coordinate (13.28, 80.33)
            for sc in scenes:
                if "003132" in sc.get("product_name", ""):
                    target_scene = sc
                    break
            if not target_scene:
                target_scene = scenes[0]
            product_id = target_scene["product_id"]
            product_name = target_scene.get("product_name", "")
            print(f"  Selected optimal candidate scene: {product_name}")
        else:
            print("No scenes found in search results.")
            print("data_status = NO_SUITABLE_ACQUISITION_CONFIRMED")
            sys.exit(1)

    if not product_id:
        print("No product ID specified and no search results available.")
        print("Run scripts/search_sentinel1_ennore.py first.")
        sys.exit(1)

    print(f"Fetching Sentinel-1 scene from CDSE…")
    print(f"  Product ID: {product_id}")
    print()

    try:
        print("  Authenticating with CDSE…")
        token = get_access_token(username, password)
        print("  ✓ Authentication successful")
        print()

        SAR_DIR.mkdir(parents=True, exist_ok=True)
        download_path = download_product(product_id, token, SAR_DIR)
        print(f"  ✓ Downloaded: {download_path.name}")
        print(f"    Size: {download_path.stat().st_size / 1e6:.1f} MB")

        update_scene_metadata(product_id, product_name or "", download_path)

        print()
        print("IMPORTANT: Downloading a SAR raster does NOT constitute")
        print("oil slick detection. The detection pipeline must be run")
        print("separately. Until then:")
        print("  is_raster_loaded = false")
        print("  provenance_class = OBSERVED (scene metadata)")
        print("  slick detection  = ILLUSTRATIVE (unchanged)")
        print()
        print("data_status = RASTER_DOWNLOADED")

    except Exception as exc:
        print(f"  ✗ Download failed: {exc}")
        print()
        print("data_status = NOT_LOADED")
        sys.exit(1)


if __name__ == "__main__":
    main()
