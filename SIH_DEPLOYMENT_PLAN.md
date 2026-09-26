# PALEGIC SIH 2026 — Production Deployment Plan

**Problem Statement ID:** 26143  
**Product:** PALEGIC — Explainable Oil Spill Investigation & Vessel Attribution  
**Team:** Ekatva  
**Demonstration Cases:** SIH-ENNORE-2017 (SAR-First Canonical) & INV-6011ADAF (AIS-First Surveillance)

---

## 1. Recommended Hosting Architecture

For maximum reliability during judge evaluations and SIH presentations, the simplest, most durable deployment architecture that requires **zero code changes** is a **Unified VPS or Containerized Host (Docker Compose)**:

```
                  Internet (HTTPS Port 443)
                             │
                     Reverse Proxy (Nginx / Caddy)
                     Automatic Let's Encrypt SSL
                             │
            ┌────────────────┴────────────────┐
            │                                 │
     Next.js (Port 3100)              FastAPI (Port 8100)
    (Next rewrites /api/*)                     │
            │                                  │
      Static assets & UI              PostgreSQL 17 + PostGIS 3.5
                                      (Local socket or internal network)
```

### Why this architecture is optimal for SIH:
1. **Zero CORS & Zero Cookie Domain Friction**: The Next.js frontend rewrites all `/api/*` requests to the FastAPI backend internally (`next.config.ts`), ensuring `credentials: "same-origin"` cookies and session tokens work seamlessly without cross-origin configuration errors.
2. **Deterministic Latency**: Eliminates cold starts, serverless spin-up timeouts, and ephemeral filesystem resets during live evaluations.
3. **Reproducible Environment**: PostgreSQL 17 with PostGIS 3.5 is colocated on the same internal network, guaranteeing instantaneous spatial query responses (<10ms).

---

## 2. Frontend Deployment Target

- **Framework**: Next.js 15 (Node.js 20+ runtime).
- **Hosting Target**: Node.js server container / PM2 process on Linux VPS (Ubuntu 24.04 LTS / Debian 12) or PaaS with persistent Node runtime (Railway / Render / Fly.io).
- **Port**: `3100` (internal).

---

## 3. Backend Deployment Target

- **Framework**: FastAPI (Python 3.12+).
- **ASGI Server**: `uvicorn` (with 2–4 workers).
- **Hosting Target**: Systemd service, PM2, or Docker container on the same host/private network as the frontend.
- **Port**: `8100` (internal).

---

## 4. PostgreSQL / PostGIS Requirement

- **Engine**: PostgreSQL 17.
- **Extension**: PostGIS 3.5 (`postgis`).
- **Prerequisites**:
  - Spatial indexing support (`GiST` indexes on `observations.geometry` and `tracks.points`).
  - Native spatial distance queries (`ST_DWithin`, `ST_Intersects`, `geography` type casting).

---

## 5. Required Environment Variables (Names Only)

> [!IMPORTANT]
> Values are confidential runtime secrets and must NEVER be committed to Git or published in documentation.

### Backend (`api/.env` or Host Environment):
- `DATABASE_URL` (Connection string to PostgreSQL with PostGIS)
- `ORIGIN` (Allowed HTTP/HTTPS origin for the frontend)
- `SECRET_KEY` (Key used for session token signing and verification)
- `ENVIRONMENT` (`production` or `development`)

### Frontend (`apps/web/.env.production` or Host Environment):
- `API_URL` (Internal URL of the FastAPI service, e.g., `http://127.0.0.1:8100`)
- `NODE_ENV` (`production`)
- `PORT` (`3100`)

---

## 6. Build Commands

```bash
# 1. Python virtual environment & backend dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Node.js & frontend production bundle
cd apps/web
npm ci
npm run build
cd ../..
```

---

## 7. Start Commands

### Backend Service:
```bash
.venv/bin/uvicorn pelagic.main:app \
  --app-dir api \
  --host 127.0.0.1 \
  --port 8100 \
  --workers 2
```

### Frontend Service:
```bash
npm --prefix apps/web run start
```

---

## 8. CORS Requirements

Because Next.js proxies `/api/*` requests server-side through `apps/web/next.config.ts`, browser requests to `/api` are **same-origin**.

However, for direct API communication or defense-in-depth:
- Backend `main.py` enforces CORS middleware for the configured `ORIGIN` header.
- In production, set `ORIGIN` to match the exact public HTTPS domain (e.g., `https://palegic.maritime.gov.in` or `https://palegic.yourdomain.com`).

---

## 9. Frontend API URL Configuration

In `apps/web/next.config.ts`:
```typescript
{
  source: "/api/:path*",
  destination: `${process.env.API_URL || "http://127.0.0.1:8100"}/api/:path*`,
}
```
Setting `API_URL=http://127.0.0.1:8100` allows the Next.js production server to route all API calls locally without network overhead.

---

## 10. Database Initialization & Seed Procedure

Both database bootstrap and incident seeding scripts are **strictly idempotent** (`ON CONFLICT DO NOTHING`):

```bash
# 1. Initialize schema, create roles, and seed baseline observations
.venv/bin/python scripts/bootstrap.py

# 2. Seed canonical Ennore 2017 incident package
.venv/bin/python scripts/seed_ennore.py
```

---

## 11. Persistent vs Ephemeral Filesystem Considerations

- **Cache Directories**: `apps/web/public/maplibre/` contains cached maplibre worker scripts generated during `prebuild`. These are committed/built statically and require no runtime write access.
- **Session State**: User sessions and audit trails are stored in PostgreSQL (`sessions`, `audit` tables).
- **Static Assets**: GeoJSON charts and incident data packages (`data/demo/ennore-2017/`) are read-only static files bundled into the deployment repository.
- **Result**: The application can run safely on a read-only container filesystem with standard `/tmp` scratch access.

---

## 12. Health-Check Endpoint

- **Backend Health Check**: `GET /api/health`
  - Validates active database connectivity (`SELECT 1`).
  - Returns: `{"status": "ok", "db": true}` (HTTP 200).
- **Frontend Health Check**: `GET /`
  - Returns: HTTP 200 with server-rendered HTML shell.

---

## 13. Expected Final Stable HTTPS URLs

For production presentation:
- **Application URL**: `https://<custom-domain-or-subdomain>/`
- **Canonical Incident Demo**: `https://<custom-domain-or-subdomain>/?demo=true`
- **Health Check**: `https://<custom-domain-or-subdomain>/api/health`

---

## 14. Rollback Procedure

1. **Previous Build Retention**: Maintain previous Next.js production builds in `.next.old` or tag Docker container images with git commit hashes (`palegic:v0.1.0-alpha`).
2. **Zero-Migration Rollback**: Because migrations use immutable additive tables (`cases`, `tracks`, `observations`), rolling back the application code requires only:
   ```bash
   git checkout <previous-stable-tag>
   npm --prefix apps/web run build
   # Restart systemd / PM2 / Docker services
   ```
3. **Database Restore**: Standard PostGIS dump snapshot (`pg_dump -Fc maritime_oil_v2 > backup.dump`) can be restored via `pg_restore` if needed.
