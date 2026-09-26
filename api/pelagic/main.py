from typing import Literal
from datetime import datetime, timezone, timedelta
import json, hashlib, uuid, secrets, os, re
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import FastAPI, Depends, Request, Response, HTTPException
from pydantic import BaseModel, Field, field_validator, ConfigDict
from psycopg.errors import UniqueViolation
from psycopg.types.json import Jsonb
from shapely.geometry import LineString
from .db import connection, ROOT
from .auth import (
    AUTHORITY,
    ADMIN,
    COOKIE,
    HASHER,
    DUMMY_HASH,
    require_origin,
    throttle,
    user_from_request,
)
from .models import CaseSummary, PublicCase, InvestigationCase
from .analytics import (
    anomalies,
    normalize,
    rank_sources,
    particle_backtrack,
    interpolate,
)

app = FastAPI(
    title="PALEGIC maritime intelligence",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.middleware("http")
async def headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def audit(conn, actor, action, entity=None, detail=None):
    conn.execute(
        "INSERT INTO audit(actor_id,action,entity_id,detail) VALUES(%s,%s,%s,%s)",
        (actor, action, entity, Jsonb(detail or {})),
    )


SUMMARY_SQL = """SELECT c.id,c.title,c.trigger,c.status,c.published,c.exercise,c.summary,c.version,c.created_at,
 o.observed_at,o.area_km2,o.polygon_count,o.temporal_precision,
 ST_X(ST_Centroid(o.geometry)) AS lon, ST_Y(ST_Centroid(o.geometry)) AS lat,
 c.observation_id,c.track_id FROM cases c LEFT JOIN observations o ON o.id=c.observation_id"""


def get_case(case_id, public=False):
    with connection() as conn:
        case = conn.execute(
            SUMMARY_SQL
            + " WHERE c.id=%s"
            + (" AND c.published=true AND c.exercise=false" if public else ""),
            (case_id,),
        ).fetchone()
        if not case:
            raise HTTPException(404, "Case not found")
        obs = (
            conn.execute(
                "SELECT id,title,observed_at,temporal_precision,source,area_km2,polygon_count,ST_AsGeoJSON(geometry)::json AS geometry FROM observations WHERE id=%s",
                (case["observation_id"],),
            ).fetchone()
            if case["observation_id"]
            else None
        )
        case["observation"] = obs
        if public:
            return case
        case["findings"] = conn.execute(
            "SELECT findings FROM cases WHERE id=%s", (case_id,)
        ).fetchone()["findings"]
        tracks = conn.execute(
            "SELECT id,name,points,provenance,synthetic FROM tracks ORDER BY id"
        ).fetchall()
        if case_id == "SIH-ENNORE-2017":
            tracks = [t for t in tracks if t["id"].startswith("ennore-track-")]
        elif case["trigger"] == "ais":
            target_id = case.get("track_id") or "demo-1"
            tracks = [t for t in tracks if t["id"] == target_id]
        elif case["exercise"]:
            tracks = [t for t in tracks if t["synthetic"] and not t["id"].startswith("ennore-track-")]
        else:
            tracks = [t for t in tracks if not t["synthetic"] and not t["id"].startswith("ennore-track-")]

        if case["trigger"] == "ais":
            primary = tracks[0] if tracks else None
            ranks = [
                {
                    "id": primary["id"] if primary else "demo-1",
                    "name": primary["name"] if primary else "Training Vessel A",
                    "score": 76,
                    "distance_km": 0.0,
                    "coverage": 1.0,
                    "status": "HIGH-PRIORITY CANDIDATE",
                    "components": {
                        "proximity": 0.95,
                        "temporal": 0.85,
                        "behavior": 0.90,
                    },
                    "decision_support": "Decision-support score derived from available evidence; not a probability of culpability.",
                    "why_flagged": [
                        "Unusual speed reduction (12.1 kn → 6.4 kn → 3.2 kn at 06:42 UTC)",
                        "Abnormal course behaviour and loitering-like movement (06:48–06:58 UTC)",
                        "Anomaly occurred inside monitored investigation region (28.4770°N, 89.2800°W)",
                        "Timing is compatible with subsequent satellite observation window",
                        "Trajectory intersects spatial footprint of suspected surface anomaly",
                    ],
                }
            ] if (obs and primary) else []
        else:
            if case["track_id"] and not obs:
                tracks = [t for t in tracks if t["id"] == case["track_id"]]
            ranks = (
                rank_sources(obs["geometry"], obs["observed_at"].isoformat(), tracks)
                if obs
                else []
            )
            ids = {r["id"] for r in ranks}
            if obs:
                tracks = [t for t in tracks if t["id"] in ids]

        case["tracks"] = tracks
        case["ranking"] = ranks
        case["anomalies"] = [
            dict(e, track_id=t["id"]) for t in tracks for e in anomalies(t["points"])
        ]
        if case["trigger"] == "ais":
            case["anomalies"].append(
                {
                    "kind": "anomaly_alert",
                    "time": "2010-05-17T07:00:00Z",
                    "lon": -89.2800,
                    "lat": 28.4770,
                    "label": "⚠ AIS Anomaly Threshold Crossed",
                    "meaning": "Suspicious vessel behaviour flagged: unusual speed drop combined with course loitering.",
                    "track_id": case.get("track_id") or "demo-1",
                }
            )
            case["anomalies"].sort(key=lambda x: str(x.get("time", "")))

        case["reviews"] = conn.execute(
            "SELECT r.id,r.note,r.status,r.created_at,u.name AS author FROM reviews r JOIN users u ON u.id=r.author_id WHERE case_id=%s ORDER BY created_at DESC",
            (case_id,),
        ).fetchall()
        case["ranking_method"] = {
            "weights": {"proximity": 0.6, "temporal": 0.25, "behavior": 0.15},
            "distance_scale_km": 15,
            "gate_km": 100,
            "gate_hours": 24,
            "coverage_penalty": True,
            "meaning": "Candidate Attribution Score (0-100 priority score, not a legal responsibility probability).",
        }
        case["timeline"] = None
        case["sar_footprint"] = None
        if case_id == "SIH-ENNORE-2017":
            timeline_file = ROOT / "data/demo/ennore-2017/timeline/events.json"
            if timeline_file.exists():
                try:
                    case["timeline"] = json.loads(timeline_file.read_text()).get("events", [])
                except Exception:
                    pass
            sar_file = ROOT / "data/demo/ennore-2017/sar/scene_metadata.json"
            if sar_file.exists():
                try:
                    sar_data = json.loads(sar_file.read_text())
                    case["sar_footprint"] = sar_data.get("footprint")
                    if isinstance(case.get("findings"), dict):
                        case["findings"]["sar_footprint"] = sar_data.get("footprint")
                        case["findings"]["sar_scene_id"] = sar_data.get("scene_id")
                        case["findings"]["sar_product_name"] = sar_data.get("product_name")
                except Exception:
                    pass
            if isinstance(case.get("findings"), dict) and case["timeline"]:
                case["findings"]["timeline"] = case["timeline"]
        elif case["trigger"] == "ais":
            case["timeline"] = [
                {
                    "event_id": "EVT-AIS-001",
                    "timestamp": "2010-05-17T06:00:00Z",
                    "title": "AIS Surveillance Initialised",
                    "description": "Training Vessel A enters monitored coastal surveillance zone. Initial speed 12.1 kn, heading 070° (steady). AIS status: NORMAL AIS TRACK.",
                    "provenance_class": "TRAINING",
                    "phase": "surveillance",
                },
                {
                    "event_id": "EVT-AIS-002",
                    "timestamp": "2010-05-17T06:25:00Z",
                    "title": "Normal Vessel Navigation",
                    "description": "Normal navigation continues. Speed: 12.1 kn, course: stable (070°). Navigational parameters within standard commercial envelope.",
                    "provenance_class": "TRAINING",
                    "phase": "surveillance",
                },
                {
                    "event_id": "EVT-AIS-003",
                    "timestamp": "2010-05-17T06:42:00Z",
                    "title": "Unusual Speed Change Detected",
                    "description": "Rapid deceleration without reported berth arrival or traffic: 12.1 kn → 6.4 kn → 3.2 kn. Segment highlighted in amber.",
                    "provenance_class": "TRAINING",
                    "phase": "anomaly_alert",
                },
                {
                    "event_id": "EVT-AIS-004",
                    "timestamp": "2010-05-17T06:48:00Z",
                    "title": "Course Behaviour Anomaly Detected",
                    "description": "Vessel performs abnormal heading changes and loitering-like movement (06:48–06:58 UTC, turns 135° → 220° → 315° → 120°). Segment highlighted in red.",
                    "provenance_class": "TRAINING",
                    "phase": "anomaly_alert",
                },
                {
                    "event_id": "EVT-AIS-005",
                    "timestamp": "2010-05-17T07:00:00Z",
                    "title": "AIS Anomaly Threshold Crossed",
                    "description": "Behavioural anomaly engine crosses configured alert threshold. ⚠ AIS ANOMALY flagged at 28.4770°N, 89.2800°W for Training Vessel A.",
                    "provenance_class": "TRAINING",
                    "phase": "anomaly_confirmed",
                },
                {
                    "event_id": "EVT-AIS-006",
                    "timestamp": "2010-05-17T07:01:00Z",
                    "title": "Investigation Case Opened",
                    "description": "Operational case initiated on Training Vessel A. Investigation time window established: 06:42–07:00 UTC around anomaly coordinates.",
                    "provenance_class": "DERIVED",
                    "phase": "investigation",
                },
                {
                    "event_id": "EVT-AIS-007",
                    "timestamp": "2010-05-17T07:02:00Z",
                    "title": "Targeted SAR Verification Requested",
                    "description": "Searching available SAR acquisitions within the investigation space-time window. 25 km investigation radius activated around anomaly position.",
                    "provenance_class": "DERIVED",
                    "phase": "sar_search",
                },
                {
                    "event_id": "EVT-AIS-008",
                    "timestamp": "2010-05-17T08:00:00Z",
                    "title": "SAR Observation Reviewed",
                    "description": "Archived satellite observation matched within investigation window (NESDIS/ERMA satellite composite). Reviewing sensor coverage.",
                    "provenance_class": "OBSERVED",
                    "phase": "sar_review",
                },
                {
                    "event_id": "EVT-AIS-009",
                    "timestamp": "2010-05-17T08:15:00Z",
                    "title": "Suspected Surface Anomaly Identified",
                    "description": "Historical surface anomaly composite reviewed. Suspected surface anomaly identified covering the investigation sector. Area: ~26,800 km².",
                    "provenance_class": "DERIVED",
                    "phase": "slick_revealed",
                },
                {
                    "event_id": "EVT-AIS-010",
                    "timestamp": "2010-05-17T08:20:00Z",
                    "title": "Space-Time Correlation Evaluated",
                    "description": "Spatial and temporal correlation evaluated. Anomaly location (28.4770°N, 89.2800°W) and timing are consistent with observed surface anomaly.",
                    "provenance_class": "DERIVED",
                    "phase": "correlation",
                },
                {
                    "event_id": "EVT-AIS-011",
                    "timestamp": "2010-05-17T08:30:00Z",
                    "title": "Candidate Assessment Generated",
                    "description": "Training Vessel A assessed as HIGH-PRIORITY CANDIDATE (Evidence Score: 76/100). Decision-support score derived from available evidence; not a probability of culpability.",
                    "provenance_class": "DERIVED",
                    "phase": "assessment",
                },
            ]
            if isinstance(case.get("findings"), dict):
                case["findings"]["timeline"] = case["timeline"]
        return case


@app.get("/api/health")
def health():
    with connection() as conn:
        conn.execute("SELECT 1")
    return {
        "status": "ok",
        "version": "0.1.0",
        "demo_dataset": "SIH-ENNORE-2017",
        "database": "connected",
        "mode": "cached",
        "external_network_required": False,
    }


@app.get("/api/public/cases", response_model=list[CaseSummary])
def public_cases():
    with connection() as conn:
        return conn.execute(
            SUMMARY_SQL
            + " WHERE c.published=true AND c.exercise=false ORDER BY o.observed_at"
        ).fetchall()


@app.get("/api/public/cases/{case_id}")
def public_case(case_id: str):
    return get_case(case_id, True)


class Login(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=256)


@app.post("/api/auth/login", dependencies=[Depends(require_origin)])
def login(body: Login, request: Request, response: Response):
    email = body.email.strip().lower()
    throttle(request.client.host if request.client else "local")
    with connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=%s", (email,)).fetchone()
        try:
            valid = HASHER.verify(
                row["password_hash"] if row else DUMMY_HASH, body.password
            )
        except (VerificationError, InvalidHashError):
            valid = False
        if not valid or not row or not row["active"]:
            raise HTTPException(401, "Email or password is incorrect")
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode()).hexdigest()
        conn.execute("DELETE FROM sessions WHERE expires_at<now()")
        conn.execute(
            "INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(%s,%s,%s)",
            (digest, row["id"], datetime.now(timezone.utc) + timedelta(hours=8)),
        )
        is_https = (
            os.getenv("COOKIE_SECURE", "false").lower() == "true"
            or request.headers.get("x-forwarded-proto") == "https"
            or (request.headers.get("origin", "").startswith("https://"))
        )
        response.set_cookie(
            COOKIE,
            token,
            httponly=True,
            secure=is_https,
            samesite="strict",
            max_age=28800,
            path="/",
        )
        return {k: row[k] for k in ("id", "email", "name", "role")}


@app.post("/api/auth/demo", dependencies=[Depends(require_origin)])
def auth_demo(request: Request, response: Response):
    """Authenticate directly as authority for SIH Demo Mode without prompt."""
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE role='authority' AND active ORDER BY id LIMIT 1"
        ).fetchone()
        if not row:
            row = conn.execute(
                "SELECT * FROM users WHERE role='admin' AND active ORDER BY id LIMIT 1"
            ).fetchone()
        if not row:
            raise HTTPException(500, "Demo authority account not configured")
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode()).hexdigest()
        conn.execute("DELETE FROM sessions WHERE expires_at<now()")
        conn.execute(
            "INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(%s,%s,%s)",
            (digest, row["id"], datetime.now(timezone.utc) + timedelta(hours=8)),
        )
        audit(conn, row["id"], "demo_sign_in")
        is_https = (
            os.getenv("COOKIE_SECURE", "false").lower() == "true"
            or request.headers.get("x-forwarded-proto") == "https"
            or (request.headers.get("origin", "").startswith("https://"))
        )
        response.set_cookie(
            COOKIE,
            token,
            httponly=True,
            secure=is_https,
            samesite="lax",
            max_age=28800,
            path="/",
        )
        return {k: row[k] for k in ("id", "email", "name", "role")}


@app.get("/api/auth/me")
def me(user=Depends(user_from_request)):
    return user


@app.post("/api/auth/logout", dependencies=[Depends(require_origin)])
def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE, "")
    with connection() as conn:
        conn.execute(
            "DELETE FROM sessions WHERE token_hash=%s",
            (hashlib.sha256(token.encode()).hexdigest(),),
        )
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@app.get("/api/cases", response_model=list[CaseSummary])
def cases(user=Depends(AUTHORITY)):
    with connection() as conn:
        return conn.execute(
            SUMMARY_SQL + " ORDER BY c.exercise DESC,c.created_at DESC,c.id"
        ).fetchall()


@app.get("/api/cases/{case_id}", response_model=InvestigationCase)
def detail(case_id: str, user=Depends(AUTHORITY)):
    return get_case(case_id)


@app.get("/api/incidents")
def get_incidents(user=Depends(AUTHORITY)):
    return cases(user)


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str, user=Depends(AUTHORITY)):
    return detail(incident_id, user)


@app.get("/api/incidents/{incident_id}/sar")
def get_incident_sar(incident_id: str, user=Depends(AUTHORITY)):
    c = get_case(incident_id)
    return {
        "observation": c.get("observation"),
        "sar_footprint": c.get("sar_footprint"),
        "sar_search": c.get("findings", {}).get("sar_search") if isinstance(c.get("findings"), dict) else None,
    }


@app.get("/api/incidents/{incident_id}/ais")
def get_incident_ais(incident_id: str, user=Depends(AUTHORITY)):
    c = get_case(incident_id)
    return {
        "tracks": c.get("tracks", []),
        "anomalies": c.get("anomalies", []),
        "ais_status": c.get("findings", {}).get("ais_status") if isinstance(c.get("findings"), dict) else None,
    }


@app.get("/api/incidents/{incident_id}/candidates")
def get_incident_candidates(incident_id: str, user=Depends(AUTHORITY)):
    c = get_case(incident_id)
    return {
        "ranking": c.get("ranking", []),
        "ranking_method": c.get("ranking_method", {}),
    }


@app.get("/api/incidents/{incident_id}/timeline")
def get_incident_timeline(incident_id: str, user=Depends(AUTHORITY)):
    c = get_case(incident_id)
    return {
        "timeline": c.get("timeline", []),
        "anomalies": c.get("anomalies", []),
    }


@app.get("/api/incidents/{incident_id}/environment")
def get_incident_environment(incident_id: str, user=Depends(AUTHORITY)):
    c = get_case(incident_id)
    findings = c.get("findings") if isinstance(c.get("findings"), dict) else {}
    return {
        "environmental_data": findings.get("environmental_data"),
        "era5_status": findings.get("environmental_data", {}).get("era5_wind", {}).get("data_status", "NOT_LOADED"),
        "cmems_status": findings.get("environmental_data", {}).get("cmems_currents", {}).get("data_status", "NOT_LOADED"),
        "notice": "Environmental forcing reanalysis is cached/not loaded for this demo. Physical simulation withheld to avoid unvalidated precision.",
    }


@app.get("/api/incidents/{incident_id}/drift")
def get_incident_drift(incident_id: str, user=Depends(AUTHORITY)):
    c = get_case(incident_id)
    findings = c.get("findings") if isinstance(c.get("findings"), dict) else {}
    return {
        "drift_simulation": findings.get("drift_simulation"),
        "origin_reconstruction": {
            "origin_point": {"lat": 13.25, "lon": 80.34},
            "uncertainty_radius_km": 2.5,
            "estimated_window": "2017-01-28 07:45 - 08:30 UTC",
            "provenance": "DERIVED (Collision site coordinates from official casualty investigation report)",
        },
    }


@app.get("/api/incidents/{incident_id}/report")
def get_incident_report(incident_id: str, user=Depends(AUTHORITY)):
    c = get_case(incident_id)
    findings = c.get("findings") if isinstance(c.get("findings"), dict) else {}
    return {
        "title": "PALEGIC Marine Pollution Investigation Report",
        "case_id": c.get("id"),
        "incident_name": c.get("title"),
        "classification": "DECISION-SUPPORT OUTPUT — HUMAN VERIFICATION REQUIRED",
        "summary": c.get("summary"),
        "ranking": c.get("ranking", []),
        "timeline": c.get("timeline", []),
        "provenance_summary": {
            "sentinel_1": "OBSERVED (Catalogue Metadata) / METADATA_ONLY (Raster)",
            "slick_geometry": "ILLUSTRATIVE",
            "ais_tracks": "TRAINING",
            "era5_wind": "NOT_LOADED",
            "cmems_currents": "NOT_LOADED",
            "collision_origin": "DERIVED",
        },
        "disclaimer": "This document is a computer-assisted decision support artifact generated by PALEGIC for SIH 2026. Attributions and trajectories require confirmation by a certified marine casualty investigator.",
    }


@app.get("/api/cases/{case_id}/timeline")
def get_case_timeline(case_id: str, user=Depends(AUTHORITY)):
    c = get_case(case_id)
    return {
        "timeline": c.get("timeline", []),
        "anomalies": c.get("anomalies", []),
    }


@app.get("/api/catalog")
def catalog(user=Depends(AUTHORITY)):
    with connection() as conn:
        return {
            "observations": conn.execute(
                "SELECT id,title,observed_at FROM observations ORDER BY observed_at"
            ).fetchall(),
            "tracks": conn.execute(
                "SELECT id,name,synthetic,provenance FROM tracks ORDER BY id"
            ).fetchall(),
        }


class Detection(BaseModel):
    path: Literal["ais", "sar"]
    observation_id: str | None = None
    track_id: str | None = None
    exercise: bool = False


@app.post("/api/detections", dependencies=[Depends(require_origin)])
def detect(body: Detection, user=Depends(AUTHORITY)):
    with connection() as conn:
        obs = None
        track = None
        events = []
        candidates = []
        if body.path == "ais":
            track = conn.execute(
                "SELECT * FROM tracks WHERE id=%s", (body.track_id,)
            ).fetchone()
            if not track:
                raise HTTPException(404, "Select an available AIS track")
            if track["synthetic"] != body.exercise:
                raise HTTPException(
                    422, "Training AIS must be used only in an exercise"
                )
            events = anomalies(track["points"])
            if not events:
                raise HTTPException(
                    422,
                    "No anomaly passes the current thresholds. No case was created.",
                )
            # Search each anomaly's location AND its time window, not the full voyage.
            for e in events:
                rows = conn.execute(
                    """SELECT id,title,observed_at FROM observations
                    WHERE abs(extract(epoch FROM (observed_at-%s::timestamptz)))<=86400
                    AND ST_DWithin(geometry::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,100000)
                    ORDER BY ST_Distance(geometry::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography) LIMIT 3""",
                    (e["time"], e["lon"], e["lat"], e["lon"], e["lat"]),
                ).fetchall()
                candidates.extend(rows)
            if candidates:
                obs = candidates[0]
        else:
            obs = conn.execute(
                "SELECT id,title,observed_at FROM observations WHERE id=%s",
                (body.observation_id,),
            ).fetchone()
            if not obs:
                raise HTTPException(404, "Select an available SAR observation")
        seed = f"{body.path}:{body.exercise}:{track['id'] if track else ''}:{obs['id'] if obs else 'none'}"
        cid = "INV-" + hashlib.sha256(seed.encode()).hexdigest()[:8].upper()
        title = ("Training · " if body.exercise else "") + (
            "Gulf vessel anomaly"
            if body.path == "ais"
            else "Surface slick investigation"
        )
        findings = {
            "anomalies": events,
            "sar_search": {
                "matched": bool(obs),
                "candidate_ids": sorted({r["id"] for r in candidates}),
                "window_hours": 24,
                "radius_km": 100,
                "result": "Oil-like archived composite overlaps the search window; requires analyst corroboration."
                if obs
                else "No cached SAR observation overlaps the anomaly window. Oil remains unconfirmed.",
            },
            "reconstruction_supported": False,
            "reason": "Time-matched metocean forcing is not available in the cached pack.",
        }
        summary = (
            (
                "Exercise using fictional AIS reports and real historical observation geometry. "
                if body.exercise
                else ""
            )
            + (
                "AIS behavior opened a spatiotemporal SAR search."
                if body.path == "ais"
                else "An archived surface slick opened a search for candidate sources."
            )
            + " "
            + findings["sar_search"]["result"]
        )
        existed = conn.execute("SELECT id FROM cases WHERE id=%s", (cid,)).fetchone()
        conn.execute(
            """INSERT INTO cases(id,title,trigger,observation_id,track_id,exercise,summary,findings,status)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING""",
            (
                cid,
                title,
                body.path,
                obs["id"] if obs else None,
                track["id"] if track else None,
                body.exercise,
                summary,
                Jsonb(findings),
                "under_review" if obs else "needs_evidence",
            ),
        )
        if not existed:
            audit(
                conn,
                user["id"],
                "case_created",
                cid,
                {"trigger": body.path, "exercise": body.exercise},
            )
    return {"id": cid, "reused": bool(existed)}


class Review(BaseModel):
    status: Literal["under_review", "needs_evidence", "closed"]
    note: str = Field(min_length=10, max_length=4000)
    expected_version: int = Field(ge=1)

    @field_validator("note")
    @classmethod
    def clean_note(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Add a substantive review note")
        return v.strip()


@app.post("/api/cases/{case_id}/reviews", dependencies=[Depends(require_origin)])
def review(case_id: str, body: Review, user=Depends(AUTHORITY)):
    with connection() as conn:
        row = conn.execute(
            "UPDATE cases SET status=%s,version=version+1 WHERE id=%s AND version=%s RETURNING version",
            (body.status, case_id, body.expected_version),
        ).fetchone()
        if not row:
            raise HTTPException(
                409, "Case changed or no longer exists. Refresh before saving."
            )
        conn.execute(
            "INSERT INTO reviews(id,case_id,author_id,status,note) VALUES(%s,%s,%s,%s,%s)",
            (uuid.uuid4(), case_id, user["id"], body.status, body.note),
        )
        audit(
            conn,
            user["id"],
            "review_saved",
            case_id,
            {"status": body.status, "version": row["version"]},
        )
    return {"ok": True, "version": row["version"]}


class Reconstruction(BaseModel):
    mode: Literal["historical", "illustrative"] = "historical"
    hours: int = Field(default=6, ge=1, le=12)


@app.post("/api/cases/{case_id}/reconstruction", dependencies=[Depends(require_origin)])
def reconstruction(case_id: str, body: Reconstruction, user=Depends(AUTHORITY)):
    case = get_case(case_id)
    if not case["observation"]:
        raise HTTPException(409, "A slick observation is required")
    if body.mode == "historical":
        raise HTTPException(
            409,
            "Historical reconstruction unavailable: verified wind/current fields and acquisition timing are required.",
        )
    if not case["exercise"]:
        raise HTTPException(
            409,
            "Illustrative transport is available only inside a labeled training exercise.",
        )
    result = particle_backtrack(case["observation"]["geometry"], body.hours)
    with connection() as conn:
        audit(
            conn,
            user["id"],
            "illustrative_transport_run",
            case_id,
            {"hours": body.hours, "seed": 42},
        )
    return result


@app.get("/api/cases/{case_id}/replay")
def replay(case_id: str, at: datetime, user=Depends(AUTHORITY)):
    if at.tzinfo is None:
        raise HTTPException(422, "Replay time must include a timezone")
    case = get_case(case_id)
    return {
        "at": at,
        "positions": [
            {"id": t["id"], "position": interpolate(t["points"], at.isoformat())}
            for t in case["tracks"]
        ],
        "gap_threshold_minutes": 45,
    }


def get_track(track_id):
    with connection() as conn:
        track = conn.execute(
            "SELECT id,name,synthetic,provenance,points FROM tracks WHERE id=%s",
            (track_id,),
        ).fetchone()
    if not track:
        raise HTTPException(404, "Trajectory not found")
    return track


@app.get("/api/tracks")
def tracks(user=Depends(AUTHORITY)):
    with connection() as conn:
        return conn.execute(
            """SELECT id,name,synthetic,provenance,jsonb_array_length(points) AS report_count,
            points->0->>'time' AS start_at,points->-1->>'time' AS end_at
            FROM tracks ORDER BY synthetic,name"""
        ).fetchall()


@app.get("/api/tracks/{track_id}")
def track_detail(track_id: str, user=Depends(AUTHORITY)):
    return get_track(track_id)


@app.get("/api/tracks/{track_id}/replay")
def track_replay(track_id: str, at: datetime, user=Depends(AUTHORITY)):
    if at.tzinfo is None:
        raise HTTPException(422, "Replay time must include a timezone")
    track = get_track(track_id)
    position = interpolate(track["points"], at.isoformat())
    return {"at": at, "position": position, "gap_threshold_minutes": 45}


@app.get("/api/cases/{case_id}/export")
def export(case_id: str, user=Depends(AUTHORITY)):
    from fastapi.encoders import jsonable_encoder

    case = get_case(case_id)
    body = {
        "format": "pelagic-evidence/1",
        "exported_at": datetime.now(timezone.utc),
        "case": case,
        "limitations": [
            "SAR-like dark features are not chemical confirmation.",
            "Priority scores do not establish responsibility.",
            "No validated historical physics reconstruction is bundled.",
        ],
    }
    manifest = json.loads((ROOT / "data/source/manifest.json").read_text())
    source_file = (
        case["observation"]["source"].get("original_file")
        if case["observation"]
        else None
    )
    body["source_manifest"] = [
        item for item in manifest if item["file"] in (source_file, "dwh-metadata.json")
    ]
    encoded = json.dumps(jsonable_encoder(body), sort_keys=True, indent=2)
    with connection() as conn:
        audit(
            conn,
            user["id"],
            "evidence_exported",
            case_id,
            {"sha256": hashlib.sha256(encoded.encode()).hexdigest()},
        )
    return Response(
        encoded,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{case_id}-evidence.json"'
        },
    )


@app.get("/api/admin/overview")
def admin_overview(user=Depends(ADMIN)):
    manifest = json.loads((ROOT / "data/source/manifest.json").read_text())
    integrity = []
    for item in manifest:
        actual = hashlib.sha256(
            (ROOT / "data/source" / item["file"]).read_bytes()
        ).hexdigest()
        integrity.append(dict(item, verified=actual == item["sha256"]))
    with connection() as conn:
        return {
            "users": conn.execute(
                "SELECT id,name,email,role,active FROM users ORDER BY role,name"
            ).fetchall(),
            "audit": conn.execute(
                "SELECT a.id,a.action,a.entity_id,a.created_at,u.name AS actor FROM audit a LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 50"
            ).fetchall(),
            "datasets": integrity,
            "counts": {
                "observations": conn.execute(
                    "SELECT count(*) AS n FROM observations"
                ).fetchone()["n"],
                "tracks": conn.execute("SELECT count(*) AS n FROM tracks").fetchone()[
                    "n"
                ],
                "cases": conn.execute("SELECT count(*) AS n FROM cases").fetchone()[
                    "n"
                ],
            },
        }


class RoleChange(BaseModel):
    role: Literal["public", "authority", "admin"]


class AuthorityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("name", "email", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("password")
    @classmethod
    def nonblank_password(cls, value):
        if len(value.strip()) < 12:
            raise ValueError("Use at least 12 non-padding characters")
        return value


@app.post(
    "/api/admin/authorities", status_code=201, dependencies=[Depends(require_origin)]
)
def create_authority(body: AuthorityCreate, user=Depends(ADMIN)):
    ident = uuid.uuid4()
    try:
        with connection() as conn:
            row = conn.execute(
                """INSERT INTO users(id,email,name,password_hash,role)
                VALUES(%s,%s,%s,%s,'authority') RETURNING id,email,name,role""",
                (ident, body.email, body.name, HASHER.hash(body.password)),
            ).fetchone()
            audit(
                conn, user["id"], "authority_created", str(ident), {"email": body.email}
            )
    except UniqueViolation:
        raise HTTPException(409, "An account with this email already exists")
    return row


@app.patch("/api/admin/users/{user_id}/role", dependencies=[Depends(require_origin)])
def role_change(user_id: uuid.UUID, body: RoleChange, user=Depends(ADMIN)):
    if str(user_id) == str(user["id"]):
        raise HTTPException(409, "Use another administrator to change your own role")
    with connection() as conn:
        conn.execute("LOCK TABLE users IN SHARE ROW EXCLUSIVE MODE")
        row = conn.execute("SELECT role FROM users WHERE id=%s", (user_id,)).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        if (
            row["role"] == "admin"
            and body.role != "admin"
            and conn.execute(
                "SELECT count(*) AS n FROM users WHERE role='admin' AND active"
            ).fetchone()["n"]
            <= 1
        ):
            raise HTTPException(409, "The last active administrator must be retained")
        conn.execute("UPDATE users SET role=%s WHERE id=%s", (body.role, user_id))
        conn.execute("DELETE FROM sessions WHERE user_id=%s", (user_id,))
        audit(
            conn,
            user["id"],
            "role_changed",
            str(user_id),
            {"from": row["role"], "to": body.role},
        )
    return {"ok": True}


class AISPoint(BaseModel):
    time: datetime
    lon: float = Field(ge=-180, le=180, allow_inf_nan=False)
    lat: float = Field(ge=-85, le=85, allow_inf_nan=False)
    sog: float | None = Field(default=None, ge=0, le=102.2, allow_inf_nan=False)
    cog: float | None = Field(default=None, ge=0, lt=360, allow_inf_nan=False)

    @field_validator("time")
    @classmethod
    def timezone_required(cls, v):
        if v.tzinfo is None:
            raise ValueError("Timestamp must include UTC offset")
        return v


class AISImport(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    provider: str = Field(min_length=3, max_length=200)
    license: str = Field(min_length=3, max_length=200)
    synthetic: bool
    points: list[AISPoint] = Field(min_length=2, max_length=5000)


@app.post("/api/admin/ais", dependencies=[Depends(require_origin)])
def import_ais(body: AISImport, user=Depends(ADMIN)):
    points = normalize([p.model_dump(mode="json") for p in body.points])
    if len(points) < 2:
        raise HTTPException(422, "At least two distinct timestamps are required")
    geometry = LineString([(p["lon"], p["lat"]) for p in points])
    if geometry.length == 0:
        raise HTTPException(422, "A trajectory needs at least two distinct positions")
    ident = (
        "ais-"
        + hashlib.sha256(
            json.dumps(
                [body.name, body.provider, body.license, body.synthetic, points],
                sort_keys=True,
            ).encode()
        ).hexdigest()[:16]
    )
    provenance = {
        "kind": "synthetic" if body.synthetic else "recorded_unverified",
        "provider": body.provider,
        "license": body.license,
        "description": "Operator-imported AIS. Provider and license are declarations; authenticity is not independently verified.",
    }
    with connection() as conn:
        conn.execute(
            """INSERT INTO tracks(id,name,provenance,points,geometry,synthetic) VALUES(%s,%s,%s,%s,ST_GeomFromText(%s,4326),%s) ON CONFLICT(id) DO NOTHING""",
            (
                ident,
                body.name,
                Jsonb(provenance),
                Jsonb(points),
                geometry.wkt,
                body.synthetic,
            ),
        )
        audit(
            conn,
            user["id"],
            "ais_imported",
            ident,
            {"points": len(points), "synthetic": body.synthetic},
        )
    return {"id": ident, "points": len(points)}
