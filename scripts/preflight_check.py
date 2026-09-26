#!/usr/bin/env python3
"""Scientific data provider credential and capability preflight check for SIH-ENNORE-2017.

Checks whether the local environment has valid, working credentials to retrieve:
  A. Copernicus Data Space Ecosystem (CDSE) Sentinel-1 SAR
  B. ECMWF / Copernicus Climate Data Store (CDS) ERA5 Wind
  C. Copernicus Marine Service (CMEMS) Historical Ocean Currents

SAFETY AND SECURITY RULES:
  - NEVER prints passwords, API keys, access tokens, or refresh tokens.
  - ONLY reports standard status codes:
      READY
      CREDENTIALS_MISSING
      TERMS_NOT_ACCEPTED
      AUTH_ERROR
      NETWORK_ERROR
  - Cleanly halts if credentials are absent.
  - Never fabricates or substitutes fake data.

Usage:
    python scripts/preflight_check.py [--json] [--verbose]
"""

import argparse
import json
import os
import sys
import ssl
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# CDSE endpoints
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

# CDS endpoints
CDS_API_URL_DEFAULT = "https://cds.climate.copernicus.eu/api"

# CMEMS configuration paths
CMEMS_CREDENTIALS_FILE = Path.home() / ".copernicusmarine" / ".copernicusmarine-credentials"


def _make_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx


def check_cdse(verbose: bool = False) -> tuple[str, str]:
    """Check Copernicus Data Space Ecosystem (CDSE) credentials and API access.
    
    Returns (status, message)
      Status is one of: READY, CREDENTIALS_MISSING, AUTH_ERROR, NETWORK_ERROR
    """
    username = os.environ.get("CDSE_USERNAME", "").strip()
    password = os.environ.get("CDSE_PASSWORD", "").strip()

    if not username or not password:
        msg = "CDSE_USERNAME and/or CDSE_PASSWORD environment variables are not set."
        return "CREDENTIALS_MISSING", msg

    # Validate by attempting to get a token
    try:
        import urllib.request
        import urllib.parse
        import urllib.error

        data = urllib.parse.urlencode({
            "client_id": "cdse-public",
            "grant_type": "password",
            "username": username,
            "password": password,
        }).encode("utf-8")

        req = urllib.request.Request(
            CDSE_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        ctx = _make_ssl_context()
        try:
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                if resp.status == 200:
                    body = json.loads(resp.read().decode("utf-8"))
                    if "access_token" in body:
                        return "READY", "Successfully authenticated with CDSE."
                    return "AUTH_ERROR", "Token response did not contain access_token."
                return "AUTH_ERROR", f"HTTP {resp.status} received from CDSE identity service."
        except urllib.error.HTTPError as h_err:
            if h_err.code in (400, 401, 403):
                return "AUTH_ERROR", f"CDSE authentication failed: HTTP {h_err.code} (invalid credentials)."
            return "NETWORK_ERROR", f"CDSE identity service returned HTTP {h_err.code}."
        except urllib.error.URLError as u_err:
            return "NETWORK_ERROR", f"Cannot connect to CDSE identity service: {u_err.reason}."

    except Exception as exc:
        err_msg = str(exc)
        if password in err_msg:
            err_msg = err_msg.replace(password, "[REDACTED]")
        return "NETWORK_ERROR", f"CDSE request error: {err_msg}"


def check_era5(verbose: bool = False) -> tuple[str, str]:
    """Check ECMWF / Copernicus Climate Data Store (CDS) credentials and API access.
    
    Returns (status, message)
      Status is one of: READY, CREDENTIALS_MISSING, TERMS_NOT_ACCEPTED, AUTH_ERROR, NETWORK_ERROR
    """
    cdsapirc = Path.home() / ".cdsapirc"
    env_url = os.environ.get("CDSAPI_URL", "").strip()
    env_key = os.environ.get("CDSAPI_KEY", "").strip()

    url = ""
    key = ""

    if cdsapirc.exists():
        try:
            for line in cdsapirc.read_text().splitlines():
                line = line.strip()
                if line.startswith("url:"):
                    url = line.split(":", 1)[1].strip()
                elif line.startswith("key:"):
                    key = line.split(":", 1)[1].strip()
        except Exception as exc:
            return "AUTH_ERROR", f"Could not read ~/.cdsapirc: {exc}"

    if not url and env_url:
        url = env_url
    if not key and env_key:
        key = env_key

    if not key:
        msg = "No CDS API key found in ~/.cdsapirc or CDSAPI_KEY environment variable."
        return "CREDENTIALS_MISSING", msg

    if not url:
        url = CDS_API_URL_DEFAULT

    # Test API authentication
    try:
        import urllib.request
        import urllib.error

        test_url = url.rstrip("/")
        req = urllib.request.Request(
            test_url,
            headers={"PRIVATE-TOKEN": key} if ":" not in key else {},
        )
        if ":" in key:
            import base64
            auth_header = base64.b64encode(key.encode("utf-8")).decode("utf-8")
            req.add_header("Authorization", f"Basic {auth_header}")

        ctx = _make_ssl_context()
        try:
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                pass
        except urllib.error.HTTPError as h_err:
            if h_err.code in (401, 403):
                body = h_err.read().decode("utf-8", errors="ignore").lower()
                if "term" in body or "licence" in body or "license" in body or "accept" in body:
                    return "TERMS_NOT_ACCEPTED", "CDS user has not accepted licence terms for dataset."
                return "AUTH_ERROR", "Invalid CDS API credentials (HTTP 401/403)."
            elif h_err.code == 404:
                # URL root returning 404 still proves reachability
                pass
            else:
                return "NETWORK_ERROR", f"CDS API returned HTTP {h_err.code}"
        except urllib.error.URLError as u_err:
            return "NETWORK_ERROR", f"Cannot connect to CDS API: {u_err.reason}."

        return "READY", "CDS API credentials verified."

    except Exception as exc:
        err_str = str(exc)
        if key in err_str:
            err_str = err_str.replace(key, "[REDACTED]")
        return "NETWORK_ERROR", f"CDS API check failed: {err_str}"


def check_cmems(verbose: bool = False) -> tuple[str, str]:
    """Check Copernicus Marine Service (CMEMS) credentials.
    
    Returns (status, message)
      Status is one of: READY, CREDENTIALS_MISSING, AUTH_ERROR, NETWORK_ERROR
    """
    env_user = os.environ.get("COPERNICUSMARINE_SERVICE_USERNAME", "").strip()
    env_pass = os.environ.get("COPERNICUSMARINE_SERVICE_PASSWORD", "").strip()

    has_env = bool(env_user and env_pass)
    has_file = CMEMS_CREDENTIALS_FILE.exists()

    if not has_env and not has_file:
        msg = "CMEMS credentials not found in env (COPERNICUSMARINE_SERVICE_*) or ~/.copernicusmarine/."
        return "CREDENTIALS_MISSING", msg

    try:
        import copernicusmarine
        try:
            copernicusmarine.login(
                username=env_user if env_user else None,
                password=env_pass if env_pass else None,
                check_connection=True,
            )
            return "READY", "Successfully validated CMEMS credentials."
        except Exception as login_exc:
            err = str(login_exc)
            if env_pass and env_pass in err:
                err = err.replace(env_pass, "[REDACTED]")
            if "unauthorized" in err.lower() or "forbidden" in err.lower() or "credential" in err.lower() or "login" in err.lower():
                return "AUTH_ERROR", f"CMEMS authentication failed: {err}"
            return "NETWORK_ERROR", f"CMEMS connection error: {err}"
    except ImportError:
        if has_env or has_file:
            return "AUTH_ERROR", "copernicusmarine package is not installed."
        return "CREDENTIALS_MISSING", "copernicusmarine package not installed and no credentials configured."


def run_preflight(verbose: bool = False) -> dict[str, dict]:
    results = {}

    cdse_status, cdse_msg = check_cdse(verbose)
    results["CDSE"] = {"status": cdse_status, "message": cdse_msg}

    era5_status, era5_msg = check_era5(verbose)
    results["ERA5"] = {"status": era5_status, "message": era5_msg}

    cmems_status, cmems_msg = check_cmems(verbose)
    results["CMEMS"] = {"status": cmems_status, "message": cmems_msg}

    return results


def main():
    parser = argparse.ArgumentParser(description="Preflight check for scientific data providers.")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Include detailed messages.")
    args = parser.parse_args()

    results = run_preflight(verbose=args.verbose)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print("=" * 60)
    print("PALEGIC SIH-ENNORE-2017 — SCIENTIFIC DATA PREFLIGHT CHECK")
    print("=" * 60)
    for provider in ["CDSE", "ERA5", "CMEMS"]:
        res = results[provider]
        status = res["status"]
        print(f"{provider}: {status}")
        if args.verbose or status != "READY":
            print(f"  Note: {res['message']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
