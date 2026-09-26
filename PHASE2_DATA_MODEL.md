# PHASE2_DATA_MODEL.md

## How Incident, SAR, Slick, AIS, Environment, Timeline, and Evidence Relate

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SIH-ENNORE-2017 Data Model                           │
└─────────────────────────────────────────────────────────────────────────┘

  INCIDENT (incident.json)
  ├── Canonical identity: location, time, mode=historical_validation
  ├── Known public facts: vessels, spill volume, coastline affected
  └── Links to every layer below

  SAR (sar/scene_metadata.json)
  ├── Platform: Sentinel-1A IW GRD
  ├── Acquisition: 2017-01-29T04:30:00Z
  ├── data_status: METADATA_ONLY (raster not yet downloaded)
  └── Defines the expected contract for the raster layer

        ↓ SAR scene observes surface
  SLICK (spill/observed_slick.geojson + detection_metadata.json)
  ├── Geometry: MultiPolygon, Bay of Bengal, near Ennore
  ├── provenance_class: ILLUSTRATIVE
  ├── detection_method: historical_validation_mask
  │   (manually digitised from secondary sources — NOT ML detection)
  └── Maps to → DB: observations table (id=ennore-obs-2017-01-29)

        ↓ Slick anchors the investigation case
  CASE (DB: cases table, id=SIH-ENNORE-2017)
  ├── trigger=sar, observation_id=ennore-obs-2017-01-29
  ├── published=true, exercise=false
  └── findings: metocean status, AIS status, evidence items, provenance

        ↓ AIS tracks are ranked against the slick centroid
  AIS (ais/tracks.json + provenance.json)
  ├── Track: ennore-track-bw-maple  (TRAINING / is_synthetic=true)
  ├── Track: ennore-track-dawn-kancheepuram (TRAINING / is_synthetic=true)
  ├── UI must display: "Training AIS reconstruction"
  ├── rank_sources() computes proximity, temporal, behavior scores
  └── Maps to → DB: tracks table (synthetic=true)

        ↓ Environment is required for drift backtracking
  METOCEAN (metocean/wind.json + currents.json + provenance.json)
  ├── ERA5 wind: NOT_LOADED — provenance_class=REANALYSIS
  ├── CMEMS currents: NOT_LOADED — provenance_class=REANALYSIS
  ├── Fallback: NONE (must NOT silently use fictional constants)
  └── Controls: particle_backtrack() in analytics.py

        ↓ All events are ordered in a single timeline
  TIMELINE (timeline/events.json)
  ├── EVT-001: INCIDENT_REPORTED (RECORDED — 2017-01-28T08:00)
  ├── EVT-002–006: VESSEL_POSITION / AIS_GAP (TRAINING)
  ├── EVT-007: SATELLITE_ACQUISITION (OBSERVED — 2017-01-29)
  ├── EVT-008: SLICK_OBSERVATION (ILLUSTRATIVE)
  ├── EVT-009–010: WIND/CURRENT samples (REANALYSIS — NOT_LOADED)
  ├── EVT-011: ORIGIN_ESTIMATE (RECORDED — collision site)
  ├── EVT-012: CANDIDATE_EVIDENCE (DERIVED)
  └── EVT-013: INVESTIGATION_COMPLETE (RECORDED)

        ↓ All evidence items are bundled with provenance
  EVIDENCE (evidence/evidence.json)
  ├── EV-001: SAR slick — ILLUSTRATIVE
  ├── EV-002: Collision record — RECORDED
  ├── EV-003: BW Maple track — TRAINING
  ├── EV-004: Dawn Kancheepuram track — TRAINING
  ├── EV-005: ERA5 wind — REANALYSIS (NOT_LOADED)
  └── EV-006: CMEMS currents — REANALYSIS (NOT_LOADED)
```

## Database mapping

| Package layer | DB table | Notes |
|---|---|---|
| Slick polygon | `observations` | id=ennore-obs-2017-01-29, temporal_precision=hour |
| AIS tracks | `tracks` | synthetic=true, provenance.provenance_class=TRAINING |
| Investigation case | `cases` | id=SIH-ENNORE-2017, trigger=sar |
| Evidence chain | `cases.findings` (JSONB) | Full evidence bundle in findings column |
| Audit events | `audit` | Written by seed script actions |

## Provenance flow

```
PUBLIC RECORDS (RECORDED)
  └── Collision date, location, vessels, spill volume
        → EVT-001, EV-002, EVT-011, EVT-013

ESA COPERNICUS (OBSERVED / METADATA_ONLY)
  └── Sentinel-1A scene metadata
        → scene_metadata.json, EVT-007

SECONDARY DIGITISATION (ILLUSTRATIVE)
  └── Slick polygon from news/ITOPF maps
        → observed_slick.geojson, EV-001, EVT-008

PALEGIC TRAINING FIXTURE (TRAINING / is_synthetic=true)
  └── AIS track reconstructions
        → tracks.json, EV-003, EV-004, EVT-002–006

ECMWF ERA5 (REANALYSIS / NOT_LOADED)
  └── Wind data schema
        → wind.json, EV-005, EVT-009

CMEMS (REANALYSIS / NOT_LOADED)
  └── Current data schema
        → currents.json, EV-006, EVT-010

PALEGIC HEURISTIC (DERIVED)
  └── rank_sources() priority score
        → cases.ranking, EVT-012
```
