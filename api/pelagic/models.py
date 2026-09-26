"""Response contracts keep public records separate from investigation-only evidence."""

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel


class CaseSummary(BaseModel):
    id: str
    title: str
    trigger: Literal["ais", "sar"]
    status: Literal["under_review", "needs_evidence", "closed"]
    published: bool
    exercise: bool
    summary: str
    version: int
    created_at: datetime
    observed_at: datetime | None
    area_km2: float | None
    polygon_count: int | None
    temporal_precision: str | None
    lon: float | None
    lat: float | None
    observation_id: str | None
    track_id: str | None


class Observation(BaseModel):
    id: str
    title: str
    observed_at: datetime
    temporal_precision: str
    source: dict[str, Any]
    area_km2: float
    polygon_count: int
    geometry: dict[str, Any]


class PublicCase(CaseSummary):
    observation: Observation | None


class InvestigationCase(PublicCase):
    findings: dict[str, Any]
    tracks: list[dict[str, Any]]
    ranking: list[dict[str, Any]]
    anomalies: list[dict[str, Any]]
    reviews: list[dict[str, Any]]
    ranking_method: dict[str, Any]
    timeline: list[dict[str, Any]] | None = None
    sar_footprint: dict[str, Any] | None = None
