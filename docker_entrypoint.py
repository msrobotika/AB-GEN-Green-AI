"""Docker entrypoint for the AB-GEN research demo.

The image contains no private model artifacts. Startup fails closed before the
application can deserialize the model bundle unless the configured runtime
artifacts exist and match the trusted manifest.
"""

import os
import sys

from runtime_integrity import runtime_preflight_errors


def main():
    errors = runtime_preflight_errors()
    if errors:
        print("[AB-GEN] Runtime preflight failed.", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        print(
            "[AB-GEN] Refusing to start before model deserialization. "
            "Use only trusted artifacts and a manifest bound to the accepted "
            "release/evidence package. See SECURITY.md and REPRODUCIBILITY.md.",
            file=sys.stderr,
        )
        return 3

    os.execv(sys.executable, [sys.executable, "serve.py"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
