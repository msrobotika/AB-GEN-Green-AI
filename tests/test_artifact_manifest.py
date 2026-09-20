import json
from pathlib import Path

from tools import artifact_manifest


def test_manifest_records_hashes_without_absolute_paths(tmp_path, monkeypatch):
    model = tmp_path / "abgen_bundle.pkl"
    data = tmp_path / "sample_data.pkl"
    model.write_bytes(b"model-bytes")
    data.write_bytes(b"sample-bytes")

    monkeypatch.setattr(artifact_manifest, "current_git_commit", lambda: "deadbeef")
    manifest = artifact_manifest.create_manifest({"model_bundle": model, "sample_data": data})
    serialized = json.dumps(manifest)

    assert manifest["schema_version"] == 1
    assert manifest["git_commit"] == "deadbeef"
    assert manifest["artifacts"]["model_bundle"]["filename"] == "abgen_bundle.pkl"
    assert manifest["artifacts"]["model_bundle"]["size_bytes"] == len(b"model-bytes")
    assert len(manifest["artifacts"]["model_bundle"]["sha256"]) == 64
    assert str(tmp_path) not in serialized


def test_manifest_verification_detects_tampering(tmp_path):
    model = tmp_path / "abgen_bundle.pkl"
    model.write_bytes(b"original")

    artifacts = {"model_bundle": model}
    manifest = artifact_manifest.create_manifest(artifacts)
    assert artifact_manifest.verify_manifest(manifest, artifacts) == []

    model.write_bytes(b"tampered")
    errors = artifact_manifest.verify_manifest(manifest, artifacts)

    assert any("size mismatch" in error or "SHA-256 mismatch" in error for error in errors)


def test_manifest_roundtrip_and_cli_verify(tmp_path, monkeypatch):
    model = tmp_path / "model.pkl"
    model.write_bytes(b"abc123")
    output = tmp_path / "manifest.json"

    monkeypatch.setattr(artifact_manifest, "current_git_commit", lambda: None)

    assert artifact_manifest.main([
        "create",
        "--artifact", f"model={model}",
        "--output", str(output),
    ]) == 0

    loaded = artifact_manifest.load_manifest(output)
    assert loaded["artifacts"]["model"]["filename"] == "model.pkl"

    assert artifact_manifest.main([
        "verify",
        "--manifest", str(output),
        "--artifact", f"model={model}",
    ]) == 0


def test_parse_artifact_specs_rejects_duplicate_labels(tmp_path):
    file_a = tmp_path / "a.bin"
    file_b = tmp_path / "b.bin"
    file_a.write_bytes(b"a")
    file_b.write_bytes(b"b")

    try:
        artifact_manifest.parse_artifact_specs([
            f"artifact={file_a}",
            f"artifact={file_b}",
        ])
    except ValueError as exc:
        assert "Duplicate artifact name" in str(exc)
    else:
        raise AssertionError("duplicate labels must be rejected")
