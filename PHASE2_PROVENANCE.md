# PHASE2_PROVENANCE.md
# Data provenance register for SIH-ENNORE-2017

> All data used in the PALEGIC SIH 2026 demonstration must be classified below.
> This table is the authoritative provenance register for the Ennore 2017 canonical incident.

| DATA ITEM | SOURCE | DATE | REAL / DERIVED / TRAINING | PROCESSING | LIMITATION |
|---|---|---|---|---|---|
| Incident collision facts (date, location, vessels) | ITOPF; The Hindu (Chennai); Ministry of Shipping India; Kamarajar Port Authority press releases | Jan–Feb 2017 | REAL (RECORDED) | Direct use of publicly documented coordinates and facts | Secondary public sources; primary investigation records not obtained |
| BW Maple vessel identity (IMO 9346537) | Lloyd's/IMO ship registry; press reporting | 2017 | REAL (RECORDED) | Public record | Identity confirmed from public records; vessel movements not confirmed |
| Dawn Kancheepuram vessel identity (IMO 9368730) | Lloyd's/IMO ship registry; press reporting | 2017 | REAL (RECORDED) | Public record | Identity confirmed from public records; vessel movements not confirmed |
| Sentinel-1A SAR scene metadata | ESA Copernicus Open Access Hub | 2017-01-29 | REAL (OBSERVED) — METADATA ONLY | Scene ID and approximate bounding box from Copernicus catalogue | Actual raster NOT downloaded; metadata only; acquisition time approximate |
| Oil slick polygon (observed_slick.geojson) | Manually digitised from The Hindu, ITOPF, NRSC media reports | 2017-01 | DERIVED (ILLUSTRATIVE) | Manual digitisation in WGS84; topology validated | NOT the output of SAR classification; shape and position approximate; provenance_class=ILLUSTRATIVE |
| BW Maple AIS track (ennore-track-bw-maple) | PALEGIC training fixture | 2026-09 | TRAINING (is_synthetic=true) | Points placed at published collision site ±illustrative vectors; 30-min interval | NOT recorded AIS; UI must show "Training AIS reconstruction"; must never be labelled "Recorded AIS" |
| Dawn Kancheepuram AIS track (ennore-track-dawn-kancheepuram) | PALEGIC training fixture | 2026-09 | TRAINING (is_synthetic=true) | Same method as BW Maple | Same limitations |
| ERA5 10 m wind (wind.json) | ECMWF / Copernicus CDS | 2017-01 (schema defined; data NOT downloaded) | REANALYSIS (NOT_LOADED) | Schema only; no samples present | MUST be downloaded before drift backtracking can run; fallback to fictional values is forbidden |
| CMEMS surface current (currents.json) | Copernicus Marine Service GLOBAL-REANALYSIS-PHY-001-030 | 2017-01 (schema defined; data NOT downloaded) | REANALYSIS (NOT_LOADED) | Schema only; no samples present | Same as ERA5 |
| Master timeline (timeline/events.json) | Mixed — see provenance_class per event | 2026-09 | Mixed (RECORDED / TRAINING / ILLUSTRATIVE / REANALYSIS / DERIVED) | Events constructed from public sources + training fixtures; each event carries its own provenance_class | Timeline accuracy depends on provenance of each individual event |
| rank_sources() priority score | PALEGIC analytics engine | Computed at query time | DERIVED | Proximity (60%) + temporal (25%) + behavior (15%) heuristic; see ranking_method in case findings | Priority score, NOT a probability of responsibility; derived from TRAINING AIS |
| Investigation closure outcome | Directorate General of Shipping India; Tamil Nadu Coastal Police | 2017-03 | REAL (RECORDED) | Public record | Not possessed by PALEGIC; cited from public reporting only |
| Swedish Gothenburg AIS (data/source/ais-gothenburg-2017.gpkg) | MovingPandas example dataset | 2017 | REAL (RECORDED) — SEPARATE DATASET | Imported via prepare_ais.py | Must NOT be used as candidate vessels for the Ennore investigation; kept as a separate recorded-data demonstration |
| Deepwater Horizon slick polygons (data/source/dwh-2010-05-*.geojson) | NOAA/NESDIS/ERMA/SMU via GCOOS | 2010-05 | REAL (OBSERVED) — SEPARATE DATASET | NOAA public data; GCOOS as-is disclaimer | Separate historical case; not part of Ennore investigation |

## Provenance classes used (per specification)

| Class | Meaning | Used for |
|---|---|---|
| RECORDED | Primary sources — official records, confirmed facts | Collision event, vessel identity, investigation closure |
| OBSERVED | Direct sensor measurement | Sentinel-1A SAR acquisition (metadata only) |
| ILLUSTRATIVE | Derived from secondary sources for demonstration | Slick polygon, SAR detection mask |
| TRAINING | Constructed for workflow demonstration; is_synthetic=true | AIS track reconstructions |
| REANALYSIS | Gridded retrospective model product | ERA5 wind, CMEMS currents (schemas only — not loaded) |
| DERIVED | Output of PALEGIC algorithms applied to other data | rank_sources() priority score, candidate evidence flag |

## Integrity rules enforced

1. **AIS provenance_class=TRAINING** must propagate to the DB `tracks.provenance` JSONB column
2. **Metocean NOT_LOADED** — `particle_backtrack()` in `analytics.py` must not run on fictional constants for this case
3. **SAR detection_method=historical_validation_mask** — the UI must never claim AI detection was performed
4. **Swedish AIS separation** — `ais-gothenburg-2017.gpkg` tracks must not appear in the Ennore case ranking
5. **Running seed_ennore.py twice** must not duplicate any rows (ON CONFLICT DO NOTHING)
