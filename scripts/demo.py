"""Run the cached recording build. Ctrl-C stops both child processes."""

from pathlib import Path
import subprocess, sys, time, urllib.request

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / "apps/web/.next/BUILD_ID").exists():
    raise SystemExit("Run npm --prefix apps/web run build once before recording.")
children = []
try:
    children.append(
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "pelagic.main:app",
                "--app-dir",
                str(ROOT / "api"),
                "--host",
                "127.0.0.1",
                "--port",
                "8100",
            ],
            cwd=ROOT,
        )
    )
    for _ in range(60):
        if children[0].poll() is not None:
            raise RuntimeError("API failed to start. Check port 8100 and DATABASE_URL.")
        try:
            with urllib.request.urlopen(
                "http://127.0.0.1:8100/api/health", timeout=1
            ) as response:
                if response.status == 200:
                    break
        except Exception:
            time.sleep(0.25)
    else:
        raise RuntimeError("Database/API did not become ready.")
    children.append(
        subprocess.Popen(
            [
                "node",
                "node_modules/next/dist/bin/next",
                "start",
                "--hostname",
                "127.0.0.1",
                "-p",
                "3100",
            ],
            cwd=ROOT / "apps/web",
        )
    )
    print(
        "\nPALEGIC: http://127.0.0.1:3100\nLocal services are required; internet access is not.\n"
    )
    while all(p.poll() is None for p in children):
        time.sleep(0.5)
    raise RuntimeError("A service exited; see the log above.")
except KeyboardInterrupt:
    print("\nStopping PALEGIC.")
finally:
    for child in children:
        if child.poll() is None:
            child.terminate()
    for child in children:
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
