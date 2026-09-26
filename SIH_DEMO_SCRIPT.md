# PALEGIC — SIH 2026 Live Demonstration Script

**Problem Statement ID:** 26143  
**Problem Statement:** Leveraging satellite imagery to determine Oil spills at sea along with AIS data correlations to identify vessel responsible for the spill  
**Team:** Ekatva  
**System:** PALEGIC (Explainable Oil Spill Investigation & Vessel Attribution)  
**Canonical Demonstration Case:** `SIH-ENNORE-2017`  
**Duration:** 2 minutes 45 seconds (Target: 2–3 minutes)

---

## 0:00 – 0:20 | The Problem
> *"Respected Judges, when oil spills occur in coastal waters, maritime authorities face two fundamental challenges:*  
> *First, **the surface slick observed by satellite is almost never where the spill occurred** — currents and winds rapidly disperse oil miles away.*  
> *Second, **simple AIS proximity is misleading** — innocent ships pass by hours after release, while the actual discharging vessel may have already cleared port or disabled its AIS.*  
> *Authorities need an explainable, multi-modal evidence chain connecting satellite observations, vessel trajectories, and reconstructed origins."*

---

## 0:20 – 0:40 | The PALEGIC Solution
> *"This is **PALEGIC**. PALEGIC fuses Synthetic Aperture Radar (SAR) observations from Sentinel-1 with AIS vessel tracks and physical drift reconstruction to solve vessel attribution.*  
> *Critically, PALEGIC operates under two operational entry points:*  
> *1. **SAR-First** — when a satellite overpass detects a slick and we backtrack to identify candidate vessels.*  
> *2. **AIS-First** — when an AIS anomaly or report triggers an immediate search for surface pollution.*  
> *Let us launch the canonical benchmark: **SIH-ENNORE-2017**, the documented collision off Kamarajar Port, Chennai."*
>  
> *(Action: Click **RUN SIH DEMO**)*

---

## 0:40 – 1:10 | Satellite Observation + AIS Behavior
> *"The canonical investigation loads deterministically.*  
> *On the map, you immediately see five fused geospatial layers:*  
> *1. The **suspected surface slick** in amber, spanning 7 km².*  
> *2. The **Sentinel-1A SAR footprint** in cyan dashed outline, acquired by Copernicus Data Space Ecosystem.*  
> *3. The **AIS trajectories** of candidate vessels in the corridor.*  
> *4. In dashed red, **AIS transmission gaps exceeding 45 minutes**.*  
> *5. And in pulsing purple, the **documented collision origin zone**.*  
> *Notice our scientific honesty: the radar catalogue metadata is OBSERVED from ESA Copernicus, but our slick polygon is explicitly labeled ILLUSTRATIVE because no automated classifier should pretend a training mask is live AI."*
>  
> *(Action: Toggle the layer pills — SAR Footprint, AIS Gaps, Collision Origin)*

---

## 1:10 – 1:40 | Origin Reconstruction & Explainable Candidate Ranking
> *"Now we look at the right-hand evidence panel under **Sources**.*  
> *PALEGIC does not produce an arbitrary, black-box suspect. It calculates a multi-factor **Candidate Attribution Score** (0–100) based on spatial proximity, temporal compatibility, track relationship, and AIS transmission anomalies.*  
> *Ranked #1 is **BW Maple** (IMO 9346537, LPG Tanker) with a score of **51/100**.*  
> *Ranked #2 is **Dawn Kancheepuram** (IMO 9368730, Bulk Carrier) with a score of **50/100**.*  
> *Right beneath the rank, PALEGIC answers the critical question judges and maritime courts ask:*  
> ***'WHY IS THIS VESSEL RANKED FIRST?'***  
> *- Proximity: Vessel track passed within 0.0 km of the collision origin.*  
> *- Temporal overlap: Present precisely during the release window (07:45–08:30 UTC).*  
> *- Anomaly: Exhibits a 150-minute AIS transmission gap.*  
> *- Collision context: Official casualty reports confirm a ruptured bunker fuel tank."*
>  
> *(Action: Point to the 'WHY IS THIS VESSEL RANKED FIRST?' card)*

---

## 1:40 – 2:10 | Scientific Integrity & Transparent Uncertainty
> *"Unlike black-box AI demos that claim '99% confidence', PALEGIC's greatest strength is that **Uncertainty is Reported, Not Hidden**.*  
> *Under the **Evidence** tab:*  
> *- We report an **Origin Region** (±1.5 km maritime zone) rather than a false-precision point.*  
> *- We report an **Estimated Release Window** (2017-01-28 07:45–08:30 UTC) bounded by daily composite resolution.*  
> *- Because real-time ERA5 and CMEMS reanalysis grids are not loaded in this cached demonstration, physical hydrodynamic simulation is withheld to avoid false precision.*  
> *- Both vessels have verified AIS transmission gaps.*  
> *Every score is accompanied by the disclaimer: **'Decision-support output — analyst verification required.'**"*
>  
> *(Action: Click **Evidence** tab and scroll to Uncertainty & Transparency)*

---

## 2:10 – 2:40 | Interactive Investigation Replay
> *"Now let's examine the temporal dimension with **AIS Replay**.*  
> *This is not an animation loop. It is a deterministic, event-synchronized reconstruction scrubber.*  
> *As we click **Play** or scrub to 08:00 UTC:*  
> *- Vessel positions update dynamically.*  
> *- We witness BW Maple outbound from Ennore Port intersecting Dawn Kancheepuram inbound.*  
> *- The active event banner synchronizes: **'Vessel collision — BW Maple x Dawn Kancheepuram'**.*  
> *- We can accelerate to **2x** or **4x**, scrub backward to verify earlier positions, or click **Restart**.*  
> *The simulation is 100% deterministic — identical results on every scrub, with zero random values."*
>  
> *(Action: Click Play, switch to 2x, scrub the slider, and click Pause)*

---

## 2:40 – 3:00 | Timeline, Report Generation & Impact
> *"Finally, we view the **Timeline** tab with all 13 chronological investigation events, each carrying strict provenance badges: RECORDED, TRAINING, OBSERVED, and DERIVED.*  
> *With a single click on **Generate Investigation Report**, PALEGIC compiles a formal, 14-section **Marine Pollution Investigation Report** ready for Coast Guard command, Port Authorities, or maritime courts.*  
> *The report includes complete incident metrics, satellite metadata, AIS gap logs, candidate scoring rationale, uncertainty caveats, and a one-click **Print / Export PDF** capability.*  
> *PALEGIC transforms fragmented maritime data into court-defensible, explainable maritime intelligence.*  
> *Thank you. We welcome your questions."*
>  
> *(Action: Click **Generate Investigation Report**, scroll through the sections, and show Print / Export PDF)*
