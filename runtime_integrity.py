"""Runtime artifact integrity checks for AB-GEN launch paths.

This module performs byte-integrity checks before any runtime code is allowed to
deserialize the recovered joblib/pickle bundle. Integrity is not provenance:
the accepted manifest must itself come from a trusted immutable evidence or
release package.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from tools.artifact_manifest import load_manifest, verify_manifest


TRUTHY = {"1", "true", "yes", "on"}
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_ARTIFACT_DIR = BASE_DIR / "artifacts"

_RUNTIME_SPECS = {
    "model_bundle": ("ABGEN_BUNDLE_PATH", DEFAULT_ARTIFACT_DIR / "abgen_bundle.pkl"),
    "sample_data": ("ABGEN_SAMPLE_DATA_PATH", DEFAULT_ARTIFACT_DIR / "sample_data.pkl"),
    "training_module": ("ABGEN_TRAINING_MODULE_PATH", DEFAULT_ARTIFACT_DIR / "training_module.py"),
}


def _environment(env: Mapping[str, str] | None = None) -> Mapping[str, str]:
    return os.environ if env is None else env


def required_runtime_paths(env: Mapping[str, str] | None = None) -> dict[str, Path]:
    """Return manifest-label -> artifact-path mapping for the current runtime."""
    env = _environment(env)
    return {
        label: Path(env.get(variable, str(default_path)))
        for label, (variable, default_path) in _RUNTIME_SPECS.items()
    }


def missing_runtime_paths(env: Mapping[str, str] | None = None) -> dict[str, Path]:
    return {
        label: path
        for label, path in required_runtime_paths(env).items()
        if not path.is_file()
    }


def manifest_required(env: Mapping[str, str] | None = None) -> bool:
    env = _environment(env)
    return str(env.get("ABGEN_REQUIRE_MANIFEST", "1")).strip().lower() in TRUTHY


def runtime_manifest_path(env: Mapping[str, str] | None = None) -> Path:
    env = _environment(env)
    default_path = DEFAULT_ARTIFACT_DIR / "runtime-manifest.json"
    return Path(env.get("ABGEN_ARTIFACT_MANIFEST_PATH", str(default_path)))


def verify_runtime_manifest(env: Mapping[str, str] | None = None) -> list[str]:
    """Return integrity errors; an empty list means the configured bytes match.

    `ABGEN_REQUIRE_MANIFEST=0` is an explicit forensic/debug override and must
    never be used to describe a runtime as validated.
    """
    env = _environment(env)
    if not manifest_required(env):
        return []

    manifest_path = runtime_manifest_path(env)
    if not manifest_path.is_file():
        return [f"artifact manifest missing: {manifest_path}"]

    try:
        manifest = load_manifest(manifest_path)
        return verify_manifest(manifest, required_runtime_paths(env))
    except (OSError, ValueError) as exc:
        return [f"artifact manifest verification failed: {exc}"]


def runtime_preflight_errors(env: Mapping[str, str] | None = None) -> list[str]:
    """Return all fail-closed runtime-preflight errors before deserialization."""
    env = _environment(env)
    missing = missing_runtime_paths(env)
    if missing:
        return [
            f"required runtime artifact missing: {label} -> {path}"
            for label, path in missing.items()
        ]
    return verify_runtime_manifest(env)
