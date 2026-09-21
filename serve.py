"""AB-GEN Research Demo - production WSGI entry point.

Production startup verifies configured runtime artifacts and their trusted
manifest before `app.load_resources()` can deserialize the recovered bundle.
"""

import os
import subprocess
import sys

from runtime_integrity import runtime_preflight_errors

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app, load_resources  # noqa: E402

HOST = os.environ.get("ABGEN_HOST", "0.0.0.0")
PORT = int(os.environ.get("ABGEN_PORT", "5000"))
THREADS = int(os.environ.get("ABGEN_THREADS", "4"))


def main():
    errors = runtime_preflight_errors()
    if errors:
        print("[AB-GEN] Production startup refused: runtime preflight failed.", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 3

    load_resources()

    try:
        from waitress import serve

        print(f"[AB-GEN] Production server: Waitress ({THREADS} threads)")
        print(f"[AB-GEN] Listening on http://{HOST}:{PORT}")
        serve(app, host=HOST, port=PORT, threads=THREADS)
        return 0
    except ImportError:
        pass

    try:
        __import__("gunicorn")
        print(f"[AB-GEN] Production server: Gunicorn ({THREADS} workers)")
        print(f"[AB-GEN] Listening on http://{HOST}:{PORT}")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "gunicorn",
                "-b",
                f"{HOST}:{PORT}",
                "-w",
                str(THREADS),
                "--timeout",
                "120",
                "app:app",
            ],
            check=True,
        )
        return 0
    except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"[AB-GEN] Production server unavailable: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
