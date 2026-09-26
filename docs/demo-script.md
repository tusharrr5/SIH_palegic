# Four-and-a-half-minute recording script

Run `.venv/bin/python scripts/preflight.py` first. Use the production build at approximately 1440 × 1000. Keep PostgreSQL, FastAPI and Next.js running. All demo assets are local; external source links are optional. Admin credentials are in README; other local credentials are in `.runtime/demo-accounts.json`. Start signed out.

| Time | Action | Suggested narration |
|---|---|---|
| 0:00–0:30 | Public Ocean watch: switch between 17, 19 and 20 May. | “These are real NOAA/NESDIS archived surface-anomaly polygons, with source records and area. Satellite interpretations retain uncertainty.” |
| 0:30–1:10 | Sign in as admin; AIS replay → STENA JUTLANDICA; press Play at 120×, pause, then click its reception gap. | “This is recorded Danish Maritime Authority traffic near Gothenburg in 2017. Source coordinates and times are retained. Interpolated positions are labeled; long gaps stay empty. These vessels are not linked to the Gulf spill.” |
| 1:10–1:45 | Investigations → New investigation → AIS first → Training vessel ALPHA → Create; Sources tab. | “A behavior flag initiates a satellite search. Here the vessel reports are explicitly fictional training data. Explainable ranking prioritizes leads, not findings of responsibility.” |
| 1:45–2:15 | New investigation → SAR first → Training exercise → 17 May → Create. | “The reverse trigger begins with slick geometry. Both paths use the same case, evidence, ranking and review workflow.” |
| 2:15–2:50 | Transport → Run illustrative backtrack; move the hour slider. | “Historical reconstruction requires verified forcing fields and timing. This separate sandbox demonstrates the transport equation under disclosed hypothetical inputs; it is not a hindcast of this incident.” |
| 2:50–3:20 | Review → Needs evidence; enter the note below; Save assessment; Export evidence. | “The investigator records uncertainty and missing evidence. Reviews are versioned and evidence exports are attributed.” |
| 3:20–4:30 | Administration → Add authority; fill a demo officer name, unique email and a password of at least 12 characters; create it. Show the new row, integrity checks and audit trail. Optionally sign in as that officer. | “Admins provision additional authority accounts. Officers can investigate and replay data; only administrators manage users and imports. Access is enforced by the backend.” |

Suggested review: “Training assessment: obtain incident-matched AIS and verified wind/current fields before considering attribution.”

Use a fresh demo-officer email for each recording, or reuse an account created earlier. Never narrate the real Gothenburg vessels as suspects. Password fields are masked; omit credential entry from a public video if desired. The bundled timestamp clock strings are explicitly interpreted as UTC because their mirrored GeoPackage has no timezone metadata.

For Indian waters, new SAR, AIS and metocean datasets require acquisition and validation. This pack is a verified historical demonstration, not a live Indian surveillance feed. The prototype consumes published slick interpretations; it does not claim fresh validated Sentinel-1 segmentation or an OpenOil hindcast.
