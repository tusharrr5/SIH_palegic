import pytest
from datetime import datetime


def test_1_ais_first_begins_without_visible_slick(authority):
    """1. AIS-FIRST begins without visible slick."""
    r = authority.get("/api/cases/INV-6011ADAF")
    assert r.status_code == 200
    case = r.json()
    assert case["trigger"] == "ais"
    findings = case["findings"]
    assert "slick_reveal_time" in findings
    slick_reveal = datetime.fromisoformat(findings["slick_reveal_time"].replace("Z", "+00:00"))
    surveillance_start = datetime.fromisoformat("2010-05-17T06:00:00+00:00")
    
    # At surveillance start, the slick must NOT be revealed
    assert surveillance_start < slick_reveal


def test_2_normal_vessel_trajectory_appears_first(authority):
    """2. Normal vessel trajectory appears first."""
    r = authority.get("/api/tracks/demo-1")
    assert r.status_code == 200
    track = r.json()
    points = track["points"]
    assert len(points) >= 10

    # Normal navigation window: 06:00 - 06:35 UTC
    normal_pts = [
        p for p in points
        if "2010-05-17T06:00:00" <= p["time"] <= "2010-05-17T06:35:00"
    ]
    assert len(normal_pts) >= 3
    for p in normal_pts:
        sog = p.get("sog")
        assert sog is not None
        assert 10.0 <= sog <= 14.0  # Normal cruising speed ~12.1 kn

    # Replay query at early normal timestamp
    rep = authority.get(
        "/api/tracks/demo-1/replay",
        params={"at": "2010-05-17T06:15:00Z"},
    ).json()
    assert rep["position"] is not None
    assert rep["position"]["quality"] in ("received", "interpolated")


def test_3_anomaly_appears_at_correct_timestamp(authority):
    """3. Anomaly appears at correct timestamp."""
    r = authority.get("/api/cases/INV-6011ADAF")
    assert r.status_code == 200
    case = r.json()
    anomalies = case.get("anomalies", [])

    # The anomaly alert is triggered at 07:00:00Z
    alert_anomalies = [
        a for a in anomalies
        if a.get("time") == "2010-05-17T07:00:00Z" or "07:00" in str(a.get("time"))
    ]
    assert len(alert_anomalies) >= 1
    alert = alert_anomalies[0]
    assert "Anomaly" in alert.get("label", "") or alert.get("kind") == "anomaly_alert"
    assert round(alert.get("lat", 0), 2) == 28.48
    assert round(alert.get("lon", 0), 2) == -89.28


def test_4_one_vessel_becomes_investigation_focus(authority):
    """4. One vessel becomes investigation focus."""
    r = authority.get("/api/cases/INV-6011ADAF")
    assert r.status_code == 200
    case = r.json()

    # AIS-FIRST focuses on 1 investigated vessel, not multiple competing candidates
    tracks = case["tracks"]
    assert len(tracks) == 1
    assert tracks[0]["id"] == "demo-1"

    ranking = case["ranking"]
    assert len(ranking) == 1
    primary = ranking[0]
    assert primary["id"] == "demo-1"
    assert "why_flagged" in primary
    assert len(primary["why_flagged"]) >= 3


def test_5_sar_verification_begins_only_after_anomaly(authority):
    """5. SAR verification begins only after anomaly."""
    r = authority.get("/api/cases/INV-6011ADAF")
    assert r.status_code == 200
    findings = r.json()["findings"]

    sar_request_time = datetime.fromisoformat(
        findings["sar_verification_requested_at"].replace("Z", "+00:00")
    )
    anomaly_threshold_time = datetime.fromisoformat("2010-05-17T07:00:00+00:00")

    # SAR verification is requested strictly after the anomaly threshold
    assert sar_request_time > anomaly_threshold_time
    assert findings["sar_search_radius_km"] == 25


def test_6_slick_appears_only_during_sar_verification_stage(authority):
    """6. Slick appears only during SAR verification/result stage."""
    r = authority.get("/api/cases/INV-6011ADAF")
    assert r.status_code == 200
    findings = r.json()["findings"]

    sar_obs_time = datetime.fromisoformat(
        findings["sar_observation_time"].replace("Z", "+00:00")
    )
    slick_reveal_time = datetime.fromisoformat(
        findings["slick_reveal_time"].replace("Z", "+00:00")
    )

    # Observation at 08:00 UTC, slick revealed at 08:15 UTC
    assert sar_obs_time >= datetime.fromisoformat("2010-05-17T08:00:00+00:00")
    assert slick_reveal_time >= sar_obs_time


def test_7_replay_restart_is_deterministic(authority):
    """7. Replay restart is deterministic."""
    case_id = "INV-6011ADAF"
    t_start = "2010-05-17T06:00:00Z"

    results = []
    for _ in range(5):
        res = authority.get(f"/api/cases/{case_id}/replay", params={"at": t_start}).json()
        results.append(res)

    first = results[0]
    for other in results[1:]:
        assert other == first, "Replay restart must produce strictly deterministic results"


def test_8_scrubbing_reconstructs_correct_state(authority):
    """8. Scrubbing reconstructs correct state."""
    case_id = "INV-6011ADAF"
    timestamps = [
        "2010-05-17T06:15:00Z",
        "2010-05-17T06:45:00Z",
        "2010-05-17T07:00:00Z",
        "2010-05-17T07:45:00Z",
        "2010-05-17T08:30:00Z",
    ]

    forward_states = {}
    for ts in timestamps:
        forward_states[ts] = authority.get(
            f"/api/cases/{case_id}/replay", params={"at": ts}
        ).json()

    # Scrub backwards in reverse order
    for ts in reversed(timestamps):
        scrubbed = authority.get(
            f"/api/cases/{case_id}/replay", params={"at": ts}
        ).json()
        assert scrubbed == forward_states[ts], f"Scrubbing to {ts} must match forward state"


def test_9_ais_first_and_sar_first_remain_separate_workflows(authority):
    """9. AIS-FIRST and SAR-FIRST remain separate workflows."""
    ais_case = authority.get("/api/cases/INV-6011ADAF").json()
    sar_case = authority.get("/api/cases/SIH-ENNORE-2017").json()

    assert ais_case["trigger"] == "ais"
    assert sar_case["trigger"] == "sar"

    # AIS-FIRST focuses on 1 investigated vessel
    assert len(ais_case["tracks"]) == 1
    assert len(ais_case["ranking"]) == 1
    assert ais_case["ranking"][0]["status"] == "HIGH-PRIORITY CANDIDATE"

    # SAR-FIRST compares multiple candidates
    assert len(sar_case["tracks"]) >= 2
    assert len(sar_case["ranking"]) >= 2


def test_10_candidate_result_uses_decision_support_language(authority):
    """10. Candidate result uses attribution/decision-support language rather than claiming legal certainty."""
    case = authority.get("/api/cases/INV-6011ADAF").json()
    ranking = case["ranking"]
    assert len(ranking) > 0
    candidate = ranking[0]

    # Attribution language
    assert candidate["status"] == "HIGH-PRIORITY CANDIDATE"
    assert "score" in candidate
    assert "why_flagged" in candidate

    # Prohibited certainty words
    prohibited = ["guilty", "convicted", "culprit", "legal responsibility", "liable"]
    decision_text = (
        candidate.get("decision_support", "") + " " + " ".join(candidate.get("why_flagged", []))
    ).lower()
    for word in prohibited:
        assert word not in decision_text, f"Legal certainty word '{word}' found in decision support text"

    # Data honesty
    findings = case["findings"]
    provenance = findings.get("data_provenance", {})
    assert "SYNTHETIC" in provenance.get("ais", "")
    assert "NOT LOADED" in provenance.get("metocean", "")
