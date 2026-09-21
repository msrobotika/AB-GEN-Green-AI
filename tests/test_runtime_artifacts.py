from pathlib import Path

import engine
import runtime_integrity
from tools.artifact_manifest import create_manifest, write_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_docker_image_does_not_copy_private_or_parent_artifacts():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY ../" not in dockerfile
    assert "COPY abgen_bundle.pkl" not in dockerfile
    assert "COPY sample_data.pkl" not in dockerfile
    assert "COPY tools/ tools/" in dockerfile
    assert "runtime_integrity.py" in dockerfile
    assert 'VOLUME ["/artifacts"]' in dockerfile
    assert "ABGEN_REQUIRE_MANIFEST=1" in dockerfile
    assert 'CMD ["python", "docker_entrypoint.py"]' in dockerfile


def test_compose_mounts_runtime_artifacts_read_only_and_requires_manifest():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "./artifacts:/artifacts:ro" in compose
    assert "ABGEN_BUNDLE_PATH=/artifacts/abgen_bundle.pkl" in compose
    assert "ABGEN_SAMPLE_DATA_PATH=/artifacts/sample_data.pkl" in compose
    assert "ABGEN_TRAINING_MODULE_PATH=/artifacts/training_module.py" in compose
    assert "ABGEN_ARTIFACT_MANIFEST_PATH=/artifacts/runtime-manifest.json" in compose
    assert "ABGEN_REQUIRE_MANIFEST=1" in compose


def test_runtime_preflight_reports_missing_files(tmp_path):
    env = {
        "ABGEN_BUNDLE_PATH": str(tmp_path / "abgen_bundle.pkl"),
        "ABGEN_SAMPLE_DATA_PATH": str(tmp_path / "sample_data.pkl"),
        "ABGEN_TRAINING_MODULE_PATH": str(tmp_path / "training_module.py"),
        "ABGEN_ARTIFACT_MANIFEST_PATH": str(tmp_path / "runtime-manifest.json"),
        "ABGEN_REQUIRE_MANIFEST": "1",
    }

    missing = runtime_integrity.missing_runtime_paths(env)
    assert set(missing) == {"model_bundle", "sample_data", "training_module"}
    errors = runtime_integrity.runtime_preflight_errors(env)
    assert len(errors) == 3
    assert all("required runtime artifact missing" in error for error in errors)


def test_runtime_manifest_verification_passes_then_detects_tamper(tmp_path):
    bundle = tmp_path / "abgen_bundle.pkl"
    samples = tmp_path / "sample_data.pkl"
    module = tmp_path / "training_module.py"
    manifest_path = tmp_path / "runtime-manifest.json"

    bundle.write_bytes(b"bundle-v1")
    samples.write_bytes(b"samples-v1")
    module.write_text("VALUE = 1\n", encoding="utf-8")

    artifacts = {
        "model_bundle": bundle,
        "sample_data": samples,
        "training_module": module,
    }
    write_manifest(create_manifest(artifacts), manifest_path)

    env = {
        "ABGEN_BUNDLE_PATH": str(bundle),
        "ABGEN_SAMPLE_DATA_PATH": str(samples),
        "ABGEN_TRAINING_MODULE_PATH": str(module),
        "ABGEN_ARTIFACT_MANIFEST_PATH": str(manifest_path),
        "ABGEN_REQUIRE_MANIFEST": "1",
    }

    assert runtime_integrity.runtime_preflight_errors(env) == []

    bundle.write_bytes(b"bundle-tampered")
    errors = runtime_integrity.runtime_preflight_errors(env)
    assert errors
    assert any("SHA-256 mismatch" in error or "size mismatch" in error for error in errors)


def test_manifest_requirement_can_only_be_disabled_explicitly(tmp_path):
    env = {
        "ABGEN_BUNDLE_PATH": str(tmp_path / "abgen_bundle.pkl"),
        "ABGEN_SAMPLE_DATA_PATH": str(tmp_path / "sample_data.pkl"),
        "ABGEN_TRAINING_MODULE_PATH": str(tmp_path / "training_module.py"),
        "ABGEN_REQUIRE_MANIFEST": "0",
    }
    for key in ("ABGEN_BUNDLE_PATH", "ABGEN_SAMPLE_DATA_PATH", "ABGEN_TRAINING_MODULE_PATH"):
        Path(env[key]).write_bytes(b"placeholder")

    assert runtime_integrity.manifest_required(env) is False
    assert runtime_integrity.runtime_preflight_errors(env) == []


def test_explicit_serialization_module_path_is_supported(tmp_path, monkeypatch):
    compatibility_module = tmp_path / "training_module.py"
    compatibility_module.write_text("SERIALIZATION_COMPATIBILITY_TEST = 42\n", encoding="utf-8")
    monkeypatch.setenv("ABGEN_TRAINING_MODULE_PATH", str(compatibility_module))

    loaded = engine._register_training_classes()

    assert loaded is not None
    assert loaded.SERIALIZATION_COMPATIBILITY_TEST == 42


def test_gitignore_blocks_runtime_artifacts():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "abgen_bundle.pkl" in ignore
    assert "sample_data.pkl" in ignore
    assert "artifacts/*" in ignore
    assert "!artifacts/README.md" in ignore
