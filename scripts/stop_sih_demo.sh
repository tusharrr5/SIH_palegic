#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== STOPPING PALEGIC SIH DEMO SERVICES ==="

# Stop Cloudflare tunnel
if [ -f "$ROOT_DIR/.pids/tunnel.pid" ]; then
    PID=$(cat "$ROOT_DIR/.pids/tunnel.pid" || true)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "Stopping Cloudflare tunnel (PID: $PID)..."
        kill "$PID" || true
    fi
    rm -f "$ROOT_DIR/.pids/tunnel.pid"
fi
pkill -f "cloudflared tunnel.*3100" 2>/dev/null || true

# Stop Next.js production server
if [ -f "$ROOT_DIR/.pids/web.pid" ]; then
    PID=$(cat "$ROOT_DIR/.pids/web.pid" || true)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "Stopping Next.js server (PID: $PID)..."
        kill "$PID" || true
    fi
    rm -f "$ROOT_DIR/.pids/web.pid"
fi
pkill -f "next.*start.*3100" 2>/dev/null || true

# Stop FastAPI backend
if [ -f "$ROOT_DIR/.pids/fastapi.pid" ]; then
    PID=$(cat "$ROOT_DIR/.pids/fastapi.pid" || true)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "Stopping FastAPI backend (PID: $PID)..."
        kill "$PID" || true
    fi
    rm -f "$ROOT_DIR/.pids/fastapi.pid"
fi
pkill -f "uvicorn pelagic.main:app.*8100" 2>/dev/null || true

echo "All PALEGIC demo services stopped cleanly."
