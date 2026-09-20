from pathlib import Path

import docker_entrypoint
import engine


ROOT = Path(__file__).resolve().parents[1]


def test_docker_image_does_not_copy_private_or_parent_artifacts():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY ../" not in dockerfile
    assert "COPY abgen_bundle.pkl" not in dockerfile
    assert "COPY sample_data.pkl" not in dockerfile
    assert 'VOLUME ["/artifacts"]' in dockerfile
    assert 'CMD ["python", "docker_entrypoint.py"]' in dockerfile


def test_compose_mounts_runtime_artifacts_read_only():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "./artifacts:/artifacts:ro" in compose
    assert "ABGEN_BUNDLE_PATH=/artifacts/abgen_bundle.pkl" in compose
    assert "ABGEN_SAMPLE_DATA_PATH=/artifacts/sample_data.pkl" in compose
    assert "ABGEN_TRAINING_MODULE_PATH=/artifacts/training_module.py" in compose


def test_runtime_preflight_reports_missing_files(tmp_path):
    env = {
        "ABGEN_BUNDLE_PATH": str(tmp_path / "abgen_bundle.pkl"),
        "ABGEN_SAMPLE_DATA_PATH": str(tmp_path / "sample_data.pkl"),
        "ABGEN_TRAINING_MODULE_PATH": str(tmp_path / "training_module.py"),
    }

    missing = docker_entrypoint.missing_runtime_paths(env)
    assert set(missing) == set(env)

    for path in env.values():
        Path(path).write_bytes(b"trusted-test-placeholder")

    assert docker_entrypoint.missing_runtime_paths(env) == {}


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
