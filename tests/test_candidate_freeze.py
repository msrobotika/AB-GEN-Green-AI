from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from clean_baseline import candidate_freeze
from clean_baseline.candidate_verify import verify_frozen_candidate
from clean_baseline.contracts import LeakageError, assert_manifest_ready_for_final_test
from clean_baseline.final_test_authorize import authorize_final_test
from clean_baseline.preflight import run_preflight
from clean_baseline.split_ledger import PROTOCOL_ID, sha256_file


ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _freeze_fixture(tmp_path: Path, monkeypatch):
    ledger = _write(tmp_path / "split_ledger.csv", "sample_id,label\n")
    ledger_manifest = _write(tmp_path / "split_ledger.manifest.json", "{}\n")
    oof_plan = _write(tmp_path / "oof_plan.json", "{}\n")
    config = _write(tmp_path / "frozen_config.json", '{"model":"frozen"}\n')
    env = _write(tmp_path / "environment.lock", "numpy==2.4.6\n")
    features = _write(tmp_path / "feature_order.txt", "f0\nf1\n")
    artifact = _write(tmp_path / "model.bin", "frozen-artifact\n")

    ledger_sha = sha256_file(ledger)
    monkeypatch.setattr(
        candidate_freeze,
        "verify_ledger_package",
        lambda *_args, **_kwargs: {"ledger_sha256": ledger_sha},
    )
    monkeypatch.setattr(candidate_freeze, "verify_oof_plan", lambda *_args, **_kwargs: {})

    out = tmp_path / "candidate"
    pretest, manifest = candidate_freeze.freeze_candidate(
        template_path=ROOT / "clean_baseline" / "manifest.template.json",
        candidate_id="cbv1-test-candidate",
        source_commit="c" * 40,
        dataset_source_description="fixture CIFAR-10 source",
        raw_source_sha256="d" * 64,
        ledger_path=ledger,
        ledger_manifest_path=ledger_manifest,
        oof_plan_path=oof_plan,
        frozen_config_path=config,
        environment_lock_path=env,
        feature_order_path=features,
        artifact_paths=(artifact,),
        commands=("python run_clean_baseline.py --config frozen_config.json",),
        output_dir=out,
    )
    return {
        "ledger": ledger,
        "ledger_manifest": ledger_manifest,
        "oof_plan": oof_plan,
        "config": config,
        "env": env,
        "features": features,
        "artifact": artifact,
        "pretest": pretest,
        "manifest": manifest,
        "out": out,
    }


def test_candidate_freeze_is_pretest_only_and_integrity_verifiable(tmp_path, monkeypatch):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    candidate = json.loads(fixture["manifest"].read_text(encoding="utf-8"))

    assert candidate["status"] == "FROZEN_PRETEST"
    assert candidate["final_test"]["decisions_frozen"] is True
    assert candidate["final_test"]["sealed"] is False
    assert candidate["final_test"]["access_count_before_seal"] == 0
    assert candidate["leakage_audit"]["pretest_status"] == "UNKNOWN"
    assert candidate["batch_invariance"]["pretest_status"] == "UNKNOWN"

    verified = verify_frozen_candidate(fixture["manifest"])
    assert verified["candidate_id"] == "cbv1-test-candidate"

    with pytest.raises(LeakageError, match="final test is not sealed"):
        assert_manifest_ready_for_final_test(candidate)


def test_candidate_verifier_rejects_artifact_tampering(tmp_path, monkeypatch):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    fixture["artifact"].write_text("tampered\n", encoding="utf-8")
    with pytest.raises(LeakageError, match="hash mismatch"):
        verify_frozen_candidate(fixture["manifest"])


def test_final_test_authorization_requires_two_pass_gates_and_then_preflight_passes(tmp_path, monkeypatch):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    leakage = fixture["out"] / "leakage_gate.json"
    batch = fixture["out"] / "batch_gate.json"
    leakage.write_text(
        json.dumps(
            {
                "protocol_id": PROTOCOL_ID,
                "candidate_id": "cbv1-test-candidate",
                "status": "PASS",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    batch.write_text(
        json.dumps(
            {
                "protocol_id": PROTOCOL_ID,
                "candidate_id": "cbv1-test-candidate",
                "status": "PASS",
                "frozen_score_tolerance": 1e-8,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    authorized_path = fixture["out"] / "candidate.authorized.manifest.json"
    authorize_final_test(
        frozen_candidate_manifest=fixture["manifest"],
        leakage_gate_json=leakage,
        batch_invariance_gate_json=batch,
        split_ledger_path=fixture["ledger"],
        first_authorized_command="python evaluate_final_test.py --manifest candidate.authorized.manifest.json",
        output_path=authorized_path,
    )

    authorized = json.loads(authorized_path.read_text(encoding="utf-8"))
    assert authorized["status"] == "AUTHORIZED_FINAL_TEST"
    assert authorized["final_test"]["sealed"] is True
    assert authorized["leakage_audit"]["pretest_status"] == "PASS"
    assert authorized["batch_invariance"]["pretest_status"] == "PASS"
    assert_manifest_ready_for_final_test(authorized)
    assert run_preflight(authorized_path, split_ledger_path=fixture["ledger"]).startswith("PASS:")

    authorization_record = fixture["out"] / "final_test_authorization.json"
    assert authorization_record.is_file()
    assert authorized["final_test"]["authorization_record_sha256"] == sha256_file(authorization_record)


def test_final_test_authorization_rejects_failed_batch_gate(tmp_path, monkeypatch):
    fixture = _freeze_fixture(tmp_path, monkeypatch)
    leakage = fixture["out"] / "leakage_gate.json"
    batch = fixture["out"] / "batch_gate.json"
    leakage.write_text(
        json.dumps({"protocol_id": PROTOCOL_ID, "candidate_id": "cbv1-test-candidate", "status": "PASS"}),
        encoding="utf-8",
    )
    batch.write_text(
        json.dumps(
            {
                "protocol_id": PROTOCOL_ID,
                "candidate_id": "cbv1-test-candidate",
                "status": "FAIL",
                "frozen_score_tolerance": 1e-8,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(LeakageError, match="status is not PASS"):
        authorize_final_test(
            frozen_candidate_manifest=fixture["manifest"],
            leakage_gate_json=leakage,
            batch_invariance_gate_json=batch,
            split_ledger_path=fixture["ledger"],
            first_authorized_command="python evaluate_final_test.py",
            output_path=fixture["out"] / "authorized.json",
        )
