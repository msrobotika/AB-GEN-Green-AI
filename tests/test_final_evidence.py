from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from clean_baseline.contracts import LeakageError
from clean_baseline import final_access, final_result
from clean_baseline.final_access import issue_final_test_access_token, validate_final_test_access_token
from clean_baseline.final_result import build_final_result_package, read_prediction_rows
from clean_baseline.split_ledger import PROTOCOL_ID, sha256_file


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_access_token_binds_exact_authorized_command_and_files(tmp_path, monkeypatch):
    ledger = _write(tmp_path / "split_ledger.csv", "frozen-ledger\n")
    command = "python final_runner.py --access-token evidence/final_access_token.json"
    record = {
        "protocol_id": PROTOCOL_ID,
        "candidate_id": "cbv1-test",
        "split_ledger_sha256": sha256_file(ledger),
        "first_authorized_command": command,
    }
    record_path = tmp_path / "final_test_authorization.json"
    record_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    manifest = {
        "protocol_id": PROTOCOL_ID,
        "candidate_id": "cbv1-test",
        "status": "AUTHORIZED_FINAL_TEST",
        "final_test": {
            "first_authorized_command": command,
            "authorization_record_path": record_path.name,
            "authorization_record_sha256": sha256_file(record_path),
        },
    }
    manifest_path = tmp_path / "candidate.authorized.manifest.json"
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

    monkeypatch.setattr(final_access, "assert_manifest_ready_for_final_test", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(final_access, "run_preflight", lambda *_args, **_kwargs: "PASS")

    token_path = tmp_path / "final_access_token.json"
    issue_final_test_access_token(
        authorized_manifest_path=manifest_path,
        split_ledger_path=ledger,
        intended_command=command,
        output_path=token_path,
    )

    token = validate_final_test_access_token(token_path, intended_command=command)
    assert token["candidate_id"] == "cbv1-test"

    with pytest.raises(LeakageError, match="exactly match"):
        issue_final_test_access_token(
            authorized_manifest_path=manifest_path,
            split_ledger_path=ledger,
            intended_command="python different.py",
            output_path=tmp_path / "bad.json",
        )

    ledger.write_text("changed-ledger\n", encoding="utf-8")
    with pytest.raises(LeakageError, match="changed after"):
        validate_final_test_access_token(token_path, intended_command=command)


def _write_prediction_csv(path: Path, *, bad_argmax: bool = False) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(final_result.PREDICTION_COLUMNS)
        for index in range(10_000):
            label = index % 10
            predicted = label
            scores = [0.0] * 10
            scores[label] = 1.0
            if bad_argmax and index == 0:
                predicted = (label + 1) % 10
            writer.writerow([f"id-{index:05d}", label, predicted, *scores])


def _fake_test_ledger():
    return tuple(
        SimpleNamespace(sample_id=f"id-{index:05d}", label=index % 10, split="test")
        for index in range(10_000)
    )


def test_final_result_package_requires_exact_test_identity_and_retains_metrics(tmp_path, monkeypatch):
    ledger = _write(tmp_path / "split_ledger.csv", "fixture-ledger\n")
    token_path = _write(tmp_path / "token.json", "{}\n")
    predictions = tmp_path / "raw_predictions.csv"
    _write_prediction_csv(predictions)

    token = {
        "candidate_id": "cbv1-test",
        "split_ledger_sha256": sha256_file(ledger),
        "authorized_manifest_sha256": "a" * 64,
        "authorization_record_sha256": "b" * 64,
    }
    monkeypatch.setattr(final_result, "validate_final_test_access_token", lambda *_args, **_kwargs: token)
    monkeypatch.setattr(final_result, "read_ledger_rows", lambda *_args, **_kwargs: _fake_test_ledger())

    out = tmp_path / "result"
    manifest = build_final_result_package(
        access_token_path=token_path,
        prediction_csv_path=predictions,
        ledger_path=ledger,
        score_semantics="decision_scores",
        output_dir=out,
    )

    assert manifest["correct_count"] == 10_000
    assert manifest["denominator"] == 10_000
    assert manifest["accuracy"] == 1.0
    assert (out / "final_predictions.csv").is_file()
    assert (out / "final_metrics.json").is_file()
    assert (out / "confusion_matrix.csv").is_file()
    assert (out / "final_result_manifest.json").is_file()

    metrics = json.loads((out / "final_metrics.json").read_text(encoding="utf-8"))
    assert metrics["macro_f1"] == 1.0
    assert metrics["probability_calibration_claimed"] is False


def test_prediction_reader_rejects_label_not_derived_from_score_argmax(tmp_path):
    predictions = tmp_path / "bad_predictions.csv"
    _write_prediction_csv(predictions, bad_argmax=True)
    with pytest.raises(LeakageError, match="argmax"):
        read_prediction_rows(predictions)


def test_final_result_rejects_probability_claim_before_calibration_gate(tmp_path, monkeypatch):
    ledger = _write(tmp_path / "split_ledger.csv", "fixture-ledger\n")
    token_path = _write(tmp_path / "token.json", "{}\n")
    predictions = tmp_path / "raw_predictions.csv"
    _write_prediction_csv(predictions)
    monkeypatch.setattr(
        final_result,
        "validate_final_test_access_token",
        lambda *_args, **_kwargs: {
            "candidate_id": "cbv1-test",
            "split_ledger_sha256": sha256_file(ledger),
            "authorized_manifest_sha256": "a" * 64,
            "authorization_record_sha256": "b" * 64,
        },
    )
    monkeypatch.setattr(final_result, "read_ledger_rows", lambda *_args, **_kwargs: _fake_test_ledger())

    with pytest.raises(LeakageError, match="score_semantics"):
        build_final_result_package(
            access_token_path=token_path,
            prediction_csv_path=predictions,
            ledger_path=ledger,
            score_semantics="probabilities",
            output_dir=tmp_path / "result",
        )
