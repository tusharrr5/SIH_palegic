import type { Geometry } from "geojson";
export type User = {
  id: string;
  email: string;
  name: string;
  role: "public" | "authority" | "admin";
};
export type CaseSummary = {
  id: string;
  title: string;
  trigger: "sar" | "ais";
  status: string;
  published: boolean;
  exercise: boolean;
  summary: string;
  version: number;
  observed_at: string | null;
  area_km2: number | null;
  polygon_count: number | null;
  lon: number | null;
  lat: number | null;
  observation_id: string | null;
  track_id: string | null;
};
export type AISPoint = {
  time: string;
  lon: number;
  lat: number;
  sog: number | null;
  cog: number | null;
};
export type Track = {
  id: string;
  name: string;
  points: AISPoint[];
  synthetic: boolean;
  provenance: {
    provider: string;
    description: string;
    provenance_class?: string;
    ui_label?: string;
    ui_warning?: string;
    kind?: string;
    mmsi?: string;
    region?: string;
    url?: string;
    license?: string;
    license_url?: string;
    time_basis?: string;
    transformation?: string;
    source_sha256?: string;
  };
};
export type TrackSummary = Omit<Track, "points"> & {
  report_count: number;
  start_at: string;
  end_at: string;
};
export type MapDetail = Pick<
  CaseDetail,
  "id" | "trigger" | "observation" | "tracks" | "exercise" | "findings"
>;
export type Ranking = {
  id: string;
  name: string;
  synthetic: boolean;
  score: number;
  candidate_score?: number;
  distance_km: number;
  coverage: number;
  nearest_time: string;
  components: { proximity: number; temporal: number; behavior: number };
  vessel_name?: string;
  vessel_type?: string;
  imo?: number;
  flag?: string;
  provenance_class?: string;
  time_diff_hours?: number;
  gap_minutes?: number;
  evidence_statements?: string[];
  why_ranked_first?: string;
  disclaimer?: string;
  caveat?: string;
};
export type TimelineEvent = {
  event_id: string;
  timestamp: string;
  event_type: string;
  title: string;
  description: string;
  source: string;
  provenance_class: string;
  is_synthetic?: boolean;
  is_illustrative?: boolean;
  data_status?: string;
  related_entity_ids?: string[];
  spatial?: { lat: number; lon: number };
  ui_warning?: string;
  citation_or_dataset_identifier?: string;
};
export type Observation = {
  id: string;
  title: string;
  geometry: Geometry;
  source: {
    provider: string;
    label: string;
    url: string;
    license: string;
    license_url: string;
    certainty: string;
    precision: string;
    sensor: string;
  };
  area_km2: number;
  polygon_count: number;
  observed_at: string;
};
export type CaseDetail = CaseSummary & {
  observation: Observation | null;
  tracks?: Track[];
  ranking?: Ranking[];
  timeline?: TimelineEvent[];
  sar_footprint?: Geometry;
  anomalies?: {
    kind: string;
    time: string;
    label: string;
    meaning: string;
    track_id: string;
  }[];
  reviews?: {
    id: string;
    note: string;
    status: string;
    created_at: string;
    author: string;
  }[];
  findings?: {
    reason?: string;
    historical_source?: {
      name: string;
      lon: number;
      lat: number;
      status: string;
      url: string;
    };
    collision_site?: {
      lat: number;
      lon: number;
      status: string;
      source: string;
      provenance_class: string;
    };
    sar_search?: { matched: boolean; result: string };
    sar_footprint?: Geometry;
    sar_scene_id?: string;
    sar_product_name?: string;
    timeline?: TimelineEvent[];
    vessels_involved?: {
      name: string;
      type: string;
      flag: string;
      imo: number;
      role_in_incident: string;
    }[];
    metocean_status?: {
      wind?: string;
      currents?: string;
      sar_status?: string;
    };
    ais_status?: string;
    slick_provenance?: string;
    known_spill_volume_tonnes?: number;
    affected_coastline_km?: number;
    public_sources?: string[];
    provenance_note?: string;
  };
};
export type Reconstruction = {
  mode: string;
  engine: string;
  frames: { hours_before: number; particles: number[][]; envelope: Geometry }[];
  forcing: {
    current_m_s: number[];
    wind_m_s: number[];
    windage: number;
    diffusivity_m2_s: number;
    source: string;
  };
  limitations: string[];
};
export type Catalog = {
  observations: { id: string; title: string }[];
  tracks: { id: string; name: string; synthetic: boolean }[];
};
export type AdminData = {
  users: User[];
  datasets: {
    file: string;
    sha256: string;
    verified: boolean;
    bytes: number;
    retrieved_at: string;
    feature_count: number;
    url: string;
  }[];
  audit: {
    id: number;
    actor: string;
    action: string;
    entity_id: string | null;
    created_at: string;
  }[];
  counts: { observations: number; tracks: number; cases: number };
};
