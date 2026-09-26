# Source register

Downloaded 21 September 2026. Per-file source URLs, acquisition times, byte counts and SHA-256 values are in `data/source/manifest.json`.

## Historical oil-like polygons

**NOAA / NESDIS / ERMA / SMU, distributed by the Gulf of Mexico Coastal Ocean Observing System (GCOOS).** [Deepwaterhorizon Oilspill dataset compiled for GCOOS](https://www.arcgis.com/home/item.html?id=afafd2255f9d43bd8a5531de7e98c9a5).

| File | Service layer | Date | Original features |
|---|---:|---|---:|
| dwh-2010-05-17.geojson | 3 | 17 May 2010 | 11 |
| dwh-2010-05-19.geojson | 4 | 19 May 2010 | 46 |
| dwh-2010-05-20.geojson | 5 | 20 May 2010 | 259 |

The service identifies these as daily composites within a historical potential surface-oil anomaly product. Do not describe these as Sentinel-1 imagery or newly detected oil. Source metadata and service credit are retained. [GCOOS disclaimer](https://gcoos.org/disclaimer/) applies; data are supplied as-is, including restrictions on reliance for navigation. [NOAA incident background](https://response.restoration.noaa.gov/oil-and-chemical-spills/significant-incidents/deepwater-horizon-oil-spill).

This is an independently downloaded GCOOS-distributed NOAA dataset, not a Cerulean data export. Cerulean collection metadata was accessible, but slick feature requests required authorization; no private API or bypass was used.

## Basemap

[Natural Earth, 1:50m countries](https://www.naturalearthdata.com/about/terms-of-use/), public domain. Downloaded from the [Natural Earth vector repository](https://github.com/nvkelso/natural-earth-vector). Original countries are retained in `data/source/countries.geojson`. Browser geometry uses topology-preserving 0.012° simplification and stripped descriptive properties, solely for fast offline display. The map is not suitable for navigation or precise jurisdictional boundaries.

## AIS

Three synthetic trajectories authored for this prototype, CC0-1.0. Coordinates, course and speed are constructed programmatically for a labeled exercise. No real vessel identity, AIS provider output or real-world responsibility claim is included. Operator imports must provide a provider, license and synthetic flag; see the import contract.

## Reference concepts

[Aquintel](https://github.com/JDeepD/Aquintel): repository tree, README and entry page inspected. No reuse license was found in the inspected root; no source code was reused. The inspected role-in-query-string entry is not suitable as an authorization mechanism and was not adopted.

[SkyTruth Cerulean methods](https://skytruth.org/cerulean/methods/): consulted for polygon-centric UX, source association and AIS search concepts. No code, branding or design was copied. Cerulean data access was not available for feature downloads without authorization, so its data are not bundled. [SkyTruth terms](https://skytruth.org/terms-of-service/) were reviewed during reference assessment.

The previous local maritime-oil-intelligence repository was only inventoried for reference paths. No implementation, database, frontend, or architecture was migrated or reused.

## Recorded AIS replay: Gothenburg, 5 July 2017

The [MovingPandas source register](https://github.com/movingpandas/movingpandas-examples/blob/main/data/README.md) identifies `ais.gpkg` as a Danish Maritime Authority sample near Gothenburg. The unmodified 84,702-report GeoPackage is cached as `data/source/ais-gothenburg-2017.gpkg`; its SHA-256, retrieval time, upstream URL, source register and repository license are retained. The [DMA data management policy](https://www.dma.dk/safety-at-sea/navigational-information/ais-data/ais-data-management-policy-) describes historical open-data access, limits of liability and recipient obligations. DMA is the data provider; the MovingPandas repository's BSD-3-Clause notice does not replace the provider's data conditions.

`scripts/prepare_ais.py` creates `ais-replay.json` from three fixed commercial-vessel passage windows: STENA JUTLANDICA (MMSI 265410000, 08:00–11:00), MAGNOLIA SEAWAYS (219455000, 18:00–19:00), and MARIT MAERSK (219632000, 16:00–17:00), all on 5 July 2017. The pack has 104 retained reports. Last source row wins duplicate timestamps; retain the first report, each subsequent report at least 60 seconds later, and the final report. Coordinates and clock strings are unchanged; invalid/unavailable SOG/COG codes become null. Stationary reports are retained. Each point carries its original `source_fid`, and automated tests compare it directly to the GeoPackage.

The source clock strings do not include timezone metadata. The prototype explicitly interprets them as UTC and displays that assumption. It does not shift these tracks to 2010 or attach them to unrelated oil-spill cases. These are recorded AIS broadcasts, not independently validated vessel ground truth or evidence of pollution. The GeoPackage is an upstream subset, not a complete Danish AIS archive; missing reception may reflect upstream extraction.

Rebuild the replay JSON offline with `.venv/bin/python scripts/prepare_ais.py`; bootstrap verifies the manifest before inserting fixed track IDs idempotently. Do not silently replace existing investigations when refreshing source data.

## Detailed cached coastlines

The final basemap uses Natural Earth public-domain `ne_10m_land.geojson`, retained unmodified with a source checksum. Bootstrap simplifies it by 0.002 degrees with topology preservation for local rendering. The earlier 1:50m countries file is retained as a reference artifact. Coastlines are generalized geographic context, not harbor navigation charts or a shoreline impact model.
