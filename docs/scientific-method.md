# Scientific method and uncertainty

## Observation truth

The cached geometry is NOAA/NESDIS potential surface-oil anomaly data distributed by GCOOS. Dates represent daily composites, with noon UTC used internally only as a day reference. The interface displays day-level timing. These data can contain look-alikes; no chemical composition, thickness, volume, age, or new segmentation-model confidence is inferred. Geometry is exported in WGS84, made valid if necessary, unioned per day, and measured with PostGIS geography area. Original features are retained without simplification. Only the Natural Earth basemap is simplified.

## AIS and behavior

Reports are sorted by UTC timestamp; the last duplicate timestamp wins. Input limits reject invalid coordinates, non-finite values, impossible supplied SOG/COG ranges, missing timezone and oversized trajectories. The provided three trajectories are geodesically generated fictional exercises with invented names; no MMSI or identity from a real vessel is attached.

Behavior flags are transparent thresholds: a reporting gap >45 minutes; SOG dropping from ≥8 to ≤3 knots within ≤45 minutes; circular course difference >70° within ≤45 minutes. These may reflect benign operations or reception effects. A gap never becomes a positive suspiciousness component in ranking. These are explainable heuristics, not a trained anomaly model or benchmarked detector. Implied kinematic outliers in imported coordinates are not currently corrected.

Replay uses WGS84 ellipsoidal geodesic interpolation between reports at most 45 minutes apart. There is no extrapolation outside the received trajectory and no interpolated ship marker inside a larger gap. The map draws separate segments on either side of the gap.

## Source ranking

Only reports inside ±24 hours of the day reference are considered. Distances are measured from received report locations to the polygon in a local azimuthal equidistant projection. Candidates farther than 100 km are excluded.

`priority = round(100 × (0.60 P + 0.25 T + 0.15 B) × C)`

- `P = exp(−distance_km / 15)`.
- `T = max(0, 1 − |closest_report_time − day_reference| / 24h)`.
- `B = min(non-gap behavior flag count / 2, 1)`.
- `C = max(0, 1 − excess_inter_report_minutes / observed_span_minutes)`, where excess is time above a 30-minute expected reporting interval. A single report has zero coverage.

Weights and thresholds are fixed prototype choices, not validated attribution probabilities. The 30-minute coverage assumption is for the sparse demo pack and needs provider-specific configuration for operational AIS. Proximity to a large daily composite is weak causal evidence; the interface makes no responsibility finding. The real Macondo source is displayed as documented historical context with a NOAA citation, separately from algorithmic candidate scores.

## Physics

Historical reconstruction is gated off without verified acquisition timing and time-matched current and wind fields. No ERA5, CMEMS, HYCOM or OpenOil output is silently substituted.

The exercise-only sandbox runs 160 particles with fixed random seed 42, a 900-second step, windage 0.03 and horizontal diffusivity 8 m²/s. It solves:

`Δx = (u_current + 0.03 u_wind) Δt + sqrt(2 K |Δt|) N(0,1)`

Current `(east, north) = (0.12, −0.06) m/s`; wind `(4, 2) m/s`. Negative timesteps reverse advection; random diffusion remains positive. Particles start uniformly by area in a local projection of the mapped polygon. The hull displays ensemble spread, not a calibrated confidence interval or a unique origin zone.

This illustration has no weathering, oil chemistry, shoreline stranding, vertical mixing, Stokes drift, oil mass, time-varying forcing or validation against an independent observation. It is not a forecast, historical reconstruction, or OpenOil run. OpenDrift/OpenOil integration is deferred until the required forcing and a defensible benchmark are available.

References: [MapLibre API](https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/), [OpenDrift OpenOil implementation](https://opendrift.github.io/_modules/opendrift/models/openoil/openoil.html), [BAKTRAK paper](https://arxiv.org/abs/1111.0756).

## Recorded trajectory replay

The dedicated AIS library uses the same server-side WGS84 interpolation as case replay. Authorities and admins can select published recorded, operator-imported or explicitly synthetic tracks. Playback never extrapolates outside a track's range and leaves gaps over 45 minutes empty. Last-received SOG/COG remains labeled as reported telemetry; it is not an interpolated measurement. Bundled source times are interpreted as UTC because the mirror lacks timezone metadata. Source rows, transformations and checksums are retained; see `sources.md`.
