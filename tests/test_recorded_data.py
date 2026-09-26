"""Check the cached replay against the actual source, not a generated trajectory."""

import json, sqlite3, sys, hashlib
from datetime import datetime
from pelagic.db import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
from prepare_ais import point_from_gpkg, derive


def test_every_recorded_point_matches_retained_source():
    source = ROOT / "data/source/ais-gothenburg-2017.gpkg"
    tracks = json.loads((ROOT / "data/source/ais-replay.json").read_text())
    assert tracks == derive()
    with sqlite3.connect(source) as conn:
        conn.row_factory = sqlite3.Row
        assert (
            conn.execute("SELECT count(*) FROM aisdk_20170705_gothenburg2").fetchone()[
                0
            ]
            == 84702
        )
        for track in tracks:
            assert (
                track["provenance"]["source_sha256"]
                == hashlib.sha256(source.read_bytes()).hexdigest()
            )
            for p in track["points"]:
                raw = conn.execute(
                    "SELECT * FROM aisdk_20170705_gothenburg2 WHERE fid=?",
                    (p["source_fid"],),
                ).fetchone()
                geo = point_from_gpkg(raw["geom"])
                assert (p["lon"], p["lat"]) == (geo.x, geo.y)
                assert (
                    datetime.fromisoformat(p["time"]).strftime("%d/%m/%Y %H:%M:%S")
                    == raw["Timestamp"]
                )
                assert str(raw["MMSI"]) == track["provenance"]["mmsi"]
