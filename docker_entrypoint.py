"""Docker entrypoint for the AB-GEN research demo.

The image deliberately contains no private model artifacts. A validated runtime
must mount trusted artifacts read-only and point the process at them through
explicit environment variables.
"""

import os
import sys
from pathlib import Path


def required_runtime_paths(env=None):
    env = os.environ if env is None else env
    required = {
        "ABGEN_BUNDLE_PATH": env.get("ABGEN_BUNDLE_PATH", "/artifacts/abgen_bundle.pkl"),
        "ABGEN_SAMPLE_DATA_PATH": env.get("ABGEN_SAMPLE_DATA_PATH", "/artifacts/sample_data.pkl"),
        "ABGEN_TRAINING_MODULE_PATH": env.get(
            "ABGEN_TRAINING_MODULE_PATH", "/artifacts/training_module.py"
        ),
    }
    return {key: Path(value) for key, value in required.items()}


def missing_runtime_paths(env=None):
    return {
        key: path
        for key, path in required_runtime_paths(env).items()
        if not path.is_file()
    }


def main():
    missing = missing_runtime_paths()
    if missing:
        print("[AB-GEN] Runtime preflight failed.", file=sys.stderr)
        print(
            "[AB-GEN] This image intentionally ships without model/data artifacts.",
            file=sys.stderr,
        )
        print(
            "[AB-GEN] Mount a validated, trusted artifact directory read-only and provide:",
            file=sys.stderr,
        )
        for key, path in missing.items():
            print(f"  - {key} -> {path}", file=sys.stderr)
        print(
            "[AB-GEN] Never load unverified pickle/joblib artifacts. See SECURITY.md and REPRODUCIBILITY.md.",
            file=sys.stderr,
        )
        return 2

    os.execv(sys.executable, [sys.executable, "serve.py"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
