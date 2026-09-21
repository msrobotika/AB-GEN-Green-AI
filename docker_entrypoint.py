"""Docker entrypoint for the AB-GEN research demo.

The image contains no private model artifacts. A validated runtime mounts
trusted artifacts read-only and verifies their manifest before the Flask
process is allowed to deserialize the model bundle.

Manifest verification detects accidental/tampered byte changes. The manifest
itself must still come from a trusted, immutable release/evidence package.
"""

import os
import sys
from pathlib import Path

from tools.artifact_manifest import load_manifest, verify_manifest


TRUTHY = {"1", "true", "yes", "on"}


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


def manifest_required(env=None) -> bool:
    env = os.environ if env is None else env
    return str(env.get("ABGEN_REQUIRE_MANIFEST", "1")).strip().lower() in TRUTHY


def runtime_manifest_path(env=None) -> Path:
    env = os.environ if env is None else env
    return Path(
        env.get("ABGEN_ARTIFACT_MANIFEST_PATH", "/artifacts/runtime-manifest.json")
    )


def runtime_artifact_mapping(env=None):
    paths = required_runtime_paths(env)
    return {
        "model_bundle": paths["ABGEN_BUNDLE_PATH"],
        "sample_data": paths["ABGEN_SAMPLE_DATA_PATH"],
        "training_module": paths["ABGEN_TRAINING_MODULE_PATH"],
    }


def verify_runtime_manifest(env=None) -> list[str]:
    """Return manifest verification errors; empty list means accepted bytes.

    Setting ``ABGEN_REQUIRE_MANIFEST=0`` disables this preflight for explicit
    local forensic work only. Docker defaults to requiring the manifest.
    """
    env = os.environ if env is None else env
    if not manifest_required(env):
        return []

    path = runtime_manifest_path(env)
    if not path.is_file():
        return [f"artifact manifest missing: {path}"]

    try:
        manifest = load_manifest(path)
        return verify_manifest(manifest, runtime_artifact_mapping(env))
    except (OSError, ValueError) as exc:
        return [f"artifact manifest verification failed: {exc}"]


def main():
    missing = missing_runtime_paths()
    if missing:
        print("[AB-GEN] Runtime preflight failed: required artifacts missing.", file=sys.stderr)
        print(
            "[AB-GEN] This image intentionally ships without model/data artifacts.",
            file=sys.stderr,
        )
        for key, path in missing.items():
            print(f"  - {key} -> {path}", file=sys.stderr)
        print(
            "[AB-GEN] Never load unverified pickle/joblib artifacts. See SECURITY.md and REPRODUCIBILITY.md.",
            file=sys.stderr,
        )
        return 2

    manifest_errors = verify_runtime_manifest()
    if manifest_errors:
        print("[AB-GEN] Runtime preflight failed: artifact integrity check failed.", file=sys.stderr)
        for error in manifest_errors:
            print(f"  - {error}", file=sys.stderr)
        print(
            "[AB-GEN] Refusing to start before model deserialization. The manifest must be trusted and bound to the accepted release/evidence package.",
            file=sys.stderr,
        )
        return 3

    os.execv(sys.executable, [sys.executable, "serve.py"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
