import numpy as np
from shapely.geometry import shape
from pelagic.analytics import (
    normalize,
    anomalies,
    interpolate,
    distance_km,
    rank_sources,
    particle_backtrack,
)


def p(time, lon=0, lat=0, sog=10, cog=90):
    return dict(time=f"2020-01-01T{time}:00+00:00", lon=lon, lat=lat, sog=sog, cog=cog)


def test_normalization_sort_and_duplicate():
    points = normalize([p("01:00", 1), p("00:00"), p("01:00", 2)])
    assert len(points) == 2 and points[0]["lon"] == 0 and points[1]["lon"] == 2


def test_geodesic_interpolation_and_no_extrapolation():
    points = [p("00:00", 179.9), p("00:30", -179.9)]
    at = interpolate(points, "2020-01-01T00:15:00Z")
    assert abs(abs(at["lon"]) - 180) < 1e-6 and at["quality"] == "interpolated"
    assert interpolate(points, "2019-12-31T23:00:00Z") is None
    assert interpolate(points, "2020-01-01T00:00:00Z")["quality"] == "received"


def test_long_gaps_are_not_interpolated():
    assert interpolate([p("00:00"), p("02:00", 1)], "2020-01-01T01:00:00Z") is None


def test_anomalies_turn_wraparound_and_gap_not_accusation():
    assert anomalies([p("00:00", cog=359), p("00:30", cog=1)]) == []
    result = anomalies([p("00:00"), p("00:30", sog=1, cog=200), p("02:00")])
    assert {x["kind"] for x in result} == {"slowdown", "course_change", "reporting_gap"}
    assert "not proof" in result[-1]["meaning"]
    assert [e["kind"] for e in anomalies([p("00:00"), p("02:00", sog=1, cog=200)])] == [
        "reporting_gap"
    ]


GEOMETRY = {
    "type": "Polygon",
    "coordinates": [
        [[-0.02, -0.02], [0.02, -0.02], [0.02, 0.02], [-0.02, 0.02], [-0.02, -0.02]]
    ],
}


def test_rank_uses_spatiotemporal_gates_and_gap_penalty():
    complete = [p("00:00"), p("00:30"), p("01:00"), p("01:30"), p("02:00")]
    tracks = [
        {"id": "a", "name": "Complete", "synthetic": True, "points": complete},
        {
            "id": "b",
            "name": "Gapped",
            "synthetic": True,
            "points": [complete[0], complete[-1]],
        },
        {
            "id": "far",
            "name": "Far",
            "synthetic": True,
            "points": [p("00:00", 10), p("00:30", 10)],
        },
        {
            "id": "old",
            "name": "Old",
            "synthetic": True,
            "points": [
                dict(x, time=x["time"].replace("2020", "2010")) for x in complete
            ],
        },
    ]
    ranked = rank_sources(GEOMETRY, "2020-01-01T01:00:00Z", tracks)
    assert [r["id"] for r in ranked] == ["a", "b"]
    assert ranked[0]["score"] > ranked[1]["score"] and ranked[1]["coverage"] < 1


def test_particle_integrator_units_direction_and_reproducibility():
    a = particle_backtrack(GEOMETRY, 6)
    b = particle_backtrack(GEOMETRY, 6)
    assert a == b and len(a["frames"]) == 7 and len(a["frames"][0]["particles"]) == 160
    initial = np.array(a["frames"][0]["particles"])
    end = np.array(a["frames"][-1]["particles"])
    assert all(
        shape(GEOMETRY).covers(__import__("shapely").geometry.Point(x)) for x in initial
    )
    # westward 0.24 m/s * 21600 s = 5.184 km; diffusion averages around zero.
    delta = distance_km(initial.mean(axis=0), end.mean(axis=0))
    assert 4.8 < delta < 5.6 and end[:, 0].mean() < initial[:, 0].mean()
    assert (
        a["mode"] == "illustrative" and "no observed forcing" in a["forcing"]["source"]
    )
