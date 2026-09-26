# Ennore 2017 — Canonical Incident Package

**Incident ID:** SIH-ENNORE-2017  
**Status:** Historical Validation Investigation  
**Demo ready:** ✅ Yes (with illustrative/training data clearly labelled)

## Incident summary

On **28 January 2017**, LPG tanker **BW Maple** (IMO 9346537, Singapore) and bulk carrier **Dawn Kancheepuram** (IMO 9368730, India) collided approximately 1.5 nm east of **Ennore Port** (Kamarajar Port), Tamil Nadu. The collision released an estimated **196 tonnes of fuel oil**, which reached approximately **35 km of Chennai coastline**.

A **Sentinel-1A SAR acquisition** on **29 January 2017 ~04:30 UTC** captured the surface oil anomaly. This case serves as PALEGIC's canonical SIH 2026 demonstration.

## Data status

| Layer | Status | Provenance class |
|---|---|---|
| Incident identity | ✅ Complete | RECORDED |
| SAR scene metadata | ✅ Complete (raster not downloaded) | OBSERVED |
| Oil slick polygon | ⚠️ Illustrative | ILLUSTRATIVE |
| AIS — BW Maple | ⚠️ Training reconstruction | TRAINING |
| AIS — Dawn Kancheepuram | ⚠️ Training reconstruction | TRAINING |
| ERA5 wind | ❌ Not loaded | REANALYSIS |
| CMEMS currents | ❌ Not loaded | REANALYSIS |
| Master timeline | ✅ Complete | Mixed (per event) |
| Evidence bundle | ✅ Complete | Mixed (per item) |

## Critical honesty rules

1. **AIS tracks** — labelled `TRAINING / is_synthetic: true`. The UI must display `"Training AIS reconstruction"`. Never `"Recorded AIS"`.
2. **Slick polygon** — labelled `ILLUSTRATIVE / detection_method: historical_validation_mask`. Never claim AI/ML detection was performed.
3. **Metocean** — ERA5 and CMEMS data not loaded. The application must display `"Historical environmental forcing not loaded"` and must NOT silently fall back to fictional constants.
4. **Swedish AIS** (`data/source/ais-gothenburg-2017.gpkg`) — a separate recorded-data demonstration. Must NOT appear as candidate vessels in the Ennore investigation.

## Acquiring the SAR raster

See `sar/README.md`.

## Acquiring ERA5 wind data

```bash
python scripts/fetch_era5_wind.py --incident SIH-ENNORE-2017
# Requires ~/.cdsapirc with CDS API key
# https://cds.climate.copernicus.eu/
```

## Acquiring CMEMS current data

```bash
python scripts/fetch_cmems_currents.py --incident SIH-ENNORE-2017
# Requires CMEMS credentials
# https://marine.copernicus.eu/
```

## Seeding into the database

```bash
python scripts/seed_ennore.py
# Idempotent — safe to run twice
```

## Public sources

- The Hindu: https://www.thehindu.com/news/national/tamil-nadu/ennore-oil-spill-a-disaster-caused-by-vessels-bw-maple-and-dawn-kancheepuram/article17752024.ece
- ITOPF: https://www.itopf.org/
- Kamarajar Port Authority press releases
- NRSC/ISRO satellite-imagery-derived media reports
