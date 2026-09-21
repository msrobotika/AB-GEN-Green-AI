"""AB-GEN Research Demo - production WSGI entry point.

Production startup verifies configured runtime artifacts and their trusted
manifest before `app.load_resources()` can deserialize the recovered bundle.
The supported production server for this repository is Waitress, which is
pinned by the production dependency contract rather than selected implicitly.
"""

import os
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

    try:
        from waitress import serve
    except ImportError:
        print(
            "[AB-GEN] Production startup refused: Waitress is not installed. "
            "Install requirements_prod.txt.",
            file=sys.stderr,
        )
        return 4

    load_resources()
    print(f"[AB-GEN] Production server: Waitress ({THREADS} threads)")
    print(f"[AB-GEN] Listening on http://{HOST}:{PORT}")
    serve(app, host=HOST, port=PORT, threads=THREADS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
