"""Derive a small replay pack from the retained, unmodified MovingPandas AIS sample.

No synthetic coordinates, resampling or removal of stationary reports. Each retained
point records its original GeoPackage fid. Clock strings have no offset: UTC is an
explicit interpretation, not a claim that the mirror supplies timezone metadata.
"""

from pathlib import Path
from datetime import datetime, timezone
import sqlite3, json, hashlib
from shapely import from_wkb

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/source/ais-gothenburg-2017.gpkg"
WINDOWS = [
    (265410000, "08:00:00", "11:00:00"),
    (219455000, "18:00:00", "19:00:00"),
    (219632000, "16:00:00", "17:00:00"),
]


def point_from_gpkg(blob):
    # GeoPackage binary header, followed by optional envelope and ordinary WKB.
    envelope_code = (blob[3] >> 1) & 7
    envelope_bytes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[envelope_code]
    return from_wkb(blob[8 + envelope_bytes :])


def derive():
    checksum = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    tracks = []
    with sqlite3.connect(f"file:{SOURCE}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        for mmsi, start, end in WINDOWS:
            rows = conn.execute(
                """SELECT * FROM aisdk_20170705_gothenburg2
                WHERE MMSI=? AND Timestamp>=? AND Timestamp<? ORDER BY Timestamp,fid""",
                (mmsi, "05/07/2017 " + start, "05/07/2017 " + end),
            ).fetchall()
            unique = {r["Timestamp"]: r for r in rows}  # Last fid wins ties.
            selected = []
            for r in unique.values():
                dt = datetime.strptime(r["Timestamp"], "%d/%m/%Y %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if selected and (dt - selected[-1][0]).total_seconds() < 60:
                    continue
                selected.append((dt, r))
            last = rows[-1]
            if selected[-1][1]["fid"] != last["fid"]:
                selected.append(
                    (
                        datetime.strptime(
                            last["Timestamp"], "%d/%m/%Y %H:%M:%S"
                        ).replace(tzinfo=timezone.utc),
                        last,
                    )
                )
            points = []
            for dt, r in selected:
                geo = point_from_gpkg(r["geom"])
                points.append(
                    dict(
                        time=dt.isoformat(),
                        lon=geo.x,
                        lat=geo.y,
                        sog=r["SOG"]
                        if r["SOG"] is not None and 0 <= r["SOG"] <= 102.2
                        else None,
                        cog=r["COG"]
                        if r["COG"] is not None and 0 <= r["COG"] < 360
                        else None,
                        source_fid=r["fid"],
                    )
                )
            name = next(r["Name"] for r in rows if r["Name"])
            tracks.append(
                dict(
                    id=f"recorded-dma-{mmsi}",
                    name=name,
                    synthetic=False,
                    points=points,
                    provenance=dict(
                        kind="recorded_archive",
                        provider="Danish Maritime Authority via MovingPandas",
                        description="Recorded vessel traffic near Gothenburg on 5 July 2017. No association with an oil release is claimed.",
                        mmsi=str(mmsi),
                        region="Gothenburg approaches, Sweden",
                        ship_type=next(
                            r["ShipType"] for r in rows if r["ShipType"] != "Undefined"
                        ),
                        url="https://github.com/movingpandas/movingpandas-examples/blob/main/data/README.md",
                        license="DMA historical open data; DMA data management policy applies. Mirror repository: BSD-3-Clause.",
                        license_url="https://www.dma.dk/safety-at-sea/navigational-information/ais-data/ais-data-management-policy-",
                        original_file=SOURCE.name,
                        source_sha256=checksum,
                        source_window=f"2017-07-05 {start}–{end}",
                        source_report_count=len(rows),
                        time_basis="Source clock strings interpreted as UTC; the GeoPackage has no timezone metadata.",
                        transformation="Fixed passage window; last fid per timestamp; retain first then reports >=60 s apart plus final report. Original coordinates and report times retained; AIS unavailable SOG/COG codes become null.",
                    ),
                )
            )
    return tracks


if __name__ == "__main__":
    tracks = derive()
    target = ROOT / "data/source/ais-replay.json"
    target.write_text(json.dumps(tracks, indent=2) + "\n")
    manifest_path = ROOT / "data/source/manifest.json"
    manifest = [
        e for e in json.loads(manifest_path.read_text()) if e["file"] != target.name
    ]
    content = target.read_bytes()
    manifest.append(
        dict(
            file=target.name,
            url=tracks[0]["provenance"]["url"],
            sha256=hashlib.sha256(content).hexdigest(),
            bytes=len(content),
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            feature_count=sum(len(t["points"]) for t in tracks),
            derived_from=SOURCE.name,
        )
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    for t in tracks:
        print(
            t["name"], len(t["points"]), t["points"][0]["time"], t["points"][-1]["time"]
        )
