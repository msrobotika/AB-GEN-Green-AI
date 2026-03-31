"""
AB-GEN 80% - Production WSGI Server
Uses Waitress (Windows) or Gunicorn (Linux/Mac).
Run: python serve.py
"""

import sys
import os

# ── Ensure working directory is the demo folder ───────────────────────
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app, load_resources

HOST    = os.environ.get("ABGEN_HOST", "0.0.0.0")
PORT    = int(os.environ.get("ABGEN_PORT", "5000"))
THREADS = int(os.environ.get("ABGEN_THREADS", "4"))

def main():
    load_resources()

    # --- Try Waitress first (Windows) -----------------------------------
    try:
        from waitress import serve
        print(f"[AB-GEN] Production server: Waitress ({THREADS} threads)")
        print(f"[AB-GEN] Listening on http://{HOST}:{PORT}")
        serve(app, host=HOST, port=PORT, threads=THREADS)
        return
    except ImportError:
        pass

    # --- Fall back to Gunicorn (Linux/Mac) ------------------------------
    try:
        import subprocess
        print(f"[AB-GEN] Production server: Gunicorn ({THREADS} workers)")
        print(f"[AB-GEN] Listening on http://{HOST}:{PORT}")
        subprocess.run([
            sys.executable, "-m", "gunicorn",
            "-b", f"{HOST}:{PORT}",
            "-w", str(THREADS),
            "--timeout", "120",
            "app:app"
        ], check=True)
        return
    except (ImportError, FileNotFoundError):
        pass

    # --- Last resort: Flask dev server (NOT for production) -------------
    print("[AB-GEN] WARNING: No production server found. Using Flask dev server.")
    print("[AB-GEN] Install: pip install waitress  (Windows) or gunicorn (Linux)")
    app.run(host=HOST, port=PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
