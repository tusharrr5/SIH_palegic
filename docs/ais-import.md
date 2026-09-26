# AIS JSON import

Admin → Select AIS JSON, or `POST /api/admin/ais` with an authenticated admin cookie and the configured Origin header. A file contains one trajectory and 2–5,000 reports; the browser caps files at 2 MB. Coordinates are `[longitude, latitude]` in EPSG:4326; speed is knots and course is degrees clockwise from north. UTC offsets are mandatory. SOG and COG can be null when unavailable.

```json
{
  "name": "Example training track",
  "provider": "Locally authored demonstration",
  "license": "CC0-1.0",
  "synthetic": true,
  "points": [
    {"time":"2010-05-17T10:00:00Z","lon":-88.7,"lat":28.5,"sog":10,"cog":70},
    {"time":"2010-05-17T10:30:00Z","lon":-88.68,"lat":28.51,"sog":1.8,"cog":160},
    {"time":"2010-05-17T12:00:00Z","lon":-88.65,"lat":28.50,"sog":2,"cog":165}
  ]
}
```

Set `synthetic:false` only for recorded data that you are authorized to use, and provide its actual source and license. The app labels imported recorded data as operator-declared and unverified. Upload does not validate provider authenticity or create an accusation. Do not use real vessel names on synthetic tracks. The example above is deliberately synthetic, with illustrative kinematics.

Reports are sorted and duplicate timestamps are deduplicated with the last entry winning. Uploading the identical trajectory and provenance again returns the same ID. AIS-first requires a supported behavior anomaly; a trajectory without a flag does not manufacture a case. With no cached SAR match the result is explicitly “needs evidence.”

After importing, open **AIS replay** and select the new trajectory. Recorded imports appear under Recorded AIS; fictional imports appear under Training AIS. Imported provenance remains operator-declared. Replay does not require a detected anomaly or a SAR match.
