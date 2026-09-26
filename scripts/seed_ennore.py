"""Idempotent seed: import the SIH-ENNORE-2017 canonical incident package into the existing DB.

Usage:
    python scripts/seed_ennore.py [--dry-run]

Running this script twice will NOT create duplicate rows (ON CONFLICT DO NOTHING).
Only creates or updates the Ennore case — existing datasets are untouched.
"""

import sys
import os
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from pelagic.db import connection
from psycopg.types.json import Jsonb
from shapely.geometry import shape, mapping, MultiPolygon, LineString
from shapely import make_valid
from shapely.ops import unary_union

PACKAGE = ROOT / "data/demo/ennore-2017"
CASE_ID = "SIH-ENNORE-2017"
OBS_ID = "ennore-obs-2017-01-29"


def load_json(path):
    return json.loads((PACKAGE / path).read_text())


def seed(dry_run=False):
    manifest = load_json("manifest.json")
    incident = load_json("incident.json")
    spill = load_json("spill/observed_slick.geojson")
    sar_meta = load_json("sar/scene_metadata.json")
    detection_meta = load_json("spill/detection_metadata.json")
    ais_data = load_json("ais/tracks.json")
    ais_prov = load_json("ais/provenance.json")
    timeline = load_json("timeline/events.json")
    evidence = load_json("evidence/evidence.json")

    print(f"Seeding {CASE_ID} — {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"  Package version: {manifest['version']}")
    print(f"  Demo ready: {manifest['demo_ready']}")
    print()

    # ── Build spill geometry ────────────────────────────────────────────────
    features = spill["features"]
    geom = unary_union(
        [make_valid(shape(f["geometry"])) for f in features]
    )
    if geom.geom_type == "Polygon":
        geom = MultiPolygon([geom])
    elif geom.geom_type == "MultiPolygon":
        pass  # already correct
    else:
        geom = MultiPolygon(list(geom.geoms) if hasattr(geom, "geoms") else [geom])

    geom_gj = json.dumps(mapping(geom))
    area_km2 = float(
        spill["features"][0]["properties"].get("area_km2_approx", 4.2)
    )
    polygon_count = len(features)

    # ── Build observation source metadata ───────────────────────────────────
    obs_source = {
        "provider": "Sentinel-1A / ESA Copernicus (scene metadata only); slick polygon: ILLUSTRATIVE",
        "label": "Surface oil anomaly — Ennore coast, 29 January 2017",
        "detection_method": detection_meta["detection_method"],
        "detection_method_note": detection_meta["detection_method_note"],
        "provenance_class": detection_meta["provenance_class"],
        "is_illustrative": True,
        "sar_platform": sar_meta["platform"],
        "sar_product_type": sar_meta["product_type"],
        "sar_data_status": sar_meta["data_status"],
        "url": "https://dataspace.copernicus.eu/",
        "license": "ESA Copernicus Open Access / Illustrative mask: CC0-1.0",
        "original_incident": CASE_ID,
        "citation": detection_meta["citation_or_dataset_identifier"],
        "sensor": "Sentinel-1A C-SAR IW GRD",
        "certainty": "ILLUSTRATIVE reconstruction. Not output of automated SAR oil detection.",
        "precision": "Hourly acquisition, 10 m GRD; polygon is day-level illustrative mask",
        "transformation": "Manual digitisation from secondary published sources; topology validated",
    }

    # ── Build case findings ─────────────────────────────────────────────────
    findings = {
        "incident_id": CASE_ID,
        "investigation_mode": incident["investigation_mode"],
        "collision_site": {
            "lat": incident["latitude"],
            "lon": incident["longitude"],
            "status": "Documented historical source. Collision coordinates from public records.",
            "source": "ITOPF; Kamarajar Port Authority; Ministry of Shipping India",
            "provenance_class": "RECORDED",
        },
        "vessels_involved": incident["vessels_involved"],
        "reconstruction_supported": False,
        "reconstruction_blocked_reason": (
            "ERA5 wind and CMEMS ocean current reanalysis not yet loaded. "
            "Drift backtracking requires REANALYSIS forcing data. "
            "Do not use fictional constants for this canonical case."
        ),
        "metocean_status": {
            "wind": "NOT_LOADED — ERA5 required",
            "currents": "NOT_LOADED — CMEMS GLOBAL-REANALYSIS-PHY-001-030 required",
        },
        "ais_status": "TRAINING — illustrative reconstruction, not recorded AIS",
        "timeline_events": len(timeline["events"]),
        "evidence_items": len(evidence["evidence_items"]),
        "public_sources": incident["public_sources"],
        "known_spill_volume_tonnes": incident["known_spill_volume_tonnes_approx"],
        "affected_coastline_km": incident["affected_coastline_km_approx"],
        "sih_problem_id": incident["sih_problem_id"],
        "package_manifest": str(PACKAGE / "manifest.json"),
        "package_version": manifest["version"],
        "provenance_note": incident["provenance_note"],
    }

    if dry_run:
        print("DRY RUN — no database writes.")
        print(f"  Would create observation: {OBS_ID}")
        print(f"  Would create case: {CASE_ID}")
        print(f"  Would create {len(ais_data['tracks'])} AIS training tracks:")
        for t in ais_data["tracks"]:
            print(f"    - {t['id']} ({t['name']})")
        print()
        print("Run without --dry-run to apply.")
        return

    with connection() as conn:
        # ── Observation ─────────────────────────────────────────────────────
        existing_obs = conn.execute(
            "SELECT id FROM observations WHERE id=%s", (OBS_ID,)
        ).fetchone()
        if existing_obs:
            print(f"  Observation {OBS_ID} already exists — skipping.")
        else:
            conn.execute(
                """INSERT INTO observations(id,title,observed_at,temporal_precision,geometry,source,area_km2,polygon_count)
                VALUES(%s,%s,%s,'hour',ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)),%s,
                       ST_Area(ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)::geography)/1e6,%s)
                ON CONFLICT(id) DO NOTHING""",
                (
                    OBS_ID,
                    "Ennore Oil Spill — SAR observation, 29 January 2017",
                    "2017-01-29T04:30:00+00:00",
                    geom_gj,
                    Jsonb(obs_source),
                    geom_gj,
                    polygon_count,
                ),
            )
            print(f"  Created observation: {OBS_ID}")

        # ── AIS Training tracks ─────────────────────────────────────────────
        for track in ais_data["tracks"]:
            points = track["points"]
            provenance = {
                "kind": track["source_type"],
                "provider": track["source"],
                "license": "CC0-1.0",
                "provenance_class": track["provenance_class"],
                "is_reconstruction": track.get("is_reconstruction", True),
                "ui_label": track["ui_label"],
                "ui_warning": track["ui_warning"],
                "description": track.get("processing_method", ""),
                "citation": track.get("citation_or_dataset_identifier", ""),
                "vessel_name": track.get("vessel_name", ""),
                "vessel_type": track.get("vessel_type", ""),
                "imo": track.get("imo"),
                "flag": track.get("flag", ""),
            }
            coords = [(p["lon"], p["lat"]) for p in points]
            line_wkt = LineString(coords).wkt

            conn.execute(
                """INSERT INTO tracks(id,name,provenance,points,geometry,synthetic)
                VALUES(%s,%s,%s,%s,ST_GeomFromText(%s,4326),true)
                ON CONFLICT(id) DO NOTHING""",
                (
                    track["id"],
                    track["name"],
                    Jsonb(provenance),
                    Jsonb(points),
                    line_wkt,
                ),
            )
            print(f"  Track {track['id']} — seeded")

        # ── Case ────────────────────────────────────────────────────────────
        summary = (
            "HISTORICAL VALIDATION. On 28 January 2017, a collision between "
            "BW Maple (LPG tanker, Singapore) and Dawn Kancheepuram (bulk carrier, India) "
            f"near Ennore Port, Tamil Nadu released ~{incident['known_spill_volume_tonnes_approx']} "
            f"tonnes of fuel oil, affecting ~{incident['affected_coastline_km_approx']} km of coastline. "
            "This case demonstrates the PALEGIC SAR-first investigation workflow using "
            "ILLUSTRATIVE slick geometry and TRAINING AIS reconstructions. "
            "All data provenance is explicitly classified."
        )

        conn.execute(
            """INSERT INTO cases(id,title,trigger,observation_id,status,published,exercise,summary,findings)
            VALUES(%s,%s,'sar',%s,'needs_evidence',true,false,%s,%s)
            ON CONFLICT(id) DO NOTHING""",
            (
                CASE_ID,
                "Ennore Oil Spill — Historical Validation Investigation",
                OBS_ID,
                summary,
                Jsonb(findings),
            ),
        )
        print(f"  Case {CASE_ID} created (or already existed).")

    print()
    print(f"Seed complete. Case ID: {CASE_ID}")
    print(f"Case is published=true and exercise=false — visible in public archive.")
    print()
    print("NEXT STEPS:")
    print("  1. Download ERA5 wind:    python scripts/fetch_era5_wind.py --incident SIH-ENNORE-2017")
    print("  2. Download CMEMS currents: python scripts/fetch_cmems_currents.py --incident SIH-ENNORE-2017")
    print("  3. Acquire SAR raster:    see data/demo/ennore-2017/sar/README.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed SIH-ENNORE-2017 into the PALEGIC database."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing to the database.",
    )
    args = parser.parse_args()
    seed(dry_run=args.dry_run)
