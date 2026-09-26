# PALEGIC SIH 2026 — Vercel + Render Cloud Deployment Guide

**Problem Statement ID:** 26143  
**Team:** Ekatva  
**System:** PALEGIC Explainable Maritime Intelligence  
**Architecture:** Vercel (Next.js Frontend) $\rightarrow$ Render (FastAPI Backend) $\rightarrow$ Cloud PostgreSQL + PostGIS Database  

---

## Architecture Overview

```
                      Internet / SIH Judges
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │               VERCEL (apps/web)              │
        │             Next.js 15 Production            │
        │      https://<your-project>.vercel.app       │
        └──────────────────────┬───────────────────────┘
                               │
                               │ /api/* (server-side proxy rewrite)
                               ▼
        ┌──────────────────────────────────────────────┐
        │             RENDER (api/ + root)             │
        │        FastAPI Native Python Service         │
        │     https://<your-backend>.onrender.com      │
        └──────────────────────┬───────────────────────┘
                               │
                               │ SQL + PostGIS queries
                               ▼
        ┌──────────────────────────────────────────────┐
        │           CLOUD POSTGRESQL + POSTGIS         │
        │        (Supabase / Neon / Render PG)         │
        └──────────────────────────────────────────────┘
```

---

## Step 1: Provision Cloud Database with PostGIS

> [!IMPORTANT]
> **PostGIS is strictly required.** Standard PostgreSQL without PostGIS cannot store `geometry(MultiPolygon,4326)` or execute spatial functions (`ST_DWithin`, `ST_Centroid`, `ST_AsGeoJSON`).

### Option A: Supabase (Recommended — Free & Instant PostGIS)
1. Go to [supabase.com](https://supabase.com) and create a free project (e.g. `palegic-db`).
2. Go to **Project Settings** $\rightarrow$ **Database** $\rightarrow$ **Connection string** $\rightarrow$ **URI**.
3. Copy the URI (format: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`).
4. In the **SQL Editor**, verify PostGIS is enabled:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

### Option B: Render PostgreSQL
1. On [render.com](https://dashboard.render.com), click **New +** $\rightarrow$ **PostgreSQL**.
2. Name: `palegic-db`, Database: `pelagic_db`, User: `pelagic_user`.
3. Copy the **Internal Database URL** (for Render services) or **External Database URL** (for remote scripts).
4. Connect via psql and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

### Option C: Neon (Serverless PostgreSQL)
1. On [neon.tech](https://neon.tech), create a project.
2. In the SQL Console, run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
3. Copy the connection string.

---

## Step 2: Initialize & Seed the Cloud Database

From your local machine (inside the `Maritime-main` repository):

```bash
# 1. Export your cloud database connection string
export DATABASE_URL="postgresql://user:password@host:5432/dbname"

# 2. Run idempotent schema & catalog bootstrap
.venv/bin/python scripts/bootstrap.py

# 3. Seed canonical SIH-ENNORE-2017 historical benchmark
.venv/bin/python scripts/seed_ennore.py
```

Both scripts are completely idempotent (`ON CONFLICT DO NOTHING`) and will never delete or overwrite existing records.

---

## Step 3: Deploy FastAPI Backend to Render

1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository (`Maritime-main` or your fork).
4. Configure the service settings:
   - **Name:** `palegic-api` (or your choice)
   - **Region:** Singapore / Frankfurt / Oregon (choose closest to India / evaluation)
   - **Branch:** `main`
   - **Root Directory:** *(leave blank — defaults to repository root)*
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn pelagic.main:app --app-dir api --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type:** `Free` (or `Starter`)

5. Add **Environment Variables**:
   | Variable | Value | Notes |
   |---|---|---|
   | `DATABASE_URL` | `postgresql://...` | Connection string from Step 1 |
   | `SECRET_KEY` | `$(openssl rand -hex 32)` | Session cryptographic secret |
   | `ORIGIN` | `https://<your-vercel-app>.vercel.app` | Vercel production frontend domain |
   | `PYTHON_VERSION` | `3.12.0` | Recommended Python version |

6. Click **Create Web Service**.
7. Once deployment succeeds, Render gives you a public URL:  
   `https://palegic-api.onrender.com`
8. Verify health endpoint in browser:  
   `https://palegic-api.onrender.com/api/health` $\rightarrow$ returns `{"status":"ok", ...}`

---

## Step 4: Deploy Next.js Frontend to Vercel

1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Import your GitHub repository (`Maritime-main`).
4. In the Project Configuration:
   - **Framework Preset:** `Next.js` (auto-detected)
   - **Root Directory:** Click **Edit** and select:
     ```text
     apps/web
     ```
   - **Build Command:** `next build` (default)
   - **Output Directory:** `.next` (default)
   - **Install Command:** `npm install` (default)

5. In **Environment Variables**, add:
   | Variable | Value | Notes |
   |---|---|---|
   | `API_URL` | `https://palegic-api.onrender.com` | Your Render backend URL from Step 3 (no trailing slash) |

6. Click **Deploy**.
7. Vercel will build and assign your domain:  
   `https://palegic.vercel.app` (or similar).

---

## Step 5: Final Validation & Live Presentation URL

1. Go back to Render $\rightarrow$ `palegic-api` $\rightarrow$ **Environment Variables**.
2. Ensure `ORIGIN` is set to your actual Vercel URL:
   ```text
   ORIGIN=https://<your-project>.vercel.app
   ```
3. Open in an Incognito / Private browser:
   ```text
   https://<your-project>.vercel.app/?demo=true
   ```
4. Verify both operational journeys:
   - **SAR-FIRST:** Click **RUN SIH DEMO** $\rightarrow$ Ennore incident loads $\rightarrow$ Map renders $\rightarrow$ Candidates ranked $\rightarrow$ Replay works $\rightarrow$ Report opens.
   - **AIS-FIRST:** Click **AIS FIRST** $\rightarrow$ Normal surveillance at 06:00 UTC $\rightarrow$ Vessel anomaly at 07:00 UTC $\rightarrow$ Targeted satellite reveal at 08:15 UTC $\rightarrow$ Evidence Score: 76 / 100 $\rightarrow$ Report opens.
