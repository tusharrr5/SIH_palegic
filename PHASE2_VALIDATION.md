# PHASE2_VALIDATION.md
# Automated validation report for SIH-ENNORE-2017 canonical incident package

## Validation run

Executed: `python3 -c "...validation script..."` — 2026-09-25

---

## CHECK 1 — JSON file integrity

All 12 package files pass `json.loads()` without errors.

| File | Status |
|---|---|
| manifest.json | ✅ PASS |
| incident.json | ✅ PASS |
| sar/scene_metadata.json | ✅ PASS |
| sar/README.md | ✅ PASS (not JSON) |
| spill/observed_slick.geojson | ✅ PASS |
| spill/detection_metadata.json | ✅ PASS |
| ais/tracks.json | ✅ PASS |
| ais/provenance.json | ✅ PASS |
| metocean/wind.json | ✅ PASS |
| metocean/currents.json | ✅ PASS |
| metocean/provenance.json | ✅ PASS |
| timeline/events.json | ✅ PASS |
| evidence/evidence.json | ✅ PASS |

---

## CHECK 2 — AIS provenance classification

Both tracks carry the mandatory fields and values.

| Field | ennore-track-bw-maple | ennore-track-dawn-kancheepuram |
|---|---|---|
| `provenance_class` | ✅ TRAINING | ✅ TRAINING |
| `is_synthetic` | ✅ true | ✅ true |
| `ui_label` | ✅ "Training AIS reconstruction" | ✅ "Training AIS reconstruction" |
| `ui_warning` | ✅ present | ✅ present |
| Swedish AIS separation | ✅ No Swedish tracks in ais/tracks.json | ✅ No Swedish tracks in ais/tracks.json |

---

## CHECK 3 — Metocean NOT_LOADED enforcement

| File | `data_status` | `provenance_class` | `samples` empty |
|---|---|---|---|
| metocean/wind.json | ✅ NOT_LOADED | ✅ REANALYSIS | ✅ [] |
| metocean/currents.json | ✅ NOT_LOADED | ✅ REANALYSIS | ✅ [] |
| metocean/provenance.json | ✅ fallback_policy=NONE | ✅ present | — |

---

## CHECK 4 — Slick geometry

| Check | Result |
|---|---|
| GeoJSON type = MultiPolygon | ✅ PASS |
| All rings closed (first coord = last coord) | ✅ PASS — 2 polygons |
| Coordinates in Bay of Bengal range (79–82°E, 12–15°N) | ✅ PASS |
| detection_method label honest | ✅ "historical_validation_mask" |
| provenance_class | ✅ ILLUSTRATIVE |

---

## CHECK 5 — Incident identity completeness

| Field | Value | Status |
|---|---|---|
| incident_id | SIH-ENNORE-2017 | ✅ |
| investigation_mode | historical_validation | ✅ |
| latitude / longitude | 13.28 / 80.33 | ✅ Bay of Bengal |
| incident_start | 2017-01-28T08:00:00Z | ✅ |
| satellite_observation_time | 2017-01-29T04:30:00Z | ✅ |
| status | closed | ✅ |

---

## CHECK 6 — Timeline event completeness

| Event type | Count | Status |
|---|---|---|
| INCIDENT_REPORTED | 1 | ✅ |
| VESSEL_POSITION | 1 | ✅ |
| AIS_GAP_START | 2 | ✅ |
| AIS_GAP_END | 2 | ✅ |
| SATELLITE_ACQUISITION | 1 | ✅ |
| SLICK_OBSERVATION | 1 | ✅ |
| WIND_SAMPLE | 1 (NOT_LOADED placeholder) | ✅ |
| CURRENT_SAMPLE | 1 (NOT_LOADED placeholder) | ✅ |
| ORIGIN_ESTIMATE | 1 | ✅ |
| CANDIDATE_EVIDENCE | 1 | ✅ |
| INVESTIGATION_COMPLETE | 1 | ✅ |
| **Total** | **13** | ✅ |

---

## CHECK 7 — Evidence bundle completeness

| Evidence item | provenance_class | Status |
|---|---|---|
| EV-001 — SAR slick observation | ILLUSTRATIVE | ✅ |
| EV-002 — Vessel collision record | RECORDED | ✅ |
| EV-003 — BW Maple AIS track | TRAINING | ✅ |
| EV-004 — Dawn Kancheepuram AIS track | TRAINING | ✅ |
| EV-005 — ERA5 wind | REANALYSIS / NOT_LOADED | ✅ |
| EV-006 — CMEMS currents | REANALYSIS / NOT_LOADED | ✅ |

---

## CHECK 8 — Seed script syntax

```
python3 -m py_compile scripts/seed_ennore.py → OK
```

✅ PASS — no syntax errors

---

## CHECK 9 — Seed idempotency (static analysis)

The seed script uses `ON CONFLICT(id) DO NOTHING` for all three INSERT statements:
- `observations` INSERT
- `tracks` INSERT  
- `cases` INSERT

✅ Safe to run twice — no duplicates will be created.

---

## CHECK 10 — UI labelling

| Label | Required by spec | Implemented |
|---|---|---|
| "Training AIS reconstruction" in legend | Yes | ✅ OceanMap.tsx — checks provenance.provenance_class === "TRAINING" |
| "HISTORICAL VALIDATION · SIH-ENNORE-2017" kicker | Yes | ✅ EvidencePanel.tsx |
| Training AIS badge on candidate cards | Yes | ✅ EvidencePanel.tsx — .training-ais-badge class |
| "Data transparency notice" in Evidence tab | Yes | ✅ EvidencePanel.tsx |
| "ENNORE / BAY OF BENGAL" region label on map | Yes | ✅ OceanMap.tsx |
| Coordinates "13° 17′ N · 80° 20′ E" on map | Yes | ✅ OceanMap.tsx |
| Map banner "HISTORICAL VALIDATION · Training AIS · Illustrative slick" | Yes | ✅ OceanMap.tsx |
| RUN DEMO routes to SIH-ENNORE-2017 first | Yes | ✅ page.tsx handleRunDemo |

---

## Known gaps (to be resolved in later phases)

| Gap | Severity | Phase |
|---|---|---|
| ERA5 wind data not downloaded | HIGH — drift model cannot run | Phase 3 |
| CMEMS currents not downloaded | HIGH — drift model cannot run | Phase 3 |
| SAR raster not downloaded | MEDIUM — layer shows as unavailable | Phase 3 |
| Slick polygon is ILLUSTRATIVE, not SAR-derived | MEDIUM — honest but prototype-quality | Phase 3/4 |
| No verified historical AIS | MEDIUM — training tracks used | Phase 3 |
| MapLibre raster tile source for SAR not wired | LOW — contract defined, not rendered | Phase 4 |
| Animated replay for Ennore not implemented | LOW — existing replay engine ready | Phase 4 |

---

## Overall result

**12/12 JSON files valid**  
**13/13 timeline events present**  
**6/6 evidence items present**  
**All provenance classifications correct**  
**Seed script idempotent**  
**UI labels compliant**

> Phase 2 PASS — canonical incident package is complete and demo-ready.
> The application will correctly show "Historical environmental forcing not loaded"
> for drift backtracking and "Training AIS reconstruction" for all candidate tracks.
