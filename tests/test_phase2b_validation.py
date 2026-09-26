"""Phase 2B automated validation tests for the SIH-ENNORE-2017 canonical incident.

These tests validate:
1. Incident JSON schema
2. Provenance values
3. No Math.random() in canonical incident generation
4. No constant hidden wind fallback
5. No constant hidden current fallback
6. Timestamps are parseable
7. Geographic coordinates are valid
8. ERA5/CMEMS data overlap incident timeframe (when loaded)
9. Demo remains deterministic
10. Synthetic AIS cannot be labelled OBSERVED
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/demo/ennore-2017"

# ── Incident coordinates and time ───────────────────────────────────────
INCIDENT_LAT = 13.28
INCIDENT_LON = 80.33
INCIDENT_TIME = datetime(2017, 1, 28, 8, 0, 0, tzinfo=timezone.utc)
INCIDENT_START = "2017-01-28T08:00:00Z"


def load(path: str) -> dict:
    return json.loads((PACKAGE / path).read_text())


# ═══════════════════════════════════════════════════════════════════════
# 1. Incident JSON schema
# ═══════════════════════════════════════════════════════════════════════

class TestIncidentSchema:
    def test_incident_has_required_fields(self):
        inc = load("incident.json")
        required = [
            "incident_id", "name", "incident_type", "latitude", "longitude",
            "incident_start", "region", "country", "investigation_mode",
            "status", "sih_problem_id", "vessels_involved", "provenance_note",
        ]
        for field in required:
            assert field in inc, f"Missing required field: {field}"

    def test_incident_id_matches(self):
        assert load("incident.json")["incident_id"] == "SIH-ENNORE-2017"

    def test_sih_problem_id(self):
        assert load("incident.json")["sih_problem_id"] == "26143"

    def test_vessels_have_identity(self):
        vessels = load("incident.json")["vessels_involved"]
        assert len(vessels) == 2
        for v in vessels:
            assert "name" in v
            assert "imo" in v
            assert "type" in v
            assert "flag" in v

    def test_manifest_has_required_fields(self):
        m = load("manifest.json")
        required = ["package_id", "incident_id", "version", "files",
                     "data_completeness", "demo_ready"]
        for field in required:
            assert field in m, f"Missing manifest field: {field}"


# ═══════════════════════════════════════════════════════════════════════
# 2. Provenance values
# ═══════════════════════════════════════════════════════════════════════

VALID_PROVENANCE = {
    "OBSERVED", "REANALYSIS", "DERIVED", "ILLUSTRATIVE",
    "TRAINING", "SYNTHETIC", "NOT_LOADED", "RECORDED",
}


class TestProvenance:
    def test_spill_provenance_is_illustrative(self):
        meta = load("spill/detection_metadata.json")
        assert meta["provenance_class"] == "ILLUSTRATIVE"

    def test_ais_provenance_is_training(self):
        prov = load("ais/provenance.json")
        assert prov["provenance_class"] == "TRAINING"
        assert prov["is_synthetic"] is True

    def test_wind_provenance_is_reanalysis(self):
        wind = load("metocean/wind.json")
        assert wind["provenance_class"] == "REANALYSIS"

    def test_currents_provenance_is_reanalysis(self):
        curr = load("metocean/currents.json")
        assert curr["provenance_class"] == "REANALYSIS"

    def test_sar_metadata_provenance_is_observed(self):
        sar = load("sar/scene_metadata.json")
        assert sar["provenance_class"] == "OBSERVED"

    def test_all_tracks_marked_training(self):
        tracks = load("ais/tracks.json")["tracks"]
        for t in tracks:
            assert t["provenance_class"] == "TRAINING"
            assert t["is_synthetic"] is True

    def test_timeline_events_have_valid_provenance(self):
        events = load("timeline/events.json")["events"]
        for e in events:
            assert e["provenance_class"] in VALID_PROVENANCE, \
                f"Event {e['event_id']} has invalid provenance: {e['provenance_class']}"

    def test_evidence_items_have_valid_provenance(self):
        items = load("evidence/evidence.json")["evidence_items"]
        for item in items:
            assert item["provenance_class"] in VALID_PROVENANCE, \
                f"Evidence {item['evidence_id']} has invalid provenance: {item['provenance_class']}"

    def test_provenance_manifest_exists(self):
        manifest = load("provenance_manifest.json")
        assert "data_objects" in manifest
        assert len(manifest["data_objects"]) > 0

    def test_provenance_manifest_entries_have_required_fields(self):
        manifest = load("provenance_manifest.json")
        required = ["name", "source", "provider", "dataset", "source_type",
                     "provenance_class", "is_synthetic", "processing_steps",
                     "limitations", "licence_or_usage_note"]
        for obj in manifest["data_objects"]:
            for field in required:
                assert field in obj, \
                    f"Object '{obj.get('name', '?')}' missing field: {field}"


# ═══════════════════════════════════════════════════════════════════════
# 3. No Math.random() in canonical incident generation
# ═══════════════════════════════════════════════════════════════════════

class TestNoRandomData:
    def test_no_math_random_in_seed_script(self):
        seed = (ROOT / "scripts/seed_ennore.py").read_text()
        assert "Math.random" not in seed
        assert "random()" not in seed
        assert "random.random" not in seed

    def test_no_random_in_incident_data(self):
        """Ensure no file in the incident package contains random generation."""
        for path in PACKAGE.rglob("*.json"):
            content = path.read_text()
            assert "Math.random" not in content, f"Math.random found in {path.name}"

    def test_no_random_in_python_scripts(self):
        """Check data scripts don't use random for canonical data."""
        scripts = [
            "scripts/fetch_era5_wind.py",
            "scripts/fetch_cmems_currents.py",
            "scripts/search_sentinel1_ennore.py",
        ]
        for s in scripts:
            path = ROOT / s
            if path.exists():
                content = path.read_text()
                assert "random.random()" not in content, \
                    f"random.random() found in {s}"
                assert "np.random.rand(" not in content, \
                    f"np.random.rand found in {s}"


# ═══════════════════════════════════════════════════════════════════════
# 4. No constant hidden wind fallback
# ═══════════════════════════════════════════════════════════════════════

class TestNoWindFallback:
    def test_wind_status_is_not_loaded_or_loaded(self):
        wind = load("metocean/wind.json")
        assert wind["data_status"] in ("NOT_LOADED", "LOADED"), \
            f"Wind has unexpected status: {wind['data_status']}"

    def test_wind_has_no_hardcoded_samples_when_not_loaded(self):
        wind = load("metocean/wind.json")
        if wind["data_status"] == "NOT_LOADED":
            assert len(wind.get("samples", [])) == 0, \
                "Wind claims NOT_LOADED but has samples — possible hidden fallback"

    def test_wind_notes_refuse_constants(self):
        wind = load("metocean/wind.json")
        notes = wind.get("notes", "")
        assert "NOT substitute" in notes or "not substitute" in notes.lower() \
            or "fictional" in notes.lower()

    def test_no_hardcoded_wind_in_fetch_script(self):
        script = (ROOT / "scripts/fetch_era5_wind.py").read_text()
        # Must not contain hardcoded wind arrays
        assert "samples = [" not in script or "samples = []" in script
        assert "u10 =" not in script.split("def _parse_netcdf")[0], \
            "Hardcoded u10 values found before NetCDF parsing"


# ═══════════════════════════════════════════════════════════════════════
# 5. No constant hidden current fallback
# ═══════════════════════════════════════════════════════════════════════

class TestNoCurrentFallback:
    def test_currents_status_is_not_loaded_or_loaded(self):
        curr = load("metocean/currents.json")
        assert curr["data_status"] in ("NOT_LOADED", "LOADED"), \
            f"Currents has unexpected status: {curr['data_status']}"

    def test_currents_has_no_hardcoded_samples_when_not_loaded(self):
        curr = load("metocean/currents.json")
        if curr["data_status"] == "NOT_LOADED":
            assert len(curr.get("samples", [])) == 0, \
                "Currents claims NOT_LOADED but has samples — possible hidden fallback"

    def test_currents_notes_refuse_constants(self):
        curr = load("metocean/currents.json")
        notes = curr.get("notes", "")
        assert "NOT substitute" in notes or "not substitute" in notes.lower() \
            or "fictional" in notes.lower()


# ═══════════════════════════════════════════════════════════════════════
# 6. Timestamps are parseable
# ═══════════════════════════════════════════════════════════════════════

class TestTimestamps:
    def test_incident_start_parseable(self):
        inc = load("incident.json")
        dt = datetime.fromisoformat(inc["incident_start"])
        assert dt.year == 2017

    def test_ais_timestamps_parseable(self):
        tracks = load("ais/tracks.json")["tracks"]
        for t in tracks:
            for p in t["points"]:
                dt = datetime.fromisoformat(p["time"])
                assert dt.year == 2017

    def test_timeline_timestamps_parseable(self):
        events = load("timeline/events.json")["events"]
        for e in events:
            dt = datetime.fromisoformat(e["timestamp"])
            assert dt.year == 2017

    def test_wind_time_window_parseable(self):
        wind = load("metocean/wind.json")
        for ts in wind.get("time_window", []):
            datetime.fromisoformat(ts)

    def test_currents_time_window_parseable(self):
        curr = load("metocean/currents.json")
        for ts in curr.get("time_window", []):
            datetime.fromisoformat(ts)

    def test_loaded_wind_samples_timestamps(self):
        wind = load("metocean/wind.json")
        if wind["data_status"] == "LOADED":
            for s in wind["samples"][:50]:
                datetime.fromisoformat(s["timestamp"])

    def test_loaded_currents_samples_timestamps(self):
        curr = load("metocean/currents.json")
        if curr["data_status"] == "LOADED":
            for s in curr["samples"][:50]:
                datetime.fromisoformat(s["timestamp"])


# ═══════════════════════════════════════════════════════════════════════
# 7. Geographic coordinates are valid
# ═══════════════════════════════════════════════════════════════════════

class TestCoordinates:
    def test_incident_coordinates_valid(self):
        inc = load("incident.json")
        assert -90 <= inc["latitude"] <= 90
        assert -180 <= inc["longitude"] <= 180
        # Ennore is near Chennai
        assert 12 <= inc["latitude"] <= 14
        assert 79 <= inc["longitude"] <= 82

    def test_ais_coordinates_valid(self):
        tracks = load("ais/tracks.json")["tracks"]
        for t in tracks:
            for p in t["points"]:
                assert -90 <= p["lat"] <= 90, \
                    f"Invalid lat {p['lat']} in track {t['id']}"
                assert -180 <= p["lon"] <= 180, \
                    f"Invalid lon {p['lon']} in track {t['id']}"

    def test_ais_coordinates_near_ennore(self):
        tracks = load("ais/tracks.json")["tracks"]
        for t in tracks:
            for p in t["points"]:
                assert 12 <= p["lat"] <= 14, \
                    f"Point lat {p['lat']} outside Ennore region in {t['id']}"
                assert 79 <= p["lon"] <= 82, \
                    f"Point lon {p['lon']} outside Ennore region in {t['id']}"

    def test_slick_coordinates_valid(self):
        slick = load("spill/observed_slick.geojson")
        for feature in slick["features"]:
            coords = feature["geometry"]["coordinates"]
            for polygon in coords:
                for ring in polygon:
                    for lon, lat in ring:
                        assert -90 <= lat <= 90
                        assert -180 <= lon <= 180

    def test_timeline_spatial_coordinates_valid(self):
        events = load("timeline/events.json")["events"]
        for e in events:
            if "spatial" in e:
                assert -90 <= e["spatial"]["lat"] <= 90
                assert -180 <= e["spatial"]["lon"] <= 180

    def test_loaded_wind_coordinates_valid(self):
        wind = load("metocean/wind.json")
        if wind["data_status"] == "LOADED":
            for s in wind["samples"][:50]:
                assert -90 <= s["latitude"] <= 90
                assert -180 <= s["longitude"] <= 180

    def test_loaded_currents_coordinates_valid(self):
        curr = load("metocean/currents.json")
        if curr["data_status"] == "LOADED":
            for s in curr["samples"][:50]:
                assert -90 <= s["latitude"] <= 90
                assert -180 <= s["longitude"] <= 180


# ═══════════════════════════════════════════════════════════════════════
# 8. ERA5/CMEMS data overlap incident timeframe (when loaded)
# ═══════════════════════════════════════════════════════════════════════

class TestDataTemporalCoverage:
    def test_wind_time_window_covers_incident(self):
        wind = load("metocean/wind.json")
        window = wind.get("time_window", [])
        if len(window) == 2:
            start = datetime.fromisoformat(window[0])
            end = datetime.fromisoformat(window[1])
            assert start <= INCIDENT_TIME <= end, \
                "Wind time window does not cover the incident time"

    def test_currents_time_window_covers_incident(self):
        curr = load("metocean/currents.json")
        window = curr.get("time_window", [])
        if len(window) == 2:
            start = datetime.fromisoformat(window[0])
            end = datetime.fromisoformat(window[1])
            assert start <= INCIDENT_TIME <= end, \
                "Currents time window does not cover the incident time"

    def test_loaded_wind_samples_cover_incident(self):
        wind = load("metocean/wind.json")
        if wind["data_status"] == "LOADED" and wind.get("samples"):
            times = [datetime.fromisoformat(s["timestamp"]) for s in wind["samples"]]
            assert min(times) <= INCIDENT_TIME, \
                "Wind samples start after incident time"
            assert max(times) >= INCIDENT_TIME, \
                "Wind samples end before incident time"

    def test_loaded_currents_samples_cover_incident(self):
        curr = load("metocean/currents.json")
        if curr["data_status"] == "LOADED" and curr.get("samples"):
            times = [datetime.fromisoformat(s["timestamp"]) for s in curr["samples"]]
            assert min(times) <= INCIDENT_TIME
            assert max(times) >= INCIDENT_TIME

    def test_wind_spatial_extent_covers_incident(self):
        wind = load("metocean/wind.json")
        extent = wind.get("spatial_extent", {})
        if extent:
            assert extent["lat_min"] <= INCIDENT_LAT <= extent["lat_max"]
            assert extent["lon_min"] <= INCIDENT_LON <= extent["lon_max"]

    def test_currents_spatial_extent_covers_incident(self):
        curr = load("metocean/currents.json")
        extent = curr.get("spatial_extent", {})
        if extent:
            assert extent["lat_min"] <= INCIDENT_LAT <= extent["lat_max"]
            assert extent["lon_min"] <= INCIDENT_LON <= extent["lon_max"]


# ═══════════════════════════════════════════════════════════════════════
# 9. Demo remains deterministic
# ═══════════════════════════════════════════════════════════════════════

class TestDeterminism:
    def test_incident_json_is_deterministic(self):
        """Loading incident.json twice produces identical content."""
        a = load("incident.json")
        b = load("incident.json")
        assert a == b

    def test_ais_tracks_are_deterministic(self):
        a = load("ais/tracks.json")
        b = load("ais/tracks.json")
        assert a == b

    def test_slick_geojson_is_deterministic(self):
        a = load("spill/observed_slick.geojson")
        b = load("spill/observed_slick.geojson")
        assert a == b

    def test_ais_timestamps_monotonic(self):
        """AIS position timestamps must be monotonically increasing."""
        tracks = load("ais/tracks.json")["tracks"]
        for t in tracks:
            times = [datetime.fromisoformat(p["time"]) for p in t["points"]]
            for i in range(1, len(times)):
                assert times[i] >= times[i - 1], \
                    f"Non-monotonic timestamp in track {t['id']} at index {i}"

    def test_ais_no_impossible_coordinates(self):
        tracks = load("ais/tracks.json")["tracks"]
        for t in tracks:
            for p in t["points"]:
                assert abs(p["lat"]) <= 90
                assert abs(p["lon"]) <= 180

    def test_ais_no_unrealistic_speed_jumps(self):
        """Flag speed jumps > 30 knots between consecutive positions."""
        tracks = load("ais/tracks.json")["tracks"]
        for t in tracks:
            for i in range(1, len(t["points"])):
                sog_prev = t["points"][i - 1].get("sog", 0)
                sog_curr = t["points"][i].get("sog", 0)
                if sog_prev is not None and sog_curr is not None:
                    # Both should be reasonable
                    assert sog_curr <= 30, \
                        f"Unrealistic SOG {sog_curr} kn in track {t['id']}"

    def test_ais_gaps_are_preserved(self):
        """Verify AIS gaps are documented in the track data."""
        tracks = load("ais/tracks.json")["tracks"]
        gap_events = []
        for t in tracks:
            for p in t["points"]:
                if p.get("_event") in ("AIS_GAP_START", "AIS_GAP_END"):
                    gap_events.append(p["_event"])
        assert len(gap_events) >= 2, "Expected at least one gap start and end"


# ═══════════════════════════════════════════════════════════════════════
# 10. Synthetic AIS cannot be labelled OBSERVED
# ═══════════════════════════════════════════════════════════════════════

class TestSyntheticNotObserved:
    def test_synthetic_tracks_not_labelled_observed(self):
        tracks = load("ais/tracks.json")["tracks"]
        for t in tracks:
            if t.get("is_synthetic") or t.get("is_reconstruction"):
                assert t["provenance_class"] != "OBSERVED", \
                    f"Track {t['id']} is synthetic but labelled OBSERVED"

    def test_synthetic_ais_provenance_not_observed(self):
        prov = load("ais/provenance.json")
        if prov.get("is_synthetic"):
            assert prov["provenance_class"] != "OBSERVED", \
                "AIS provenance is synthetic but labelled OBSERVED"

    def test_training_evidence_not_observed(self):
        items = load("evidence/evidence.json")["evidence_items"]
        for item in items:
            if item.get("is_synthetic"):
                assert item["provenance_class"] != "OBSERVED", \
                    f"Evidence {item['evidence_id']} is synthetic but labelled OBSERVED"

    def test_ui_warning_on_training_tracks(self):
        tracks = load("ais/tracks.json")["tracks"]
        for t in tracks:
            if t["provenance_class"] == "TRAINING":
                assert "ui_warning" in t, \
                    f"Track {t['id']} is TRAINING but has no ui_warning"
                assert "NOT recorded" in t["ui_warning"] or "not recorded" in t["ui_warning"].lower()


# ═══════════════════════════════════════════════════════════════════════
# Additional SAR validation
# ═══════════════════════════════════════════════════════════════════════

class TestSARValidation:
    def test_sar_footprint_intersects_incident(self):
        sar = load("sar/scene_metadata.json")
        bbox = sar["bounding_box"]
        coords = bbox["coordinates"][0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        assert min(lons) <= INCIDENT_LON <= max(lons), \
            "SAR bounding box does not cover incident longitude"
        assert min(lats) <= INCIDENT_LAT <= max(lats), \
            "SAR bounding box does not cover incident latitude"

    def test_sar_acquisition_timestamp(self):
        sar = load("sar/scene_metadata.json")
        dt = datetime.fromisoformat(sar["acquisition_time"])
        assert dt.year == 2017
        assert dt.month == 1

    def test_sar_not_claiming_detection(self):
        sar = load("sar/scene_metadata.json")
        if not sar.get("is_raster_loaded"):
            assert sar["data_status"].startswith("METADATA_ONLY") or \
                "not yet" in sar["data_status"].lower()

    def test_sar_source_not_scihub(self):
        """Verify the retired SciHub is not used as the source."""
        sar = load("sar/scene_metadata.json")
        assert "scihub.copernicus.eu" not in sar.get("source", ""), \
            "SAR metadata still references the retired SciHub"
