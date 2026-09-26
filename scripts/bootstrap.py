"""Idempotent bootstrap. Only creates a dedicated maritime_oil_v2* database."""

from pathlib import Path
import sys, os, json, secrets, uuid, datetime, argparse, hashlib, re

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
from pelagic.db import connection, init_schema
from pelagic.analytics import GEOD
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.types.json import Jsonb
from argon2 import PasswordHasher
from shapely.geometry import shape, mapping, MultiPolygon, LineString
from shapely import make_valid
from shapely.ops import unary_union


def bootstrap(rotate=False):
    for entry in json.loads((ROOT / "data/source/manifest.json").read_text()):
        actual = hashlib.sha256(
            (ROOT / "data/source" / entry["file"]).read_bytes()
        ).hexdigest()
        if actual != entry["sha256"]:
            raise RuntimeError("Source checksum mismatch: " + entry["file"])
    dsn = os.getenv("DATABASE_URL", "postgresql:///maritime_oil_v2")
    params = conninfo_to_dict(dsn)
    dbname = params.get("dbname", "")
    if not dbname.startswith("maritime_oil_v2"):
        raise RuntimeError(
            "Refusing bootstrap outside a dedicated maritime_oil_v2* database"
        )
    try:
        with psycopg.connect(
            make_conninfo(dsn, dbname="postgres"), autocommit=True
        ) as conn:
            if not conn.execute(
                "SELECT 1 FROM pg_database WHERE datname=%s", (dbname,)
            ).fetchone():
                conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    except Exception:
        # Target database may already exist or connection to 'postgres' is restricted
        pass
    init_schema()
    (ROOT / ".runtime").mkdir(exist_ok=True)
    credential_path = ROOT / ".runtime/demo-accounts.json"
    credentials = (
        json.loads(credential_path.read_text()) if credential_path.exists() else {}
    )
    hasher = PasswordHasher()
    with connection() as conn:
        for role, name in [
            ("authority", "Duty Officer"),
            ("admin", "System Administrator"),
            ("public", "Public Viewer"),
        ]:
            email = f"{role}@pelagic.local"
            existing = conn.execute(
                "SELECT id FROM users WHERE email=%s", (email,)
            ).fetchone()
            if not existing or rotate:
                password = secrets.token_urlsafe(15)
                if existing:
                    conn.execute(
                        "UPDATE users SET password_hash=%s WHERE id=%s",
                        (hasher.hash(password), existing["id"]),
                    )
                    conn.execute(
                        "DELETE FROM sessions WHERE user_id=%s", (existing["id"],)
                    )
                else:
                    conn.execute(
                        "INSERT INTO users(id,email,name,password_hash,role) VALUES(%s,%s,%s,%s,%s)",
                        (uuid.uuid4(), email, name, hasher.hash(password), role),
                    )
                credentials[email] = password
        for day in ["17", "19", "20"]:
            filename = f"dwh-2010-05-{day}.geojson"
            raw = json.loads((ROOT / "data/source" / filename).read_text())
            geom = unary_union(
                [make_valid(shape(f["geometry"])) for f in raw["features"]]
            )
            geom = MultiPolygon([geom]) if geom.geom_type == "Polygon" else geom
            source = {
                "provider": "NOAA / NESDIS / ERMA / SMU via GCOOS",
                "label": "Historical oil-like surface anomaly composite",
                "url": "https://www.arcgis.com/home/item.html?id=afafd2255f9d43bd8a5531de7e98c9a5",
                "license": "NOAA public data; GCOOS as-is disclaimer",
                "license_url": "https://gcoos.org/disclaimer/",
                "original_file": filename,
                "sensor": "NESDIS satellite composite; not Sentinel-1",
                "certainty": "Potential surface oil. Published historical interpretation; no fresh model inference.",
                "precision": "Day-level composite, not a single acquisition",
                "transformation": "WGS84 export and topology-preserving union; full original source features retained.",
            }
            gj = json.dumps(mapping(geom))
            oid = f"dwh-2010-05-{day}"
            conn.execute(
                """INSERT INTO observations(id,title,observed_at,temporal_precision,geometry,source,area_km2,polygon_count)
            VALUES(%s,%s,%s,'day',ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)),%s,ST_Area(ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)::geography)/1e6,%s) ON CONFLICT(id) DO NOTHING""",
                (
                    oid,
                    f"Deepwater Horizon · {day} May 2010",
                    f"2010-05-{day}T12:00:00Z",
                    gj,
                    Jsonb(source),
                    gj,
                    len(raw["features"]),
                ),
            )
            findings = {
                "historical_source": {
                    "name": "Macondo MC252 well",
                    "lon": -88.3659,
                    "lat": 28.7367,
                    "status": "Documented historical source; not inferred by this prototype",
                    "url": "https://response.restoration.noaa.gov/oil-and-chemical-spills/significant-incidents/deepwater-horizon-oil-spill",
                },
                "reconstruction_supported": False,
                "reason": "No time-matched wind/current fields are bundled. Daily composites do not determine release time.",
            }
            conn.execute(
                """INSERT INTO cases(id,title,trigger,observation_id,status,published,summary,findings) VALUES(%s,%s,'sar',%s,'needs_evidence',true,%s,%s) ON CONFLICT(id) DO NOTHING""",
                (
                    f"HIST-{day}05",
                    f"Deepwater Horizon · {day} May",
                    oid,
                    "Archived NOAA/NESDIS surface anomaly polygons from the Deepwater Horizon response. This daily composite records potential oil presence, not oil volume or a vessel attribution.",
                    Jsonb(findings),
                ),
            )
        for n, name, offset in [
            (1, "Training Vessel A", 0),
            (2, "Training vessel BRAVO", 0.35),
            (3, "Training vessel CHARLIE", 0.9),
        ]:
            if n == 1:
                points = [
                    {"time": "2010-05-17T06:00:00Z", "lon": -89.4500, "lat": 28.4200, "sog": 12.1, "cog": 70.0},
                    {"time": "2010-05-17T06:15:00Z", "lon": -89.3950, "lat": 28.4400, "sog": 12.1, "cog": 70.0},
                    {"time": "2010-05-17T06:25:00Z", "lon": -89.3583, "lat": 28.4533, "sog": 12.1, "cog": 70.0},
                    {"time": "2010-05-17T06:35:00Z", "lon": -89.3217, "lat": 28.4667, "sog": 12.1, "cog": 70.0},
                    {"time": "2010-05-17T06:42:00Z", "lon": -89.2960, "lat": 28.4760, "sog": 6.4, "cog": 72.0},
                    {"time": "2010-05-17T06:45:00Z", "lon": -89.2870, "lat": 28.4790, "sog": 3.0, "cog": 75.0},
                    {"time": "2010-05-17T06:48:00Z", "lon": -89.2820, "lat": 28.4800, "sog": 2.8, "cog": 155.0},
                    {"time": "2010-05-17T06:52:00Z", "lon": -89.2780, "lat": 28.4720, "sog": 2.4, "cog": 245.0},
                    {"time": "2010-05-17T06:56:00Z", "lon": -89.2840, "lat": 28.4690, "sog": 2.6, "cog": 335.0},
                    {"time": "2010-05-17T06:58:00Z", "lon": -89.2860, "lat": 28.4740, "sog": 3.1, "cog": 120.0},
                    {"time": "2010-05-17T07:00:00Z", "lon": -89.2800, "lat": 28.4770, "sog": 3.8, "cog": 68.0},
                    {"time": "2010-05-17T07:15:00Z", "lon": -89.2300, "lat": 28.4950, "sog": 8.5, "cog": 70.0},
                    {"time": "2010-05-17T07:30:00Z", "lon": -89.1700, "lat": 28.5150, "sog": 11.8, "cog": 70.0},
                    {"time": "2010-05-17T08:00:00Z", "lon": -89.0500, "lat": 28.5550, "sog": 12.1, "cog": 70.0},
                    {"time": "2010-05-17T08:30:00Z", "lon": -88.9300, "lat": 28.5950, "sog": 12.1, "cog": 70.0},
                    {"time": "2010-05-17T09:00:00Z", "lon": -88.8100, "lat": 28.6350, "sog": 12.1, "cog": 70.0},
                    {"time": "2010-05-17T10:00:00Z", "lon": -88.5700, "lat": 28.7150, "sog": 12.0, "cog": 70.0},
                    {"time": "2010-05-17T12:00:00Z", "lon": -88.0900, "lat": 28.8750, "sog": 12.1, "cog": 70.0},
                ]
            else:
                points = []
                start = datetime.datetime(2010, 5, 17, 6, tzinfo=datetime.timezone.utc)
                lon, lat = -89.5 + offset, 28.4 + offset * 0.6
                for k in range(25):
                    sog = 11.4 if k < 7 or k > 14 else 9.2
                    cog = 70
                    if k:
                        lon, lat, _ = GEOD.fwd(lon, lat, cog, sog * 1852 * 0.5)
                    points.append(
                        {
                            "time": (
                                start + datetime.timedelta(minutes=30 * k)
                            ).isoformat(),
                            "lon": round(lon, 6),
                            "lat": round(lat, 6),
                            "sog": sog,
                            "cog": cog,
                        }
                    )
            provenance = {
                "kind": "synthetic",
                "provider": "PELAGIC demonstration fixture",
                "license": "CC0-1.0",
                "label": "SYNTHETIC AIS · TRAINING DATA",
                "description": "Deterministic training vessel trajectory demonstrating speed reduction and loitering course anomaly. Not historical AIS or evidence of legal responsibility.",
            }
            conn.execute(
                """INSERT INTO tracks(id,name,provenance,points,geometry,synthetic) VALUES(%s,%s,%s,%s,ST_GeomFromText(%s,4326),true)
                ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name, points=EXCLUDED.points, provenance=EXCLUDED.provenance, geometry=EXCLUDED.geometry""",
                (
                    f"demo-{n}",
                    name,
                    Jsonb(provenance),
                    Jsonb(points),
                    LineString([(p["lon"], p["lat"]) for p in points]).wkt,
                ),
            )
        ais_first_findings = {
            "investigated_vessel": "Training Vessel A",
            "track_id": "demo-1",
            "trigger": "ais",
            "anomaly_coordinates": {"lat": 28.4770, "lon": -89.2800},
            "anomaly_window": "2010-05-17T06:42:00Z – 2010-05-17T07:00:00Z",
            "sar_verification_requested_at": "2010-05-17T07:02:00Z",
            "sar_search_radius_km": 25,
            "sar_observation_time": "2010-05-17T08:00:00Z",
            "slick_reveal_time": "2010-05-17T08:15:00Z",
            "attribution_score": 76,
            "candidate_status": "HIGH-PRIORITY CANDIDATE",
            "decision_support_notice": "Decision-support result. Requires analyst verification.",
            "why_flagged": [
                "Unusual speed reduction (12.1 kn → 6.4 kn → 3.2 kn at 06:42 UTC)",
                "Abnormal course behaviour and loitering-like movement (06:48–06:58 UTC)",
                "Anomaly occurred inside monitored investigation region (28.4770°N, 89.2800°W)",
                "Timing is compatible with subsequent satellite observation window",
                "Trajectory intersects spatial footprint of detected surface slick"
            ],
            "data_provenance": {
                "ais": "SYNTHETIC AIS · TRAINING DATA",
                "sar_slick": "HISTORICAL / ILLUSTRATIVE SURFACE ANOMALY COMPOSITE",
                "metocean": "ERA5/CMEMS NOT LOADED · TRANSPORT WITHHELD"
            }
        }
        conn.execute(
            """INSERT INTO cases(id,title,trigger,observation_id,track_id,exercise,summary,findings,status,published)
            VALUES('INV-6011ADAF','Training · AIS Vessel Anomaly Investigation','ais','dwh-2010-05-17','demo-1',true,%s,%s,'needs_evidence',true)
            ON CONFLICT(id) DO UPDATE SET title=EXCLUDED.title, trigger=EXCLUDED.trigger, track_id=EXCLUDED.track_id, observation_id=EXCLUDED.observation_id, summary=EXCLUDED.summary, findings=EXCLUDED.findings, published=true""",
            (
                "AIS surveillance flagged Training Vessel A exhibiting an unusual speed reduction followed by an abnormal heading loitering loop between 06:42 and 07:00 UTC. Targeted satellite verification identified an overlapping surface anomaly in subsequent SAR observation.",
                Jsonb(ais_first_findings),
            ),
        )
        for track in json.loads((ROOT / "data/source/ais-replay.json").read_text()):
            conn.execute(
                """INSERT INTO tracks(id,name,provenance,points,geometry,synthetic)
                VALUES(%s,%s,%s,%s,ST_GeomFromText(%s,4326),false) ON CONFLICT(id) DO NOTHING""",
                (
                    track["id"],
                    track["name"],
                    Jsonb(track["provenance"]),
                    Jsonb(track["points"]),
                    LineString([(p["lon"], p["lat"]) for p in track["points"]]).wkt,
                ),
            )
    credential_path.write_text(json.dumps(credentials, indent=2))
    credential_path.chmod(0o600)
    # User-requested local demo login; refreshed whenever bootstrap rotates it.
    admin_password = credentials.get("admin@pelagic.local")
    if admin_password:
        readme = ROOT / "README.md"
        block = (
            "<!-- LOCAL-DEMO-ADMIN -->\n"
            "| Admin ID / email | Password |\n| --- | --- |\n"
            f"| `admin@pelagic.local` | `{admin_password}` |\n"
            "<!-- /LOCAL-DEMO-ADMIN -->"
        )
        readme.write_text(
            re.sub(
                r"<!-- LOCAL-DEMO-ADMIN -->.*?<!-- /LOCAL-DEMO-ADMIN -->",
                lambda _: block,
                readme.read_text(),
                flags=re.S,
            )
        )
    countries = json.loads((ROOT / "data/source/land-10m.geojson").read_text())
    for feature in countries["features"]:
        feature["properties"] = {"name": feature["properties"].get("NAME", "")}
        feature["geometry"] = mapping(
            shape(feature["geometry"]).simplify(0.002, preserve_topology=True)
        )
    (ROOT / "apps/web/public/data/land.geojson").write_text(
        json.dumps(countries, separators=(",", ":"))
    )
    print(
        f"Ready: {dbname}. Local credentials: .runtime/demo-accounts.json (mode 0600)."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rotate-demo-passwords", action="store_true")
    args = parser.parse_args()
    bootstrap(args.rotate_demo_passwords)
