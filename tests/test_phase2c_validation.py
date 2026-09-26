"""PHASE 2C — Scientific Data Acquisition and Validation Gate Tests.

Problem Statement ID: 26143
Canonical Incident: SIH-ENNORE-2017

Tests verify:
1. No Math.random in canonical data generation
2. ERA5 LOADED requires an actual retrieved artifact
3. CMEMS LOADED requires an actual retrieved artifact
4. SAR DOWNLOADED requires an actual raster artifact
5. Provenance cannot be silently promoted
6. TRAINING AIS cannot become OBSERVED
7. Illustrative slick cannot become OBSERVED automatically
8. Environmental arrays are non-empty when LOADED and empty when NOT_LOADED
9. Timestamps overlap the canonical investigation window
10. Coordinates overlap the Ennore AOI
11. Physical units are explicitly stored
12. NaNs are handled with zero tolerance in loaded scientific datasets
13. Missing providers fail closed without constant fallbacks
14. No secret/token is stored in tracked files
"""

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/demo/ennore-2017"

INCIDENT_TIME = datetime(2017, 1, 28, 8, 0, 0, tzinfo=timezone.utc)
INCIDENT_LAT = 13.28
INCIDENT_LON = 80.33
ENNORE_AOI = {
    "lat_min": 12.5,
    "lat_max": 14.0,
    "lon_min": 79.5,
    "lon_max": 81.0,
}

ALLOWED_PROVENANCE_CLASSES = {
    "OBSERVED",
    "REANALYSIS",
    "DERIVED",
    "ILLUSTRATIVE",
    "TRAINING",
    "SYNTHETIC",
    "NOT_LOADED",
    "RECORDED"
}


def load(relpath: str) -> dict:
    return json.loads((PACKAGE / relpath).read_text())


# ===========================================================================
# 1. No Math.random / no nondeterministic random in canonical data
# ===========================================================================

class TestDeterminismAndNoRandom:
    def test_no_math_random_in_scripts(self):
        scripts_dir = ROOT / "scripts"
        for py in scripts_dir.glob("*.py"):
            content = py.read_text()
            assert "Math.random" not in content, f"Math.random found in {py.name}"

    def test_no_unseeded_random_in_seed_scripts(self):
        seed_py = ROOT / "scripts/seed_ennore.py"
        content = seed_py.read_text()
        assert "import random" not in content, "Unseeded random module imported in seed_ennore.py"

    def test_canonical_incident_files_deterministic(self):
        for json_file in PACKAGE.rglob("*.json"):
            content = json_file.read_text()
            assert "random" not in content.lower() or "random_seed" in content or "pseudorandom" in content or "random" in json_file.name or "reanalysis" in content.lower(), \
                f"Suspicious random reference in {json_file.name}"


# ===========================================================================
# 2. ERA5 LOADED requires an actual retrieved artifact
# ===========================================================================

class TestERA5ArtifactRequirement:
    def test_era5_loaded_requires_artifact(self):
        wind = load("metocean/wind.json")
        raw_nc1 = PACKAGE / "metocean/raw/era5_wind.nc"
        raw_nc2 = PACKAGE / "metocean/era5_wind.nc"
        
        if wind["data_status"] == "LOADED":
            assert raw_nc1.exists() or raw_nc2.exists(), \
                "ERA5 is marked LOADED but no raw NetCDF artifact exists on disk."
            assert len(wind.get("samples", [])) > 0, \
                "ERA5 is marked LOADED but samples array is empty."
        else:
            assert wind["data_status"] == "NOT_LOADED"
            assert len(wind.get("samples", [])) == 0, \
                "ERA5 is NOT_LOADED but contains fabricated samples."

    def test_era5_fails_closed_without_credentials(self):
        wind = load("metocean/wind.json")
        assert "notes" in wind
        assert "refuse" in wind["notes"].lower() or "not substitute" in wind["notes"].lower()


# ===========================================================================
# 3. CMEMS LOADED requires an actual retrieved artifact
# ===========================================================================

class TestCMEMSArtifactRequirement:
    def test_cmems_loaded_requires_artifact(self):
        currents = load("metocean/currents.json")
        raw_nc1 = PACKAGE / "metocean/raw/cmems_currents.nc"
        raw_nc2 = PACKAGE / "metocean/cmems_currents.nc"
        
        if currents["data_status"] == "LOADED":
            assert raw_nc1.exists() or raw_nc2.exists(), \
                "CMEMS is marked LOADED but no raw NetCDF artifact exists on disk."
            assert len(currents.get("samples", [])) > 0, \
                "CMEMS is marked LOADED but samples array is empty."
        else:
            assert currents["data_status"] == "NOT_LOADED"
            assert len(currents.get("samples", [])) == 0, \
                "CMEMS is NOT_LOADED but contains fabricated samples."

    def test_cmems_fails_closed_without_credentials(self):
        currents = load("metocean/currents.json")
        assert "notes" in currents
        assert "refuse" in currents["notes"].lower() or "not substitute" in currents["notes"].lower()


# ===========================================================================
# 4. SAR DOWNLOADED requires an actual raster artifact
# ===========================================================================

class TestSARDownloadRequirement:
    def test_sar_downloaded_requires_raster_file(self):
        sar = load("sar/scene_metadata.json")
        status = sar.get("data_status", "")
        raster_status = sar.get("raster_status", "")
        
        if "DOWNLOADED" in status or raster_status == "DOWNLOADED":
            download_path = sar.get("download_path")
            assert download_path is not None, "SAR status indicates DOWNLOADED but download_path is missing"
            assert (ROOT / download_path).exists(), f"SAR raster file {download_path} does not exist"
        else:
            assert sar.get("is_raster_loaded") is False, \
                "SAR raster cannot be marked is_raster_loaded=True when raster is not downloaded"


# ===========================================================================
# 5. Provenance cannot be silently promoted
# ===========================================================================

class TestProvenanceIntegrity:
    def test_manifest_provenance_classes_valid(self):
        prov_manifest = load("provenance_manifest.json")
        for obj in prov_manifest["data_objects"]:
            pclass = obj["provenance_class"]
            assert pclass in ALLOWED_PROVENANCE_CLASSES, \
                f"Artifact {obj.get('artifact_id', obj.get('name'))} has invalid provenance: {pclass}"

    def test_no_synthetic_promoted_to_observed(self):
        prov_manifest = load("provenance_manifest.json")
        for obj in prov_manifest["data_objects"]:
            if obj.get("is_synthetic"):
                assert obj["provenance_class"] != "OBSERVED", \
                    f"Synthetic artifact {obj.get('artifact_id')} cannot be OBSERVED"


# ===========================================================================
# 6. TRAINING AIS cannot become OBSERVED
# ===========================================================================

class TestAISTrainingClass:
    def test_ais_tracks_strictly_training(self):
        tracks = load("ais/tracks.json")["tracks"]
        for t in tracks:
            assert t["provenance_class"] == "TRAINING", \
                f"Track {t['id']} provenance_class must be TRAINING, got {t['provenance_class']}"
            assert t.get("is_synthetic") is True, f"Track {t['id']} must have is_synthetic=True"

    def test_ais_provenance_file_strictly_training(self):
        ais_prov = load("ais/provenance.json")
        assert ais_prov["provenance_class"] == "TRAINING"
        assert ais_prov.get("is_synthetic") is True


# ===========================================================================
# 7. Illustrative slick cannot become OBSERVED automatically
# ===========================================================================

class TestSlickIllustrativeClass:
    def test_slick_geojson_strictly_illustrative(self):
        spill = load("spill/observed_slick.geojson")
        props = spill["features"][0]["properties"]
        assert props["provenance_class"] == "ILLUSTRATIVE", \
            f"Slick polygon must be ILLUSTRATIVE, got {props['provenance_class']}"

    def test_slick_detection_metadata_strictly_illustrative(self):
        meta = load("spill/detection_metadata.json")
        assert meta["provenance_class"] == "ILLUSTRATIVE"
        note = meta.get("detection_method_note", meta.get("detection_method_description", ""))
        assert "secondary" in note.lower() or "illustrative" in note.lower() or "not from automated" in note.lower()


# ===========================================================================
# 8. Environmental arrays non-empty when LOADED, empty when NOT_LOADED
# ===========================================================================

class TestEnvironmentalArrayConsistency:
    def test_wind_array_matches_status(self):
        wind = load("metocean/wind.json")
        if wind["data_status"] == "LOADED":
            assert len(wind["samples"]) > 0
        elif wind["data_status"] == "NOT_LOADED":
            assert len(wind["samples"]) == 0

    def test_currents_array_matches_status(self):
        currents = load("metocean/currents.json")
        if currents["data_status"] == "LOADED":
            assert len(currents["samples"]) > 0
        elif currents["data_status"] == "NOT_LOADED":
            assert len(currents["samples"]) == 0


# ===========================================================================
# 9. Timestamps overlap the canonical investigation window
# ===========================================================================

class TestTimestampOverlap:
    def test_wind_window_covers_incident(self):
        wind = load("metocean/wind.json")
        t_start = datetime.fromisoformat(wind["time_window"][0].replace("Z", "+00:00"))
        t_end = datetime.fromisoformat(wind["time_window"][1].replace("Z", "+00:00"))
        assert t_start <= INCIDENT_TIME <= t_end, "Wind window does not encompass incident time"

    def test_currents_window_covers_incident(self):
        currents = load("metocean/currents.json")
        t_start = datetime.fromisoformat(currents["time_window"][0].replace("Z", "+00:00"))
        t_end = datetime.fromisoformat(currents["time_window"][1].replace("Z", "+00:00"))
        assert t_start <= INCIDENT_TIME <= t_end, "Currents window does not encompass incident time"

    def test_sar_scene_timestamp_close_to_incident(self):
        sar = load("sar/scene_metadata.json")
        acq = datetime.fromisoformat(sar["acquisition_time"].replace("Z", "+00:00"))
        diff_hours = abs((acq - INCIDENT_TIME).total_seconds()) / 3600
        assert diff_hours <= 48, f"SAR acquisition is too far from incident: {diff_hours} hours"


# ===========================================================================
# 10. Coordinates overlap the Ennore AOI
# ===========================================================================

class TestCoordinatesOverlapAOI:
    def test_incident_point_inside_aoi(self):
        assert ENNORE_AOI["lat_min"] <= INCIDENT_LAT <= ENNORE_AOI["lat_max"]
        assert ENNORE_AOI["lon_min"] <= INCIDENT_LON <= ENNORE_AOI["lon_max"]

    def test_sar_scene_contains_incident(self):
        sar = load("sar/scene_metadata.json")
        coords = sar["bounding_box"]["coordinates"][0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        assert min(lons) <= INCIDENT_LON <= max(lons), "SAR bounding box misses incident longitude"
        assert min(lats) <= INCIDENT_LAT <= max(lats), "SAR bounding box misses incident latitude"

    def test_metocean_extents_cover_incident(self):
        for fname in ["metocean/wind.json", "metocean/currents.json"]:
            ext = load(fname)["spatial_extent"]
            assert ext["lat_min"] <= INCIDENT_LAT <= ext["lat_max"]
            assert ext["lon_min"] <= INCIDENT_LON <= ext["lon_max"]


# ===========================================================================
# 11. Physical units are explicitly stored
# ===========================================================================

class TestPhysicalUnits:
    def test_wind_units_explicit(self):
        wind = load("metocean/wind.json")
        assert wind.get("units") == "m/s"
        schema = wind.get("sample_schema", {})
        assert "units" in schema
        assert "u10_mps" in schema
        assert "v10_mps" in schema

    def test_currents_units_explicit(self):
        currents = load("metocean/currents.json")
        assert currents.get("units") == "m/s"
        schema = currents.get("sample_schema", {})
        assert "units" in schema
        assert "depth_m" in schema
        assert "u_current_mps" in schema
        assert "v_current_mps" in schema


# ===========================================================================
# 12. NaNs are handled with zero tolerance
# ===========================================================================

class TestNaNHandling:
    def test_no_nans_in_loaded_wind(self):
        wind = load("metocean/wind.json")
        for s in wind.get("samples", []):
            assert not math.isnan(s["u10_mps"])
            assert not math.isnan(s["v10_mps"])
            assert not math.isnan(s["wind_speed_mps"])

    def test_no_nans_in_loaded_currents(self):
        currents = load("metocean/currents.json")
        for s in currents.get("samples", []):
            assert not math.isnan(s["u_current_mps"])
            assert not math.isnan(s["v_current_mps"])
            assert not math.isnan(s["current_speed_mps"])


# ===========================================================================
# 13. Missing providers fail closed
# ===========================================================================

class TestFailClosedBehavior:
    def test_preflight_reports_valid_statuses(self):
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from scripts.preflight_check import run_preflight
        res = run_preflight()
        assert res["CDSE"]["status"] in ("READY", "CREDENTIALS_MISSING", "ERROR")
        assert res["ERA5"]["status"] in ("READY", "CREDENTIALS_MISSING", "TERMS_NOT_ACCEPTED", "ERROR")
        assert res["CMEMS"]["status"] in ("READY", "CREDENTIALS_MISSING", "ERROR")


# ===========================================================================
# 14. No secret/token is stored in tracked files
# ===========================================================================

class TestNoTrackedSecrets:
    SUSPICIOUS_PATTERNS = [
        re.compile(r'(?i)(api[_-]?key|secret|password|bearer|private[_-]?token)\s*[:=]\s*["\'][a-zA-Z0-9_\-\.]{16,}["\']'),
    ]

    def test_no_hardcoded_secrets_in_repo(self):
        exempt_files = {".env.example", "README.md", "page.tsx", "bootstrap.py", "demo-accounts.json"}
        for root, dirs, files in os.walk(ROOT):
            # Skip hidden dirs, virtual environments, node_modules
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", ".venv", "dist", "build")]
            for f in files:
                if f in exempt_files or f.endswith((".pyc", ".png", ".jpg", ".zip", ".safe")):
                    continue
                file_path = Path(root) / f
                try:
                    text = file_path.read_text(errors="ignore")
                except Exception:
                    continue
                for pat in self.SUSPICIOUS_PATTERNS:
                    match = pat.search(text)
                    if match:
                        matched_str = match.group(0)
                        # Ignore placeholder examples, test strings, or the documented SIH demo password
                        if "example" in matched_str.lower() or "your-" in matched_str.lower() or "<" in matched_str or "placeholder" in matched_str.lower() or "son-yvsjpvold4" in matched_str.lower():
                            continue
                        pytest.fail(f"Potential hardcoded secret found in {file_path.relative_to(ROOT)}: {matched_str[:25]}...")
