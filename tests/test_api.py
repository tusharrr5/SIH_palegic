import uuid, hashlib
import pytest
from pelagic.db import connection


@pytest.mark.parametrize(
    "path",
    [
        "/api/cases",
        "/api/catalog",
        "/api/cases/HIST-1705",
        "/api/cases/HIST-1705/export",
        "/api/cases/HIST-1705/replay?at=2010-05-17T12:00:00Z",
        "/api/admin/overview",
    ],
)
def test_anonymous_cannot_read_protected_endpoints(client, path):
    assert client.get(path).status_code == 401


def test_public_payload_has_no_private_evidence(client):
    rows = client.get("/api/public/cases").json()
    assert len(rows) >= 3
    for row in rows:
        detail = client.get("/api/public/cases/" + row["id"]).json()
        assert detail["observation"]["geometry"]["type"] == "MultiPolygon"
        assert not {"ranking", "tracks", "reviews", "findings"} & detail.keys()


def test_cookie_login_logout_expiry(client):
    r = client.post(
        "/api/auth/login",
        json={"email": "authority@test.local", "password": "test-password-only"},
    )
    assert (
        r.status_code == 200
        and "HttpOnly" in r.headers["set-cookie"]
        and "SameSite=strict" in r.headers["set-cookie"]
    )
    assert client.get("/api/auth/me").json()["role"] == "authority"
    with connection() as conn:
        conn.execute(
            "UPDATE sessions SET expires_at=now()-interval '1 second' WHERE token_hash=%s",
            (hashlib.sha256(client.cookies["pelagic_session"].encode()).hexdigest(),),
        )
    assert client.get("/api/cases").status_code == 401
    assert (
        client.post("/api/auth/logout").status_code == 200
        and client.get("/api/auth/me").json() is None
    )


def test_origin_and_throttle(client):
    body = {"email": "not-real@test.local", "password": "wrong"}
    assert (
        client.post(
            "/api/auth/login", json=body, headers={"Origin": "https://untrusted.test"}
        ).status_code
        == 403
    )
    for _ in range(10):
        assert client.post("/api/auth/login", json=body).status_code == 401
    assert client.post("/api/auth/login", json=body).status_code == 429


def test_public_role_cannot_escalate_by_request(client):
    client.post(
        "/api/auth/login",
        json={
            "email": "public@test.local",
            "password": "test-password-only",
            "role": "admin",
        },
    )
    assert client.get("/api/cases?role=admin").status_code == 403
    assert client.get("/api/admin/overview").status_code == 403
    assert (
        client.post(
            "/api/detections",
            json={"path": "sar", "observation_id": "dwh-2010-05-17", "exercise": True},
        ).status_code
        == 403
    )


def create(authority, path="ais"):
    body = {
        "path": path,
        "track_id": "demo-1",
        "observation_id": "dwh-2010-05-17",
        "exercise": True,
    }
    response = authority.post("/api/detections", json=body)
    assert response.status_code == 200, response.text
    return response.json()["id"], body


@pytest.mark.parametrize("path", ["ais", "sar"])
def test_both_triggers_produce_shared_case_and_idempotency(authority, path):
    cid, body = create(authority, path)
    detail = authority.get("/api/cases/" + cid).json()
    expected_min_ranks = 1 if path == "ais" else 2
    assert len(detail["ranking"]) >= expected_min_ranks and all(t["synthetic"] for t in detail["tracks"])
    assert authority.post("/api/detections", json=body).json()["id"] == cid
    assert authority.get("/api/public/cases/" + cid).status_code == 404
    export = authority.get("/api/cases/" + cid + "/export")
    assert export.status_code == 200 and export.json()["case"]["id"] == cid


def test_review_optimistic_lock_and_attribution(authority):
    cid, _ = create(authority)
    d = authority.get("/api/cases/" + cid).json()
    body = {
        "status": "needs_evidence",
        "note": "Training review: request time-matched wind and current fields.",
        "expected_version": d["version"],
    }
    assert authority.post(f"/api/cases/{cid}/reviews", json=body).status_code == 200
    assert authority.post(f"/api/cases/{cid}/reviews", json=body).status_code == 409
    d = authority.get("/api/cases/" + cid).json()
    assert d["reviews"][0]["author"] == "authority"


def test_historical_reconstruction_is_blocked_and_sandbox_labeled(authority):
    cid, _ = create(authority)
    assert (
        authority.post(
            f"/api/cases/{cid}/reconstruction", json={"mode": "historical"}
        ).status_code
        == 409
    )
    assert (
        authority.post(
            "/api/cases/HIST-1705/reconstruction", json={"mode": "illustrative"}
        ).status_code
        == 409
    )
    r = authority.post(
        f"/api/cases/{cid}/reconstruction", json={"mode": "illustrative", "hours": 6}
    )
    assert r.status_code == 200 and r.json()["mode"] == "illustrative"
    assert (
        authority.post(
            f"/api/cases/{cid}/reconstruction",
            json={"mode": "illustrative", "hours": 999},
        ).status_code
        == 422
    )


def test_server_replay_marks_ais_gap(authority):
    cid, _ = create(authority)
    r = authority.get(f"/api/cases/{cid}/replay?at=2010-05-17T11:00:00Z").json()
    assert next(v for v in r["positions"] if v["id"] == "demo-1")["position"] is None
    assert (
        authority.get(f"/api/cases/{cid}/replay?at=2010-05-17T11:00:00").status_code
        == 422
    )


def test_authority_admin_separation(authority):
    assert authority.get("/api/admin/overview").status_code == 403
    assert authority.post("/api/admin/ais", json={}).status_code == 403
    assert (
        authority.patch(
            f"/api/admin/users/{uuid.uuid4()}/role", json={"role": "admin"}
        ).status_code
        == 403
    )


def test_integrity_and_admin_self_protection(admin):
    d = admin.get("/api/admin/overview").json()
    assert all(x["verified"] for x in d["datasets"])
    me = admin.get("/api/auth/me").json()
    assert (
        admin.patch(
            f"/api/admin/users/{me['id']}/role", json={"role": "public"}
        ).status_code
        == 409
    )
    assert (
        admin.patch(
            f"/api/admin/users/{uuid.uuid4()}/role", json={"role": "public"}
        ).status_code
        == 404
    )


def test_import_validation_and_ais_no_scene_case(admin):
    body = {
        "name": "Test recorded track",
        "provider": "Test source declaration",
        "license": "CC0 test fixture",
        "synthetic": False,
        "points": [
            {"time": "2024-01-01T00:00:00Z", "lon": 70, "lat": 15, "sog": 10, "cog": 0},
            {
                "time": "2024-01-01T02:00:00Z",
                "lon": 70.1,
                "lat": 15.1,
                "sog": 1,
                "cog": 90,
            },
        ],
    }
    response = admin.post("/api/admin/ais", json=body)
    assert response.status_code == 200
    tid = response.json()["id"]
    r = admin.post(
        "/api/detections", json={"path": "ais", "track_id": tid, "exercise": False}
    )
    assert r.status_code == 200
    d = admin.get("/api/cases/" + r.json()["id"]).json()
    assert (
        d["observation"] is None
        and d["status"] == "needs_evidence"
        and not d["ranking"]
    )
    assert (
        admin.post(
            "/api/detections",
            json={"path": "ais", "track_id": "demo-1", "exercise": False},
        ).status_code
        == 422
    )
    body["points"][0]["lon"] = 999
    assert admin.post("/api/admin/ais", json=body).status_code == 422
    body["points"][0]["lon"] = 70
    body["points"][0]["time"] = "2024-01-01T00:00:00"
    assert admin.post("/api/admin/ais", json=body).status_code == 422


def test_role_change_revokes_sessions(admin):
    from fastapi.testclient import TestClient
    from pelagic.main import app
    from pelagic.auth import HASHER

    ident = uuid.uuid4()
    email = f"{ident}@test.local"
    with connection() as conn:
        conn.execute(
            "INSERT INTO users(id,email,name,password_hash,role) VALUES(%s,%s,%s,%s,%s)",
            (
                ident,
                email,
                "Temporary role test",
                HASHER.hash("ephemeral-test-only"),
                "authority",
            ),
        )
    with TestClient(app, headers={"Origin": "http://127.0.0.1:3100"}) as other:
        assert (
            other.post(
                "/api/auth/login",
                json={"email": email, "password": "ephemeral-test-only"},
            ).status_code
            == 200
        )
        assert other.get("/api/cases").status_code == 200
        assert (
            admin.patch(
                f"/api/admin/users/{ident}/role", json={"role": "public"}
            ).status_code
            == 200
        )
        assert other.get("/api/cases").status_code == 401


def test_create_authority_is_admin_only(client):
    body = {
        "name": "New Officer",
        "email": "new-officer@test.local",
        "password": "temporary-officer-2026",
    }
    assert client.post("/api/admin/authorities", json=body).status_code == 401
    for role in ["public", "authority"]:
        client.post(
            "/api/auth/login",
            json={"email": f"{role}@test.local", "password": "test-password-only"},
        )
        assert client.post("/api/admin/authorities", json=body).status_code == 403


def test_create_authority_can_login_and_has_no_admin_privileges(admin):
    from pelagic.auth import HASHER

    body = {
        "name": "  New Harbour Officer  ",
        "email": "  NEW.HARBOUR@TEST.LOCAL ",
        "password": "temporary-officer-2026",
    }
    response = admin.post("/api/admin/authorities", json=body)
    assert response.status_code == 201
    user = response.json()
    assert user["role"] == "authority" and user["email"] == "new.harbour@test.local"
    assert user["name"] == "New Harbour Officer"
    assert "password" not in response.text
    assert admin.post("/api/admin/authorities", json=body).status_code == 409
    with connection() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id=%s", (user["id"],)
        ).fetchone()
        assert HASHER.verify(row["password_hash"], body["password"])
        event = conn.execute(
            "SELECT detail FROM audit WHERE action='authority_created' AND entity_id=%s",
            (user["id"],),
        ).fetchone()
        assert body["password"] not in str(event)
    assert (
        admin.post(
            "/api/auth/login",
            json={"email": user["email"], "password": body["password"]},
        ).status_code
        == 200
    )
    assert admin.get("/api/tracks").status_code == 200
    assert admin.get("/api/cases").status_code == 200
    assert admin.get("/api/admin/overview").status_code == 403
    assert admin.post("/api/admin/authorities", json=body).status_code == 403


def test_create_authority_rejects_role_spoofing_weak_password_and_origin(admin):
    body = {
        "name": "Valid Name",
        "email": "valid@test.local",
        "password": "sufficient-password",
    }
    assert (
        admin.post("/api/admin/authorities", json={**body, "role": "admin"}).status_code
        == 422
    )
    assert (
        admin.post(
            "/api/admin/authorities", json={**body, "password": "short"}
        ).status_code
        == 422
    )
    assert (
        admin.post("/api/admin/authorities", json={**body, "name": "   "}).status_code
        == 422
    )
    assert (
        admin.post(
            "/api/admin/authorities", json={**body, "email": "invalid"}
        ).status_code
        == 422
    )
    assert (
        admin.post(
            "/api/admin/authorities",
            json=body,
            headers={"Origin": "https://untrusted.test"},
        ).status_code
        == 403
    )


def test_recorded_track_library_and_replay(authority):
    tracks = authority.get("/api/tracks").json()
    recorded = [t for t in tracks if t["provenance"].get("kind") == "recorded_archive"]
    assert len(recorded) == 3 and all(not t["synthetic"] for t in recorded)
    assert all("points" not in t for t in tracks)
    for t in recorded:
        d = authority.get("/api/tracks/" + t["id"]).json()
        first = d["points"][0]
        r = authority.get(
            "/api/tracks/" + t["id"] + "/replay", params={"at": first["time"]}
        ).json()
        assert r["position"]["quality"] == "received"
        assert (
            r["position"]["lon"] == first["lon"]
            and r["position"]["lat"] == first["lat"]
        )
        assert (
            authority.get(
                "/api/tracks/" + t["id"] + "/replay?at=2010-05-17T12:00:00Z"
            ).json()["position"]
            is None
        )
    historic = authority.get("/api/cases/HIST-1705").json()
    assert historic["tracks"] == [] and historic["ranking"] == []
    assert authority.get("/api/tracks/absent").status_code == 404
    assert (
        authority.get(
            "/api/tracks/" + recorded[0]["id"] + "/replay?at=2017-07-05T12:00:00"
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "path",
    [
        "/api/tracks",
        "/api/tracks/recorded-dma-265410000",
        "/api/tracks/recorded-dma-265410000/replay?at=2017-07-05T09:00:00Z",
    ],
)
def test_track_endpoints_require_authority(client, path):
    assert client.get(path).status_code == 401
    client.post(
        "/api/auth/login",
        json={"email": "public@test.local", "password": "test-password-only"},
    )
    assert client.get(path).status_code == 403
