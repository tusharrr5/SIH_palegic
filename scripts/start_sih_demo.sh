#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p "$ROOT_DIR/logs" "$ROOT_DIR/.pids"

echo "=== PALEGIC SIH 2026 DEMO LAUNCHER ==="

# 1. Check PostgreSQL Database
echo "[1/4] Checking PostgreSQL status..."
if command -v pg_isready >/dev/null 2>&1; then
    if ! pg_isready -q; then
        echo "PostgreSQL not running. Attempting to start via brew services..."
        brew services start postgresql@17 || brew services start postgresql || true
        sleep 2
    fi
fi

# 2. Start FastAPI Backend (:8100)
echo "[2/4] Starting FastAPI backend on 127.0.0.1:8100..."
if curl -s "http://127.0.0.1:8100/api/health" | grep -q '"status":"ok"'; then
    echo "FastAPI already running on port 8100."
else
    if [ ! -d ".venv" ]; then
        echo "Error: Python .venv not found in $ROOT_DIR" >&2
        exit 1
    fi
    nohup "$ROOT_DIR/.venv/bin/python" -m uvicorn pelagic.main:app \
        --app-dir api \
        --host 127.0.0.1 \
        --port 8100 > "$ROOT_DIR/logs/fastapi.log" 2>&1 &
    FASTAPI_PID=$!
    echo "$FASTAPI_PID" > "$ROOT_DIR/.pids/fastapi.pid"
    
    # Wait for FastAPI health
    echo "Waiting for FastAPI backend to respond..."
    for i in {1..30}; do
        if curl -s "http://127.0.0.1:8100/api/health" | grep -q '"status":"ok"'; then
            echo "FastAPI is healthy."
            break
        fi
        sleep 1
    done
fi

# 3. Start Next.js Production Server (:3100)
echo "[3/4] Starting Next.js production server on 127.0.0.1:3100..."
if curl -s "http://127.0.0.1:3100/healthz" | grep -q '"ok":true'; then
    echo "Next.js production server already running on port 3100."
else
    if [ ! -d "apps/web/.next" ]; then
        echo "Building Next.js production bundle..."
        npm --prefix apps/web run build
    fi
    nohup npm --prefix apps/web run start > "$ROOT_DIR/logs/web.log" 2>&1 &
    WEB_PID=$!
    echo "$WEB_PID" > "$ROOT_DIR/.pids/web.pid"
    
    # Wait for Next.js health
    echo "Waiting for Next.js server to respond..."
    for i in {1..30}; do
        if curl -s "http://127.0.0.1:3100/healthz" | grep -q '"ok":true'; then
            echo "Next.js is healthy."
            break
        fi
        sleep 1
    done
fi

# 4. Start Cloudflare Tunnel
echo "[4/4] Starting Cloudflare Tunnel..."
if pgrep -f "cloudflared tunnel.*3100" >/dev/null 2>&1; then
    echo "Cloudflare tunnel process is already running."
else
    if ! command -v cloudflared >/dev/null 2>&1; then
        echo "Error: cloudflared not found. Install via: brew install cloudflared" >&2
        exit 1
    fi
    > "$ROOT_DIR/logs/cloudflared.log"
    nohup cloudflared tunnel --protocol http2 --url http://127.0.0.1:3100 > "$ROOT_DIR/logs/cloudflared.log" 2>&1 &
    TUNNEL_PID=$!
    echo "$TUNNEL_PID" > "$ROOT_DIR/.pids/tunnel.pid"
fi

# Wait for tunnel URL
echo "Waiting for Cloudflare public URL..."
PUBLIC_URL=""
for i in {1..45}; do
    if [ -f "$ROOT_DIR/logs/cloudflared.log" ]; then
        FOUND_URL=$(grep -o 'https://[-a-zA-Z0-9.]*\.trycloudflare\.com' "$ROOT_DIR/logs/cloudflared.log" | head -n 1 || true)
        if [ -n "$FOUND_URL" ]; then
            PUBLIC_URL="$FOUND_URL"
            break
        fi
    fi
    sleep 1
done

if [ -z "$PUBLIC_URL" ]; then
    echo "Warning: Could not capture trycloudflare URL automatically."
    echo "Check logs/cloudflared.log for details."
else
    echo "Public Cloudflare Tunnel established: $PUBLIC_URL"
    echo "$PUBLIC_URL/?demo=true" > "$ROOT_DIR/CURRENT_DEMO_URL.txt"
fi

echo ""
echo "=================================================="
echo "PALEGIC DEMO SERVICES RUNNING"
echo "=================================================="
echo "LOCAL:  http://127.0.0.1:3100/?demo=true"
if [ -n "$PUBLIC_URL" ]; then
    echo "PUBLIC: $PUBLIC_URL/?demo=true"
fi
echo "=================================================="
