# PALEGIC — Smart India Hackathon 2026 (Problem 26143)
# Interactive Elements & Button Audit

**Problem Statement ID:** 26143  
**Problem Statement:** Leveraging satellite imagery to determine oil spills at sea along with AIS data correlations to identify the vessel responsible for the spill.  
**Repository Name:** PALEGIC (v2 Prototype)  
**Audit Date:** 2026-09-25  

---

## Executive Summary

Every button, link, form submission, and map interaction across all views (`public`, `authority`, `admin`, `replay`) has been inspected to verify whether it performs its claimed action against the backend API or merely simulates functionality.

### Key Findings:
1. **Zero Dead Buttons:** There are no completely non-responsive `onClick={() => {}}` dead-end buttons in the main navigation and workflow.
2. **Replay & Playback are Genuine:** The Play/Pause/Scrub buttons actually trigger dynamic temporal queries against the FastAPI backend, which performs server-side geodesic interpolation.
3. **No Automatic "Analyze / Detect" Button on Upload:** There is no button to upload raw satellite imagery and automatically run detection. Detection is limited to selecting from pre-existing cached observations or tracks.
4. **Historical Hindcast Mode is Intentionally Blocked:** While the UI allows selecting "Run illustrative backtrack", requesting an actual historical hindcast is rejected by the server with an HTTP 409 error.
5. **Report Generation is JSON Only:** The "Export evidence" button exports raw structured JSON rather than a human-readable or printable PDF dossier.

---

## Detailed Button & Interaction Audit Table

| BUTTON / INTERACTION | COMPONENT & FILE:LINE | EXPECTED ACTION | ACTUAL ACTION | STATUS |
|---|---|---|---|---|
| **Ocean watch** | `apps/web/app/page.tsx:218` | Switch to public observatory view showing satellite archive | Sets `view = "public"`. Fetches `/api/public/cases` and renders historical Deepwater Horizon daily composites. | **WORKING** |
| **Investigations** | `apps/web/app/page.tsx:225` | Enter authority investigation workspace | If authenticated as authority/admin, switches `view = "authority"`. If unauthenticated, opens `LoginDialog`. | **WORKING** |
| **Administration** | `apps/web/app/page.tsx:233` | Enter administrative panel | Visible only to `admin` role. Sets `view = "admin"` and renders `AdminView`. | **WORKING** |
| **AIS replay** | `apps/web/app/page.tsx:242` | Open recorded AIS trajectory player | Sets `view = "replay"` and loads `ReplayWorkspace` with Gothenburg 2017 recorded tracks. | **WORKING** |
| **Sign out** | `apps/web/app/page.tsx:264` | Log out and revoke active session | Calls `POST /api/auth/logout`. Deletes session hash in PostgreSQL, clears cookie, resets state to public view. | **WORKING** |
| **Authority sign in** | `apps/web/app/page.tsx:282` | Open authentication dialog | Sets `login = true`, opening modal dialog to enter email/password. | **WORKING** |
| **Sign in (Submit)** | `apps/web/components/Dialogs.tsx:111` | Authenticate user credentials | Calls `POST /api/auth/login`. Verifies Argon2 password hash. Sets HttpOnly session cookie on success. | **WORKING** |
| **New investigation** | `apps/web/app/page.tsx:314` | Open modal to initiate new case | Sets `detection = "ais"`, displaying `DetectionDialog` with AIS-first preselected. | **WORKING** |
| **AIS first (Dialog tab)** | `apps/web/components/Dialogs.tsx:154` | Choose AIS anomaly trigger path | Sets `path = "ais"`. Displays dropdown of available AIS tracks. | **WORKING** |
| **SAR first (Dialog tab)** | `apps/web/components/Dialogs.tsx:163` | Choose satellite observation trigger path | Sets `path = "sar"`. Displays dropdown of historical observations. | **WORKING** |
| **Training exercise (Checkbox)** | `apps/web/components/Dialogs.tsx:171` | Toggle between training synthetic data and real records | Toggles `exercise` boolean state. Updates track selector between synthetic (ALPHA/BRAVO/CHARLIE) and recorded tracks. | **WORKING** |
| **Create investigation** | `apps/web/components/Dialogs.tsx:226` | Create new investigation case | Calls `POST /api/detections`. Creates case record in PostGIS, performs spatial buffer search, and opens case file. | **WORKING** |
| **Archive date buttons** (17, 19, 20 May) | `apps/web/app/page.tsx:641-650` | Switch active historical observation date | Updates `selected` case ID. Re-fetches observation geometry and re-centers MapLibre camera. | **WORKING** |
| **Case rail search input** | `apps/web/app/page.tsx:384` | Filter list of cases by title or ID | Updates `query` state. Filters local `cases` array by text match. | **WORKING** |
| **Case rail filter tabs** (All, AIS, SAR, Training) | `apps/web/app/page.tsx:402-409` | Filter case cards by trigger type | Updates `filter` state to `'all'`, `'ais'`, `'sar'`, or `'training'`. | **WORKING** |
| **Case card item** | `apps/web/app/page.tsx:429` | Select and open a specific case file | Calls `setSelected(id)`. Fetches full case details (`/api/cases/{id}` or `/api/public/cases/{id}`). | **WORKING** |
| **AIS first (Rail footer)** | `apps/web/app/page.tsx:481` | Quick-start AIS anomaly workflow | If signed in, opens `DetectionDialog` with `initial="ais"`. If signed out, opens login modal. | **WORKING** |
| **SAR first (Rail footer)** | `apps/web/app/page.tsx:495` | Quick-start SAR slick workflow | If signed in, opens `DetectionDialog` with `initial="sar"`. If signed out, opens login modal. | **WORKING** |
| **Surface anomaly (Map pill)** | `apps/web/app/page.tsx:517` | Toggle visibility of oil slick layer | Toggles `showSlick`. MapLibre sets layout visibility of `slick-fill`, `slick-line`, `slick-glow` to `visible`/`none`. | **WORKING** |
| **AIS tracks (Map pill)** | `apps/web/app/page.tsx:526` | Toggle visibility of AIS track lines | Toggles `showTracks`. MapLibre updates track GeoJSON source and vessel markers. | **WORKING** |
| **Play / Pause (Case Replay)** | `apps/web/app/page.tsx:572` | Animate vessel movements over time | Toggles `playing`. Starts/stops 700ms timer advancing time by +15 minutes per tick. | **WORKING** |
| **Reset (Case Replay)** | `apps/web/app/page.tsx:586` | Reset case playback to starting timestamp | Sets `time = timeRange[0]` and stops playback timer. | **WORKING** |
| **Timeline Range Slider** | `apps/web/app/page.tsx:598` | Scrub case playback to specific time | Updates `time` state. Triggers `GET /api/cases/{id}/replay?at=...` to fetch interpolated vessel positions. | **WORKING** |
| **Evidence Tab** | `apps/web/components/EvidencePanel.tsx:72` | View incident overview and slick metrics | Sets active tab to "Evidence". Displays polygon area, facts grid, and evidence chain. | **WORKING** |
| **Sources Tab** | `apps/web/components/EvidencePanel.tsx:72` | View candidate vessels and ranking | Sets active tab to "Sources". Displays ranked candidate list with heuristic score bars. | **WORKING** |
| **Transport Tab** | `apps/web/components/EvidencePanel.tsx:72` | View drift simulation & backtrack sandbox | Sets active tab to "Transport". Displays required metocean fields and illustrative sandbox runner. | **WORKING** |
| **Review Tab** | `apps/web/components/EvidencePanel.tsx:72` | Record officer assessment and review history | Sets active tab to "Review". Displays form to update status and add versioned review note. | **WORKING** |
| **Candidate source item** | `apps/web/components/EvidencePanel.tsx:242` | Highlight suspect vessel | Sets `selectedTrack = id`. Expands component score breakdown and highlights vessel marker on map. | **WORKING** |
| **Run illustrative backtrack** | `apps/web/components/EvidencePanel.tsx:372` | Simulate backward Lagrangian drift | Calls `POST /api/cases/{id}/reconstruction` with `mode="illustrative"`. Renders 160 particles and convex hull. | **WORKING (Toy Sandbox)** |
| **Hours before slider** | `apps/web/components/EvidencePanel.tsx:407` | Scrub backwards through drift time steps | Updates `driftFrame` (0 to 6 hours before). MapLibre updates particle positions and convex hull envelope. | **WORKING** |
| **Clear transport layer** | `apps/web/components/EvidencePanel.tsx:441` | Remove particle visualization from map | Sets `reconstruction = null`. Clears particle and envelope layers on MapLibre map. | **WORKING** |
| **Save assessment (Review form)** | `apps/web/components/EvidencePanel.tsx:514` | Commit official assessment to audit trail | Calls `POST /api/cases/{id}/reviews`. Uses optimistic locking (`expected_version`). Updates status and appends note. | **WORKING** |
| **Export evidence JSON** | `apps/web/components/EvidencePanel.tsx:552` | Download legal evidence package | Native download link to `/api/cases/{id}/export`. Downloads audit-stamped `pelagic-evidence/1` JSON file. | **PARTIALLY WORKING (No PDF)** |
| **Open original dataset link** | `apps/web/components/EvidencePanel.tsx:206` | View upstream source reference | Opens NOAA/GCOOS ArcGIS source URL in new browser tab. | **WORKING** |
| **Dataset selector (Replay)** | `apps/web/components/ReplayWorkspace.tsx:169` | Filter replay tracks by type | Filters trajectory list between "Recorded AIS", "Training AIS", and "All trajectories". | **WORKING** |
| **Trajectory selection item** | `apps/web/components/ReplayWorkspace.tsx:197` | Select vessel for recorded playback | Sets `selected = id`. Fetches track points (`/api/tracks/{id}`) and resets clock to voyage start. | **WORKING** |
| **Play / Pause (Recorded Replay)** | `apps/web/components/ReplayWorkspace.tsx:264` | Play recorded passage animation | Toggles playback. 500ms timer advances timestamp by `speed * 1000` ms. | **WORKING** |
| **Restart (Recorded Replay)** | `apps/web/components/ReplayWorkspace.tsx:277` | Rewind passage to first received report | Sets `time = start` and stops playback. | **WORKING** |
| **Recorded Scrubber Slider** | `apps/web/components/ReplayWorkspace.tsx:288` | Scrub recorded voyage time | Updates `time`. Triggers `GET /api/tracks/{id}/replay?at=...` to query geodesic interpolation. | **WORKING** |
| **Replay Speed Dropdown** | `apps/web/components/ReplayWorkspace.tsx:301` | Adjust playback multiplier | Updates `speed` state between 30×, 120×, and 600×. | **WORKING** |
| **Reception gap jump button** | `apps/web/components/ReplayWorkspace.tsx:373` | Jump directly into an AIS transmission gap | Sets `time` to the midpoint of the gap (`Date.parse(from) + Date.parse(to)) / 2`. Updates UI to show "No position in this interval". | **WORKING** |
| **Admin Refresh button** | `apps/web/components/AdminView.tsx:41` | Refresh system admin dashboard | Calls `GET /api/admin/overview`. Re-verifies SHA-256 checksums of all source files on disk. | **WORKING** |
| **Add authority toggle** | `apps/web/components/AdminView.tsx:126` | Toggle officer account creation form | Toggles `adding = !adding` state, expanding or collapsing the account provisioning form. | **WORKING** |
| **Create authority account** | `apps/web/components/AdminView.tsx:203` | Provision new officer user account | Calls `POST /api/admin/authorities`. Validates email and $\ge 12$ char password, creates Argon2 hash, saves to DB. | **WORKING** |
| **Role change select** | `apps/web/components/AdminView.tsx:218` | Change user authorization role | Calls `PATCH /api/admin/users/{id}/role`. Updates role and immediately revokes all active sessions for that user. | **WORKING** |
| **Select AIS JSON upload** | `apps/web/components/AdminView.tsx:289` | Ingest new AIS trajectory JSON | Opens OS file dialog. Validates JSON payload, calls `POST /api/admin/ais`, inserts into PostGIS `tracks` table. | **WORKING** |
| **Zoom in / out / fit controls** | `apps/web/components/OceanMap.tsx:407-427` | Pan and zoom map camera | Calls MapLibre `zoomIn()`, `zoomOut()`, and `fitBounds()` to re-center on active slick or vessel tracks. | **WORKING** |
| **Vessel Marker Click** | `apps/web/components/OceanMap.tsx:321` | Select vessel directly on map | Calls `onSelectTrack(t.id)`. Automatically switches right panel to "Sources" tab and highlights vessel metrics. | **WORKING** |

---

## Detailed Investigation of Missing or Claimed Buttons

### 1. "Analyze / Detect" Button on Satellite Imagery
- **Status:** **MISSING**
- **Analysis:** In an end-to-end oil spill detection solution, judges expect a button such as **"Analyze Satellite Scene"** or **"Run SAR Oil Detector"** that accepts a raw Sentinel-1 GRD image or coordinates and runs an automated segmentation algorithm. In this repository, the "Detect" action (`POST /api/detections`) simply queries pre-existing database records.

### 2. "Run Historical Hindcast" Button
- **Status:** **BROKEN / INTENTIONALLY GATED**
- **Analysis:** If a client attempts to execute a historical hindcast via `POST /api/cases/{case_id}/reconstruction` with `mode: "historical"`, the backend explicitly responds with an HTTP 409 error: *"Historical reconstruction unavailable: verified wind/current fields and acquisition timing are required."*

### 3. "Generate PDF Report" Button
- **Status:** **MISSING**
- **Analysis:** The "Export evidence" button downloads a raw `.json` file (`pelagic-evidence/1`). There is no button or service to compile a visual, court-ready PDF dossier.
