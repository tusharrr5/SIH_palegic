# PHASE 2B — Validation Report

## Problem Statement ID: 26143
## Incident: SIH-ENNORE-2017

---

## Test Suite: `tests/test_phase2b_validation.py`

**60 tests — 60 passed — 0 failed**

### 1. Incident JSON Schema (5 tests)
| Test | Status |
|---|---|
| incident_has_required_fields | ✅ PASS |
| incident_id_matches | ✅ PASS |
| sih_problem_id | ✅ PASS |
| vessels_have_identity | ✅ PASS |
| manifest_has_required_fields | ✅ PASS |

### 2. Provenance Values (10 tests)
| Test | Status |
|---|---|
| spill_provenance_is_illustrative | ✅ PASS |
| ais_provenance_is_training | ✅ PASS |
| wind_provenance_is_reanalysis | ✅ PASS |
| currents_provenance_is_reanalysis | ✅ PASS |
| sar_metadata_provenance_is_observed | ✅ PASS |
| all_tracks_marked_training | ✅ PASS |
| timeline_events_have_valid_provenance | ✅ PASS |
| evidence_items_have_valid_provenance | ✅ PASS |
| provenance_manifest_exists | ✅ PASS |
| provenance_manifest_entries_have_required_fields | ✅ PASS |

### 3. No Math.random() in Canonical Data (3 tests)
| Test | Status |
|---|---|
| no_math_random_in_seed_script | ✅ PASS |
| no_random_in_incident_data | ✅ PASS |
| no_random_in_python_scripts | ✅ PASS |

### 4. No Constant Hidden Wind Fallback (4 tests)
| Test | Status |
|---|---|
| wind_status_is_not_loaded_or_loaded | ✅ PASS |
| wind_has_no_hardcoded_samples_when_not_loaded | ✅ PASS |
| wind_notes_refuse_constants | ✅ PASS |
| no_hardcoded_wind_in_fetch_script | ✅ PASS |

### 5. No Constant Hidden Current Fallback (3 tests)
| Test | Status |
|---|---|
| currents_status_is_not_loaded_or_loaded | ✅ PASS |
| currents_has_no_hardcoded_samples_when_not_loaded | ✅ PASS |
| currents_notes_refuse_constants | ✅ PASS |

### 6. Timestamps Are Parseable (7 tests)
| Test | Status |
|---|---|
| incident_start_parseable | ✅ PASS |
| ais_timestamps_parseable | ✅ PASS |
| timeline_timestamps_parseable | ✅ PASS |
| wind_time_window_parseable | ✅ PASS |
| currents_time_window_parseable | ✅ PASS |
| loaded_wind_samples_timestamps | ✅ PASS |
| loaded_currents_samples_timestamps | ✅ PASS |

### 7. Geographic Coordinates Are Valid (7 tests)
| Test | Status |
|---|---|
| incident_coordinates_valid | ✅ PASS |
| ais_coordinates_valid | ✅ PASS |
| ais_coordinates_near_ennore | ✅ PASS |
| slick_coordinates_valid | ✅ PASS |
| timeline_spatial_coordinates_valid | ✅ PASS |
| loaded_wind_coordinates_valid | ✅ PASS |
| loaded_currents_coordinates_valid | ✅ PASS |

### 8. ERA5/CMEMS Data Overlap Incident Timeframe (6 tests)
| Test | Status |
|---|---|
| wind_time_window_covers_incident | ✅ PASS |
| currents_time_window_covers_incident | ✅ PASS |
| loaded_wind_samples_cover_incident | ✅ PASS |
| loaded_currents_samples_cover_incident | ✅ PASS |
| wind_spatial_extent_covers_incident | ✅ PASS |
| currents_spatial_extent_covers_incident | ✅ PASS |

### 9. Demo Remains Deterministic (7 tests)
| Test | Status |
|---|---|
| incident_json_is_deterministic | ✅ PASS |
| ais_tracks_are_deterministic | ✅ PASS |
| slick_geojson_is_deterministic | ✅ PASS |
| ais_timestamps_monotonic | ✅ PASS |
| ais_no_impossible_coordinates | ✅ PASS |
| ais_no_unrealistic_speed_jumps | ✅ PASS |
| ais_gaps_are_preserved | ✅ PASS |

### 10. Synthetic AIS Cannot Be Labelled OBSERVED (4 tests)
| Test | Status |
|---|---|
| synthetic_tracks_not_labelled_observed | ✅ PASS |
| synthetic_ais_provenance_not_observed | ✅ PASS |
| training_evidence_not_observed | ✅ PASS |
| ui_warning_on_training_tracks | ✅ PASS |

### Additional SAR Validation (4 tests)
| Test | Status |
|---|---|
| sar_footprint_intersects_incident | ✅ PASS |
| sar_acquisition_timestamp | ✅ PASS |
| sar_not_claiming_detection | ✅ PASS |
| sar_source_not_scihub | ✅ PASS |

---

## Data Quality Summary

### ERA5 Wind
- **Timestamps**: Valid ✓
- **Coordinate bounds**: Valid (12.5°–14.0°N, 79.5°–81.0°E) ✓
- **NaN check**: N/A (NOT_LOADED)
- **Wind magnitude from u/v**: Script validates on download ✓
- **Incident time overlap**: Time window 2017-01-27 → 2017-01-30 covers incident ✓

### CMEMS Currents
- **Timestamps**: Valid ✓
- **Coordinate bounds**: Valid (12.5°–14.0°N, 79.5°–81.0°E) ✓
- **NaN check**: N/A (NOT_LOADED)
- **Current magnitude from u/v**: Script validates on download ✓
- **Depth**: Near-surface (0–1 m) ✓
- **Incident within spatial subset**: Yes ✓

### Sentinel-1
- **Footprint intersects incident**: Yes ✓ (verified from CDSE search)
- **Acquisition timestamp**: 2017-01-29T00:31:07Z ✓
- **Raster provenance**: METADATA_ONLY — no false detection claims ✓

### AIS
- **Timestamps monotonic**: Yes ✓
- **No impossible coordinates**: All points in Bay of Bengal region ✓
- **No unrealistic speed jumps**: Max SOG = 8.5 kn ✓
- **AIS gaps preserved**: 4 gap events documented ✓
