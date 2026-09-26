CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS users (
 id uuid PRIMARY KEY, email text UNIQUE NOT NULL, name text NOT NULL,
 password_hash text NOT NULL, role text NOT NULL CHECK(role IN ('public','authority','admin')),
 active boolean NOT NULL DEFAULT true, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash text PRIMARY KEY, user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 expires_at timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS observations (
 id text PRIMARY KEY, title text NOT NULL, observed_at timestamptz NOT NULL,
 temporal_precision text NOT NULL, geometry geometry(MultiPolygon,4326) NOT NULL,
 source jsonb NOT NULL, area_km2 double precision NOT NULL, polygon_count integer NOT NULL,
 CHECK(ST_IsValid(geometry))
);
CREATE INDEX IF NOT EXISTS observations_geom_idx ON observations USING gist(geometry);
CREATE TABLE IF NOT EXISTS tracks (
 id text PRIMARY KEY, name text NOT NULL, provenance jsonb NOT NULL,
 points jsonb NOT NULL, geometry geometry(LineString,4326) NOT NULL,
 synthetic boolean NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS tracks_geom_idx ON tracks USING gist(geometry);
CREATE TABLE IF NOT EXISTS cases (
 id text PRIMARY KEY, title text NOT NULL, trigger text NOT NULL CHECK(trigger IN ('sar','ais')),
 observation_id text REFERENCES observations(id), track_id text REFERENCES tracks(id),
 status text NOT NULL DEFAULT 'under_review' CHECK(status IN ('under_review','needs_evidence','closed')),
 published boolean NOT NULL DEFAULT false, exercise boolean NOT NULL DEFAULT false,
 summary text NOT NULL, findings jsonb NOT NULL DEFAULT '{}'::jsonb,
 version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS reviews (
 id uuid PRIMARY KEY, case_id text NOT NULL REFERENCES cases(id),
 author_id uuid NOT NULL REFERENCES users(id), status text NOT NULL, note text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS audit (
 id bigserial PRIMARY KEY, actor_id uuid REFERENCES users(id), action text NOT NULL,
 entity_id text, detail jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now()
);
