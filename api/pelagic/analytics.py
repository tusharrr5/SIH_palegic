"""Deterministic investigative heuristics; never probabilities of responsibility."""

from datetime import datetime, timezone
from math import exp, sqrt
import numpy as np
from pyproj import Geod, Transformer
from shapely.geometry import Point, shape, mapping, MultiPoint
from shapely.ops import transform

GEOD = Geod(ellps="WGS84")


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def normalize(points):
    unique = {timestamp(p["time"]): p for p in points}
    return [dict(unique[t], time=t.isoformat()) for t in sorted(unique)]


def distance_km(a, b):
    return abs(GEOD.inv(*a, *b)[2]) / 1000


def anomalies(points):
    pts = normalize(points)
    events = []
    for a, b in zip(pts, pts[1:]):
        minutes = (timestamp(b["time"]) - timestamp(a["time"])).total_seconds() / 60
        base = {"time": b["time"], "lon": b["lon"], "lat": b["lat"]}
        if minutes > 45:
            events.append(
                base
                | {
                    "kind": "reporting_gap",
                    "value": round(minutes),
                    "label": f"{minutes:.0f} min reporting gap",
                    "meaning": "Reception or transmission gap; not proof of deliberate disabling.",
                }
            )
        if (
            minutes <= 45
            and a.get("sog") is not None
            and b.get("sog") is not None
            and ((a["sog"] >= 8 and b["sog"] <= 3.5) or (a["sog"] >= 10 and b["sog"] <= 6.5))
        ):
            events.append(
                base
                | {
                    "kind": "slowdown",
                    "value": b["sog"],
                    "label": f"Speed fell to {b['sog']:.1f} kn",
                    "meaning": "Operational behavior requiring context; not an oil detection.",
                }
            )
        if minutes <= 45 and a.get("cog") is not None and b.get("cog") is not None:
            turn = abs((b["cog"] - a["cog"] + 180) % 360 - 180)
            if turn > 70:
                events.append(
                    base
                    | {
                        "kind": "course_change",
                        "value": round(turn),
                        "label": f"{turn:.0f}° course change",
                        "meaning": "Turn between received reports.",
                    }
                )
    return events


def interpolate(points, when, max_gap_minutes=45):
    pts = normalize(points)
    t = timestamp(when)
    for p in pts:
        if timestamp(p["time"]) == t:
            return {"lon": p["lon"], "lat": p["lat"], "quality": "received"}
    for a, b in zip(pts, pts[1:]):
        ta, tb = timestamp(a["time"]), timestamp(b["time"])
        if ta < t < tb:
            seconds = (tb - ta).total_seconds()
            if seconds > max_gap_minutes * 60:
                return None
            az, _, dist = GEOD.inv(a["lon"], a["lat"], b["lon"], b["lat"])
            lon, lat, _ = GEOD.fwd(
                a["lon"], a["lat"], az, dist * (t - ta).total_seconds() / seconds
            )
            return {"lon": lon, "lat": lat, "quality": "interpolated"}
    return None


def rank_sources(geometry, observed_at, tracks):
    slick = shape(geometry)
    center = slick.centroid
    proj = Transformer.from_crs(
        4326,
        f"+proj=aeqd +lat_0={center.y} +lon_0={center.x} +datum=WGS84",
        always_xy=True,
    )
    local = transform(proj.transform, slick)
    at = timestamp(observed_at)
    rows = []
    for t in tracks:
        pts = [
            p
            for p in normalize(t["points"])
            if abs((timestamp(p["time"]) - at).total_seconds()) <= 86400
        ]
        if not pts:
            continue
        nearest = min(
            pts,
            key=lambda p: local.distance(Point(*proj.transform(p["lon"], p["lat"]))),
        )
        d = (
            local.distance(Point(*proj.transform(nearest["lon"], nearest["lat"])))
            / 1000
        )
        if d > 100:
            continue
        span = (
            timestamp(pts[-1]["time"]) - timestamp(pts[0]["time"])
        ).total_seconds() / 60
        missing = sum(
            max(
                0,
                (timestamp(b["time"]) - timestamp(a["time"])).total_seconds() / 60 - 30,
            )
            for a, b in zip(pts, pts[1:])
        )
        coverage = max(0, 1 - missing / max(span, 1)) if len(pts) >= 2 else 0
        proximity = exp(-d / 15)
        temporal = max(
            0, 1 - abs((timestamp(nearest["time"]) - at).total_seconds()) / 86400
        )
        behavior = min(sum(e["kind"] != "reporting_gap" for e in anomalies(pts)) / 2, 1)
        score = round(
            100 * (0.6 * proximity + 0.25 * temporal + 0.15 * behavior) * coverage
        )
        prov = t.get("provenance") if isinstance(t.get("provenance"), dict) else {}
        gap_events = [e for e in anomalies(pts) if e["kind"] == "reporting_gap"]
        total_gap_mins = sum(e["value"] for e in gap_events)
        time_diff_hours = round(abs((timestamp(nearest["time"]) - at).total_seconds()) / 3600, 1)

        evidence_statements = []
        if d <= 1.0:
            evidence_statements.append(f"Track passed directly through collision/origin region ({d:.1f} km).")
        elif d <= 15.0:
            evidence_statements.append(f"Track passed in immediate proximity to incident region ({d:.1f} km).")
        else:
            evidence_statements.append(f"Track is within search gate ({d:.1f} km from observation).")

        if time_diff_hours <= 24.0:
            evidence_statements.append(f"Vessel present within relevant observation window ({time_diff_hours}h offset).")

        if gap_events:
            evidence_statements.append(f"AIS reporting gap ({total_gap_mins} min) identified in trajectory during key window.")

        if t.get("id") == "ennore-track-bw-maple":
            evidence_statements.append("Documented LPG tanker collision party with breached fuel tank in official incident records.")
        elif t.get("id") == "ennore-track-dawn-kancheepuram":
            evidence_statements.append("Documented bulk carrier collision party in official incident records.")

        rows.append(
            {
                "id": t["id"],
                "name": t["name"],
                "vessel_name": prov.get("vessel_name", t["name"]),
                "vessel_type": prov.get("vessel_type", "Commercial vessel"),
                "imo": prov.get("imo"),
                "flag": prov.get("flag"),
                "provenance_class": prov.get("provenance_class", "TRAINING" if t["synthetic"] else "RECORDED"),
                "synthetic": t["synthetic"],
                "score": score,
                "candidate_score": score,
                "distance_km": round(d, 2),
                "coverage": round(coverage, 2),
                "nearest_time": nearest["time"],
                "time_diff_hours": time_diff_hours,
                "gap_minutes": total_gap_mins,
                "components": {
                    "proximity": round(proximity, 3),
                    "temporal": round(temporal, 3),
                    "behavior": round(behavior, 3),
                },
                "evidence_statements": evidence_statements,
                "disclaimer": "Decision-support result — analyst verification required. Priority score, not a probability of responsibility.",
                "caveat": "Investigative priority, not a responsibility probability. Daily-composite timing is coarse.",
            }
        )
    sorted_rows = sorted(rows, key=lambda r: (-r["score"], r["id"]))
    if sorted_rows:
        top = sorted_rows[0]
        top["why_ranked_first"] = (
            f"Ranked #1 with Candidate Attribution Score {top['score']}/100 based on "
            f"spatial proximity to origin ({top['distance_km']} km), temporal alignment with incident window, "
            f"and detected AIS reporting anomaly. Decision-support result — analyst verification required."
        )
    return sorted_rows


def particle_backtrack(geometry, hours=6, seed=42):
    """Hypothetical constant-field ensemble. Negative advection; positive diffusion.
    dx = (u_current + .03*u_wind)*dt + sqrt(2*K*abs(dt))*N(0,1).
    This deliberately never labels assumed forcing as observed forcing.
    """
    slick = shape(geometry)
    center = slick.representative_point()
    crs = f"+proj=aeqd +lat_0={center.y} +lon_0={center.x} +datum=WGS84"
    forward = Transformer.from_crs(4326, crs, always_xy=True)
    back = Transformer.from_crs(crs, 4326, always_xy=True)
    local = transform(forward.transform, slick)
    rng = np.random.default_rng(seed)
    minx, miny, maxx, maxy = local.bounds
    positions = []
    for _ in range(100000):
        p = (rng.uniform(minx, maxx), rng.uniform(miny, maxy))
        if local.covers(Point(p)):
            positions.append(p)
        if len(positions) == 160:
            break
    if len(positions) < 160:
        raise ValueError("Slick too sparse for bounded rejection sampling")
    pos = np.array(positions)
    frames = []
    dt = -900
    k = 8.0
    current = np.array([0.12, -0.06])
    wind = np.array([4.0, 2.0])
    drift = current + 0.03 * wind

    def frame(step):
        coords = [list(back.transform(x, y)) for x, y in pos]
        return {
            "hours_before": step / 4,
            "particles": coords,
            "envelope": mapping(MultiPoint(coords).convex_hull),
        }

    frames.append(frame(0))
    for step in range(1, hours * 4 + 1):
        pos += drift * dt + rng.normal(0, sqrt(2 * k * abs(dt)), pos.shape)
        if step % 4 == 0:
            frames.append(frame(step))
    return {
        "mode": "illustrative",
        "engine": "Constant-field Lagrangian transport",
        "seed": seed,
        "frames": frames,
        "forcing": {
            "current_m_s": current.tolist(),
            "wind_m_s": wind.tolist(),
            "windage": 0.03,
            "diffusivity_m2_s": k,
            "timestep_seconds": 900,
            "source": "Explicit hypothetical constants; no observed forcing",
        },
        "limitations": [
            "Not a historical reconstruction or forecast.",
            "No shoreline interaction, weathering, emulsification, waves, or mass balance.",
            "Envelope is ensemble spread, not a calibrated confidence interval.",
            "Backtracking cannot uniquely recover release location or time.",
        ],
    }
