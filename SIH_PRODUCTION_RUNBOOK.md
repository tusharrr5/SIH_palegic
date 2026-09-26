# PALEGIC SIH 2026 — Production Deployment Runbook

**Product:** PALEGIC · Explainable Oil Spill Investigation & Vessel Attribution System  
**Problem Statement ID:** 26143  
**Team:** Ekatva  
**Target Environment:** Unified Production Host (Ubuntu 22.04 / 24.04 LTS or Debian 12)  
**Document Revision:** 1.0 (Production Release)

---

## 1. Architecture Overview

PALEGIC utilizes a unified host deployment architecture orchestrated by Docker Compose:

```
                  Internet (HTTPS:443 / HTTP:80)
                                │
                        ┌───────▼───────┐
                        │ Reverse Proxy │
                        │    (Nginx)    │
                        └───────┬───────┘
                                │
               ┌────────────────┴────────────────┐
               │                                 │
        / (Web traffic)                   /api/* (API traffic)
               │                                 │
     ┌─────────▼─────────┐             ┌─────────▼─────────┐
     │  Next.js Frontend │             │  FastAPI Backend  │
     │    (Node.js 20)   │             │   (Python 3.12)   │
     │     port 3100     │             │     port 8100     │
     └───────────────────┘             └─────────┬─────────┘
                                                 │
                                       ┌─────────▼─────────┐
                                       │ PostgreSQL 17 +   │
                                       │    PostGIS 3.5    │
                                       │     port 5432     │
                                       │ (internal network)│
                                       └───────────────────┘
```

**Key Isolation Guarantees:**
- Database port 5432 is strictly private to the internal Docker network `pelagic_net` and is **never** exposed to the public internet.
- Public ingress is mediated exclusively by Nginx on port 80/443.
- Next.js and FastAPI share origin routing via `/` and `/api/`, eliminating CORS friction and preserving SameSite session cookies.

---

## 2. Server Prerequisites & Sizing

### Recommended System Specifications
- **Operating System:** Ubuntu 22.04 LTS / 24.04 LTS or Debian 12 (x86_64 or aarch64)
- **CPU:** 4 vCPUs minimum (8 vCPUs recommended for concurrent judge evaluation)
- **Memory (RAM):** 8 GB minimum (16 GB recommended for in-memory geospatial operations and Docker builds)
- **Storage:** 50 GB NVMe / SSD minimum (includes Docker layers, PostGIS tables, and offline demo raster assets)
- **Networking:** Static public IPv4 address, inbound ports 80 (HTTP) and 443 (HTTPS) open on cloud firewall / security group.

### Docker Engine & Compose Prerequisites
The host must have Docker Engine and Docker Compose v2 installed:

```bash
# Update and install dependencies
sudo apt-get update && sudo apt-get install -y ca-certificates curl gnupg

# Add Docker official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Compose plugin
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

---

## 3. Environment Variable Configuration

Create the production `.env` file from `.env.example`:

```bash
cp .env.example .env
chmod 600 .env
```

### Configuration Parameters

| Variable | Description | Example / Default |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL superuser username | `pelagic` |
| `POSTGRES_PASSWORD` | Strong random password for database | *(generate with `openssl rand -hex 24`)* |
| `POSTGRES_DB` | Dedicated database name (must start with `maritime_oil_v2`) | `maritime_oil_v2` |
| `DATABASE_URL` | SQLAlchemy/Psycopg DSN for internal container connection | `postgresql://pelagic:<PASSWORD>@db:5432/maritime_oil_v2` |
| `SECRET_KEY` | Cryptographic secret for signing sessions | *(generate with `openssl rand -hex 32`)* |
| `ORIGIN` | Allowed public web origin | `https://palagic.org` or `http://<SERVER_IP>` |
| `APP_ORIGIN` | Comma-separated list of trusted request origins | `https://palagic.org,http://<SERVER_IP>` |
| `COOKIE_SECURE` | Set to `true` when serving over HTTPS; `false` for plain HTTP | `true` |
| `ENVIRONMENT` | Runtime mode identifier | `production` |
| `API_URL` | Internal URL for Next.js server-side API proxying | `http://api:8100` |
| `NODE_ENV` | Node.js production environment | `production` |
| `PORT` | Public port bound by Nginx reverse proxy | `80` |

> **Security Rule:** Never commit the `.env` file to version control. Passwords and secret keys must be generated uniquely per deployment host.

---

## 4. Initial Deployment Procedure

Follow this exact sequence on a clean host:

### Step 1: Clone Repository
```bash
git clone https://github.com/your-org/Maritime-main.git /opt/palagic
cd /opt/palagic
```

### Step 2: Configure Environment
```bash
cp .env.example .env
# Edit .env with your generated credentials and domain
nano .env
```

### Step 3: Build Container Images from Scratch
```bash
docker compose build --no-cache
```

### Step 4: Deterministic Database Initialization
Run the initialization container (`init-db`), which bootstraps the PostGIS schema and seeds canonical demo datasets (`dwh-2010-05-17` AIS investigation and `SIH-ENNORE-2017` SAR investigation):

```bash
docker compose run --rm init-db
```

*Expected output:*
```
Ready: maritime_oil_v2. Local credentials: .runtime/demo-accounts.json.
Seeding SIH-ENNORE-2017 — LIVE
  Package version: 1.0
  Demo ready: True
  Case SIH-ENNORE-2017 created.
Seed complete. Case ID: SIH-ENNORE-2017
```

### Step 5: Launch the Production Stack
```bash
docker compose up -d
```

### Step 6: Verify Container Health
```bash
docker compose ps
```

All 4 active services (`db`, `api`, `web`, `proxy`) should report status `Up (healthy)`.

---

## 5. Health Verification & Smoke Testing

### Automated Health Endpoints

1. **Reverse Proxy & Frontend Health Check:**
   ```bash
   curl -I http://localhost/healthz
   ```
   *Expected Response:* `HTTP/1.1 200 OK`

2. **Backend API & Database Connectivity Check:**
   ```bash
   curl -s http://localhost/api/health | jq .
   ```
   *Expected Response:*
   ```json
   {
     "status": "ok",
     "version": "0.1.0",
     "demo_dataset": "SIH-ENNORE-2017",
     "database": "connected",
     "mode": "cached",
     "external_network_required": false
   }
   ```

3. **Public Cases Archive Check:**
   ```bash
   curl -s http://localhost/api/public/cases | jq '.[].id'
   ```
   *Expected Response:*
   ```
   "SIH-ENNORE-2017"
   "HIST-1705"
   "HIST-1905"
   "HIST-2005"
   ```

---

## 6. Domain Name & HTTPS / TLS Setup (Let's Encrypt)

When attaching a public domain (e.g. `palagic.sih.gov.in`):

### Option A: Certbot on Host with Nginx Pass-through
1. Point your DNS A record to your server's public IP.
2. Install Certbot:
   ```bash
   sudo apt-get install -y certbot
   ```
3. Temporarily stop port 80 proxy:
   ```bash
   docker compose stop proxy
   ```
4. Issue certificate:
   ```bash
   sudo certbot certonly --standalone -d palagic.yourdomain.com
   ```
5. Mount certificates into `deploy/nginx/ssl/`:
   ```bash
   mkdir -p deploy/nginx/ssl
   sudo cp /etc/letsencrypt/live/palagic.yourdomain.com/fullchain.pem deploy/nginx/ssl/cert.pem
   sudo cp /etc/letsencrypt/live/palagic.yourdomain.com/privkey.pem deploy/nginx/ssl/key.pem
   sudo chmod 600 deploy/nginx/ssl/key.pem
   ```
6. Update `deploy/nginx/nginx.conf` with HTTPS listener block (port 443 with `ssl_certificate /etc/nginx/ssl/cert.pem; ssl_certificate_key /etc/nginx/ssl/key.pem;`).
7. Update `.env`:
   ```env
   ORIGIN=https://palagic.yourdomain.com
   APP_ORIGIN=https://palagic.yourdomain.com
   COOKIE_SECURE=true
   ```
8. Restart proxy:
   ```bash
   docker compose up -d proxy api
   ```

### Option B: Cloudflare / Reverse Proxy Load Balancer
If running behind Cloudflare or an AWS ALB / GCP HTTPS Load Balancer with SSL termination:
- Set SSL mode to "Full" or "Flexible".
- Forward HTTP traffic directly to host port 80.
- Set `COOKIE_SECURE=true` and `APP_ORIGIN=https://palagic.yourdomain.com`.

---

## 7. Operational Procedures

### Restarting the Application Stack
```bash
docker compose restart
```
*Note:* The database storage volume `pelagic_v2_data` is persistent and will retain all cases, tracks, and observations intact across restarts.

### Viewing Service Logs
```bash
# View combined logs in real-time
docker compose logs -f

# View specific service logs
docker compose logs -f api
docker compose logs -f web
docker compose logs -f db
docker compose logs -f proxy
```

### Performing Database Backup
```bash
# Create timestamped SQL dump
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose exec -T db pg_dump -U pelagic -d maritime_oil_v2 -F c > "backup_palagic_${TIMESTAMP}.dump"
```

### Restoring Database from Backup
```bash
# Restore to database
docker compose stop api web
cat backup_palagic_YYYYMMDD_HHMMSS.dump | docker compose exec -T db pg_restore -U pelagic -d maritime_oil_v2 --clean --if-exists
docker compose start api web
```

### Updating Code & Zero-Downtime Rollout
```bash
# Pull new changes
git pull origin main

# Rebuild containers
docker compose build web api

# Recreate containers with minimal interruption
docker compose up -d --no-deps web api
```

### Rollback Procedure
If a deployment fails or exhibits unexpected regression:
```bash
# 1. Checkout known good release tag or commit
git checkout <PREVIOUS_COMMIT_OR_TAG>

# 2. Rebuild and restart
docker compose build web api
docker compose up -d

# 3. Verify health
curl -f http://localhost/healthz
curl -f http://localhost/api/health
```

---

## 8. Troubleshooting Guide

| Issue | Potential Cause | Resolution |
|---|---|---|
| `502 Bad Gateway` on `/` | Next.js container still compiling or starting | Check `docker compose logs web`. Ensure memory is >= 8 GB. |
| `502 Bad Gateway` on `/api/*` | FastAPI container failed to start | Check `docker compose logs api`. Verify `DATABASE_URL` matches credentials in `db`. |
| `403 Untrusted request origin` | Host origin does not match `APP_ORIGIN` | Add browser URL hostname/IP to `APP_ORIGIN` in `.env` and restart `api`. |
| Database connection refused | `db` container unhealthy or initializing | Check `docker compose logs db`. Ensure port 5432 is not blocked locally. |
| PostGIS extension not found | Non-postgis image used | Ensure `compose.yaml` uses `postgis/postgis:17-3.5`. |
| Port 80 already in use | Host Apache/Nginx running outside Docker | Run `sudo systemctl stop nginx` or set `PORT=8080` in `.env`. |
