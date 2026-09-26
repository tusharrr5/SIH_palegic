"""Server-side sessions with Argon2 hashes, HttpOnly cookies and explicit role checks."""

import hashlib, os, secrets, time
from collections import defaultdict, deque
from threading import Lock
from fastapi import Request, HTTPException, Depends
from argon2 import PasswordHasher
from .db import connection

HASHER = PasswordHasher()
DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(24))
COOKIE = "pelagic_session"
ATTEMPTS = defaultdict(deque)
RATE_LOCK = Lock()


SECRET_KEY = os.getenv("SECRET_KEY", "pelagic-dev-secret-key-sih-2026")


def require_origin(request: Request):
    allowed_raw = os.getenv("ORIGIN") or os.getenv("APP_ORIGIN") or "http://127.0.0.1:3100,http://localhost:3100"
    allowed = {o.strip() for o in allowed_raw.split(",") if o.strip()}
    # Always allow localhost variants in development/testing/reverse-proxy
    allowed.update({"http://127.0.0.1:3000", "http://localhost:3000", "http://127.0.0.1:3100", "http://localhost:3100", "http://localhost", "http://127.0.0.1"})
    origin = request.headers.get("origin")
    if origin:
        if (
            origin in allowed
            or origin.endswith(".vercel.app")
            or origin.endswith(".trycloudflare.com")
            or origin.endswith(".loca.lt")
            or origin.endswith(".lhr.life")
        ):
            return
        raise HTTPException(403, f"Untrusted request origin: {origin}")
    referer = request.headers.get("referer")
    if referer and (
        any(referer.startswith(a) for a in allowed)
        or ".vercel.app" in referer
        or ".trycloudflare.com" in referer
        or ".loca.lt" in referer
        or ".lhr.life" in referer
    ):
        return
    # If forwarded by Vercel serverless proxy or Render internal router
    fwd_host = request.headers.get("x-forwarded-host", "")
    if fwd_host and (fwd_host in allowed or fwd_host.endswith(".vercel.app")):
        return
    # If Origin and Referer are not present (e.g. server-side calls or curl with custom headers), permit if host is local
    client_host = request.client.host if request.client else ""
    if client_host in ("127.0.0.1", "localhost", "::1"):
        return
    raise HTTPException(403, "Untrusted request origin")


def throttle(key):
    with RATE_LOCK:
        now = time.monotonic()
        q = ATTEMPTS[key]
        while q and now - q[0] > 300:
            q.popleft()
        if len(q) >= 10:
            raise HTTPException(
                429, "Too many sign-in attempts. Try again in five minutes."
            )
        q.append(now)


def user_from_request(request: Request):
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    with connection() as conn:
        return conn.execute(
            """SELECT u.id,u.email,u.name,u.role FROM sessions s JOIN users u ON u.id=s.user_id
            WHERE s.token_hash=%s AND s.expires_at>now() AND u.active""",
            (hashlib.sha256(token.encode()).hexdigest(),),
        ).fetchone()


def require_roles(*roles):
    def check(user=Depends(user_from_request)):
        if not user:
            raise HTTPException(401, "Sign in to continue")
        if user["role"] not in roles:
            raise HTTPException(403, "Your role does not permit this action")
        return user

    return check


AUTHORITY = require_roles("authority", "admin")
ADMIN = require_roles("admin")
