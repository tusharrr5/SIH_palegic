# PALEGIC — Smart India Hackathon 2026 (Problem 26143)
# Mock, Fake, and Hardcoded Data Audit

**Problem Statement ID:** 26143  
**Problem Statement:** Leveraging satellite imagery to determine oil spills at sea along with AIS data correlations to identify the vessel responsible for the spill.  
**Repository Name:** PALEGIC (v2 Prototype)  
**Audit Date:** 2026-09-25  
**Policy Reminder:** DO NOT REMOVE THESE OCCURRENCES YET. Documented for planned replacement.  

---

## Executive Summary of Artificial Elements

While the prototype uses real historical vector polygons from NOAA/NESDIS (Deepwater Horizon 2010) and real historical AIS records from the Danish Maritime Authority (Gothenburg 2017), the **entire core connection between satellite oil spills and vessel attribution is synthetic, hardcoded, or heuristic-driven**.

Specifically:
1. **Zero Real Vessel-Spill Intersections:** In the Gulf of Mexico where oil spills exist, all candidate vessels are 100% fictional with programmatically generated coordinates. Where real vessels exist (Gothenburg), there is no oil spill.
2. **Zero Real Environmental Forcing:** Winds and currents are hardcoded constants across the entire ocean (`wind = [4.0, 2.0] m/s`, `current = [0.12, -0.06] m/s`).
3. **Pseudo-Random Particle Dispersion:** The drift sandbox seeds particles with fixed random seed 42 and normal distribution diffusion.
4. **Hardcoded Visuals:** Mini-slick icons on the dashboard are static hardcoded SVG paths that never change regardless of actual polygon geometry.

---

## Detailed Inventory of Mock, Fake & Hardcoded Elements

### Category 1: Fictional & Scripted AIS Trajectories

#### 1. Scripted Training Vessels (ALPHA, BRAVO, CHARLIE)
- **File:** `scripts/bootstrap.py`
- **Lines / Component:** Lines 129–170 (`bootstrap()`)
- **What is Mocked:**
  Programmatically generates 3 fictional vessel trajectories in the Gulf of Mexico starting at `2010-05-17T06:00:00Z`:
  - **Training vessel ALPHA (demo-1):** 25 waypoints, SOG drops from 11.4 kn to 1.8 kn between steps 7 and 14; COG turns from 70° to 165°; artificial gap injected by skipping steps 9–11 (90-minute gap).
  - **Training vessel BRAVO (demo-2):** Offset by +0.35° lon / +0.21° lat; constant 9.2 kn speed, constant 70° course.
  - **Training vessel CHARLIE (demo-3):** Offset by +0.90° lon / +0.54° lat; constant 9.2 kn speed, constant 70° course.
- **What the UI Claims it Represents:**
  In the Investigations workspace (`EvidencePanel.tsx`), these 3 vessels are presented as real-world candidate vessels that were in the vicinity of the Deepwater Horizon oil spill. Training vessel ALPHA is scored 74/100 and placed at the top of the suspect candidate ranking.

#### 2. Disconnected Gothenburg Historical Vessels (2017)
- **File:** `data/source/ais-replay.json`, `scripts/prepare_ais.py`
- **Lines / Component:** Lines 1–1035 (`ais-replay.json`), `prepare_ais.py:15-19`
- **What is Mocked / Fabricated in Context:**
  Three real commercial vessel passages (STENA JUTLANDICA, MAGNOLIA SEAWAYS, MARIT MAERSK) from Gothenburg, Sweden on 5 July 2017.
- **What the UI Claims it Represents:**
  In `ReplayWorkspace.tsx`, these tracks are presented in the "AIS Replay" workspace. A user naturally expects them to be vessels involved in or surrounding the oil spill investigation, but they are from Sweden in 2017—7 years after and 8,000 km away from the 2010 Gulf spill.

---

### Category 2: Mocked Environmental & Metocean Data

#### 3. Hardcoded Wind & Current Vector Fields
- **File:** `api/pelagic/analytics.py`
- **Lines / Component:** Lines 187–189 (`particle_backtrack()`)
- **Code:**
  ```python
  current = np.array([0.12, -0.06])
  wind = np.array([4.0, 2.0])
  drift = current + 0.03 * wind
  ```
- **What is Mocked:**
  Ocean currents and surface winds are hardcoded to constant, static numbers across the entire geographic expanse and for all time steps.
- **What the UI Claims it Represents:**
  In `EvidencePanel.tsx` (Transport tab), the UI displays:
  - *Current (east, north): 0.12, -0.06 m/s*
  - *Wind (east, north): 4, 2 m/s*
  - *Windage: 3%*
  This is presented as the environmental forcing driving the backward advection of oil particles.

---

### Category 3: Random Number Generation & Particle Dispersion

#### 4. Fixed Seed Random Normal Brownian Diffusion
- **File:** `api/pelagic/analytics.py`
- **Lines / Component:** Lines 172, 175–181, 201 (`particle_backtrack()`)
- **Code:**
  ```python
  rng = np.random.default_rng(seed)  # seed=42
  ...
  pos += drift * dt + rng.normal(0, sqrt(2 * k * abs(dt)), pos.shape)
  ```
- **What is Mocked:**
  The random dispersal of 160 particles backwards in time uses a fixed pseudo-random seed (`seed=42`) with standard normal distribution perturbations to simulate turbulent horizontal eddy diffusivity ($K = 8.0\text{ m}^2/\text{s}$).
- **What the UI Claims it Represents:**
  The UI displays a purple bounding envelope with dots and labels it *"Illustrative transport sandbox / possible origin spread"*.

---

### Category 4: Hardcoded Candidate Ranking & Heuristic Formula

#### 5. Arbitrary Priority Weights & Scoring Multipliers
- **File:** `api/pelagic/analytics.py`
- **Lines / Component:** Lines 133–140 (`rank_sources()`)
- **Code:**
  ```python
  proximity = exp(-d / 15)
  temporal = max(0, 1 - abs((timestamp(nearest["time"]) - at).total_seconds()) / 86400)
  behavior = min(sum(e["kind"] != "reporting_gap" for e in anomalies(pts)) / 2, 1)
  score = round(100 * (0.6 * proximity + 0.25 * temporal + 0.15 * behavior) * coverage)
  ```
- **What is Mocked:**
  The weights (0.60 Proximity, 0.25 Time, 0.15 Behavior) and decay constant ($15\text{ km}$) are arbitrarily chosen heuristic constants.
- **What the UI Claims it Represents:**
  In `EvidencePanel.tsx:255-258`, the score is displayed as an objective ranking: e.g. **74 / 100**, with breakdown bars for "Proximity 93", "Time overlap 82", and "Behavior 50".

#### 6. Hardcoded Anomaly Threshold Rules
- **File:** `api/pelagic/analytics.py`
- **Lines / Component:** Lines 32, 46, 60 (`anomalies()`)
- **What is Mocked:**
  - Gap threshold: exactly `45` minutes.
  - Slowdown threshold: initial SOG $\ge 8.0$ kn and final SOG $\le 3.0$ kn.
  - Course change threshold: heading delta $> 70^\circ$.
- **What the UI Claims it Represents:**
  Advanced maritime anomaly detection identifying suspicious maneuvering associated with illicit bilge or slop discharge.

---

### Category 5: Hardcoded Geometry & Geographic Labels

#### 7. Hardcoded Wellhead Origin Point
- **File:** `scripts/bootstrap.py`
- **Lines / Component:** Lines 109–115 (`bootstrap()`)
- **Code:**
  ```python
  "historical_source": {
      "name": "Macondo MC252 well",
      "lon": -88.3659,
      "lat": 28.7367,
      "status": "Documented historical source; not inferred by this prototype",
      "url": "https://response.restoration.noaa.gov/oil-and-chemical-spills/significant-incidents/deepwater-horizon-oil-spill",
  }
  ```
- **What is Mocked:**
  Hardcoded coordinates of the Deepwater Horizon Macondo wellhead.
- **What the UI Claims it Represents:**
  On the map, a `+` marker appears at this exact coordinate labeled *"Macondo MC252 well · documented historical source"*.

#### 8. Hardcoded Static Mini-Slick SVG Shape
- **File:** `apps/web/components/EvidencePanel.tsx`
- **Lines / Component:** Lines 104–109
- **Code:**
  ```tsx
  <div className="mini-slick">
    <svg viewBox="0 0 80 55" aria-hidden="true">
      <path d="M8 36 15 23 27 25 38 10 45 19 55 16 68 26 59 31 69 41 53 37 39 45 28 37 19 44Z" />
      <path d="m18 22 7-9 5 6-4 7Z" />
    </svg>
  </div>
  ```
- **What is Mocked:**
  A fixed, hardcoded SVG path polygon representing a generic oil slick.
- **What the UI Claims it Represents:**
  The visual shape thumbnail of the active surface anomaly. It displays the exact same static shape for 17 May, 19 May, and 20 May, regardless of the fact that the actual observations contain between 11 and 259 completely different polygons.

#### 9. Hardcoded Geographic City & Sea Markers
- **File:** `apps/web/components/OceanMap.tsx`
- **Lines / Component:** Lines 212–226
- **Code:**
  ```tsx
  for (const [label, lon, lat] of [
    ["NEW ORLEANS", -90.08, 29.96],
    ["LOUISIANA", -91.0, 30.4],
    ["MISSISSIPPI", -89.35, 30.7],
    ["FLORIDA", -85.2, 30.3],
    ["GULF OF MEXICO", -88.5, 27.1],
    ["GOTHENBURG", 11.97, 57.72],
    ["KATTEGAT", 11.4, 57.4],
  ])
  ```
- **What is Mocked:**
  Static text labels hardcoded into the map canvas via DOM Markers.
- **What the UI Claims it Represents:**
  Dynamic cartographic labeling.

#### 10. Hardcoded Map Center and Coordinates
- **File:** `apps/web/components/OceanMap.tsx`
- **Lines / Component:** Lines 86, 397–404
- **Code:**
  ```tsx
  center: [-88.4, 28.6]
  ...
  <span className="coordinate-value">28° 44′ N · 88° 22′ W</span>
  ```
- **What is Mocked:**
  Default map coordinate string permanently rendered at the top of the map.
- **What the UI Claims it Represents:**
  The current sensor coordinate center.

---

### Category 6: Hardcoded Statistics & Case Findings

#### 11. Hardcoded Overview Dashboard Metrics
- **File:** `apps/web/app/page.tsx`
- **Lines / Component:** Lines 330–369 (`overview-strip`)
- **What is Mocked:**
  - `03 Historical observations`
  - `316 Archived source polygons`
  - `Gulf of Mexico · Deepwater Horizon · 2010`
  - `NOAA / NESDIS via GCOOS`
- **What the UI Claims it Represents:**
  A live dashboard monitoring system overview.

#### 12. Synthetic Case ID Hashes
- **File:** `api/pelagic/main.py`
- **Lines / Component:** Lines 272–273
- **Code:**
  ```python
  seed = f"{body.path}:{body.exercise}:{track['id'] if track else ''}:{obs['id'] if obs else 'none'}"
  cid = "INV-" + hashlib.sha256(seed.encode()).hexdigest()[:8].upper()
  ```
- **What is Mocked:**
  Generates artificial case identifiers like `INV-8A4E93F1`.
- **What the UI Claims it Represents:**
  Official coast guard or maritime authority case docket numbers.
