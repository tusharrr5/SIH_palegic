# Historical AIS Retrieval — Ennore 2017

## Status: TRAINING / SYNTHETIC

The current AIS tracks for BW Maple and Dawn Kancheepuram are
**training reconstructions** (provenance: `TRAINING`). They are
illustrative positions derived from publicly documented collision
coordinates, NOT recorded AIS messages.

## How to Attempt Retrieval of Authentic Historical AIS

### Step 1: Identify the vessels

| Vessel | Type | IMO | Flag | Search aliases |
|---|---|---|---|---|
| BW Maple | LPG tanker | 9346537 | Singapore | `BW MAPLE` |
| Dawn Kancheepuram | Bulk carrier | 9368730 | India | `DAWN KANCHIPURAM`, `DAWN KANCHEEPURAM`, `DAWN KANCHIPURAM` |

### Step 2: Open data sources to try

#### Global Fishing Watch (GFW)
- URL: https://globalfishingwatch.org/map
- API: https://globalfishingwatch.org/our-apis/
- Search by MMSI or IMO within the Bay of Bengal region
- Time window: 2017-01-27 to 2017-01-30
- Note: GFW primarily tracks fishing vessels. Cargo/tanker coverage
  may be limited for 2017.

#### MarineTraffic (commercial)
- URL: https://www.marinetraffic.com/
- Historical AIS data requires a commercial API subscription
- Search by IMO: 9346537 (BW Maple), 9368730 (Dawn Kancheepuram)

#### VesselFinder (commercial)
- URL: https://www.vesselfinder.com/
- Historical track playback available on paid tiers

#### AISDB (open source)
- URL: https://aisdb.meridian.cs.dal.ca/
- Aggregated open AIS data — coverage varies by region

#### Danish Maritime Authority (AIS archive)
- URL: https://web.ais.dk/aisdata/
- Full historical AIS archive for Danish waters (not applicable
  for Bay of Bengal, but demonstrates the open-data model)

#### India-specific sources
- Directorate General of Shipping (DGS India) — AIS records may
  be obtainable under the Right to Information Act (RTI)
- INCOIS / ISRO — Indian coastal AIS archive
- Chennai Port Trust / Kamarajar Port Authority

### Step 3: If authentic positions are obtained

1. **Verify identity**: Confirm MMSI matches IMO via ITU ship station
   database or another authoritative source.

2. **Verify timestamps**: Ensure AIS position timestamps are monotonic
   and fall within the incident time window.

3. **Store separately**: Save the observed track in a new file:
   ```
   data/demo/ennore-2017/ais/observed_tracks.json
   ```
   Do NOT overwrite `tracks.json` (training data) until verification
   is complete.

4. **Set provenance**:
   ```json
   {
     "provenance_class": "OBSERVED",
     "is_synthetic": false,
     "source": "<provider name and retrieval method>",
     "retrieved_at": "<ISO 8601 timestamp>",
     "mmsi": "<verified MMSI>",
     "imo": <verified IMO>,
     "data_limitations": "<describe gaps, accuracy, coverage>"
   }
   ```

5. **Include in each position**:
   - `timestamp` (ISO 8601)
   - `latitude`, `longitude` (WGS84)
   - `sog` (speed over ground, knots)
   - `cog` (course over ground, degrees)
   - `source` (provider)

6. **Quality checks**:
   - Verify position timestamps are monotonic
   - Reject impossible coordinates (lat > 90, lon > 180)
   - Flag unrealistic speed jumps (> 30 knots between positions)
   - Preserve AIS gaps (do not interpolate)

### Step 4: Update the manifest

If observed tracks are verified and stored:
- Update `data/demo/ennore-2017/ais/provenance.json`:
  change `ais_data_status` to `OBSERVED`
- Update `data/demo/ennore-2017/manifest.json`:
  change `ais_tracks` status to `OBSERVED`
- Add the new file to the manifest's `files` array

### Current status

As of Phase 2B, no authenticated historical AIS positions have been
obtained for either vessel. The training reconstructions are retained
and correctly labelled.

| Vessel | Status | Provenance |
|---|---|---|
| BW Maple | Training reconstruction | `TRAINING` |
| Dawn Kancheepuram | Training reconstruction | `TRAINING` |

This is acceptable for the SIH 2026 demonstration. The training data
exists to demonstrate the PALEGIC attribution workflow, not to serve
as evidence.
