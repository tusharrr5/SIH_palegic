"""Read-only recording preflight, except for an audited login/logout session."""

from pathlib import Path
import json, hashlib
import httpx

ROOT = Path(__file__).resolve().parents[1]
for entry in json.loads((ROOT / "data/source/manifest.json").read_text()):
    assert (
        hashlib.sha256((ROOT / "data/source" / entry["file"]).read_bytes()).hexdigest()
        == entry["sha256"]
    ), entry["file"]
print("PASS: source cache checksums")
with httpx.Client(
    base_url="http://127.0.0.1:3100",
    headers={"Origin": "http://127.0.0.1:3100"},
    timeout=20,
) as client:
    assert client.get("/api/health").json()["status"] == "ok"
    cases = client.get("/api/public/cases").json()
    assert len(cases) == 3
    assert client.get("/api/cases").status_code == 401
    credentials = json.loads((ROOT / ".runtime/demo-accounts.json").read_text())
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@pelagic.local",
            "password": credentials["admin@pelagic.local"],
        },
    )
    assert response.status_code == 200, response.text
    overview = client.get("/api/admin/overview").json()
    assert all(d["verified"] for d in overview["datasets"])
    tracks = client.get("/api/tracks").json()
    recorded = [t for t in tracks if t["provenance"].get("kind") == "recorded_archive"]
    assert len(recorded) == 3
    first = recorded[0]
    replay = client.get(
        f"/api/tracks/{first['id']}/replay", params={"at": first["start_at"]}
    ).json()
    assert replay["position"]["quality"] == "received"
    assert credentials["admin@pelagic.local"] in (ROOT / "README.md").read_text()
    assert client.get("/data/land.geojson").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
print(
    "PASS: frontend, API, database, published archive, RBAC, documented admin sign-in, recorded AIS replay and local basemap"
)
print(
    "Ready to record at http://127.0.0.1:3100 (keep PostgreSQL, API and web server running)."
)
