"""
AB-GEN Research Demo - production WSGI entry point.

Uses Waitress when available and falls back to Gunicorn or the Flask development
server. Runtime model/data artifacts are loaded by `app.load_resources()`.
"""

import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app, load_resources

HOST = os.environ.get("ABGEN_HOST", "0.0.0.0")
PORT = int(os.environ.get("ABGEN_PORT", "5000"))
THREADS = int(os.environ.get("ABGEN_THREADS", "4"))


def main():
    load_resources()

    try:
        from waitress import serve
        print(f"[AB-GEN] Production server: Waitress ({THREADS} threads)")
        print(f"[AB-GEN] Listening on http://{HOST}:{PORT}")
        serve(app, host=HOST, port=PORT, threads=THREADS)
        return
    except ImportError:
        pass

    try:
        import subprocess
        print(f"[AB-GEN] Production server: Gunicorn ({THREADS} workers)")
        print(f"[AB-GEN] Listening on http://{HOST}:{PORT}")
        subprocess.run([
            sys.executable, "-m", "gunicorn",
            "-b", f"{HOST}:{PORT}",
            "-w", str(THREADS),
            "--timeout", "120",
            "app:app",
        ], check=True)
        return
    except (ImportError, FileNotFoundError):
        pass

    print("[AB-GEN] WARNING: No production server found. Using Flask dev server.")
    print("[AB-GEN] Install: pip install waitress (Windows) or gunicorn (Linux)")
    app.run(host=HOST, port=PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
