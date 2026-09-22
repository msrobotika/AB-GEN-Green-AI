from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from clean_baseline.contracts import LeakageError
from clean_baseline.preflight import run_preflight


ROOT = Path(__file__).resolve().parents[1]


def _ready_manifest() -> dict:
    template = json.loads(
        (ROOT / "clean_baseline" / "manifest.template.json").read_text(encoding="utf-8")
    )
    manifest = deepcopy(template)
    digest = "a" * 64
    manifest["candidate_id"] = "cbv1-preflight-test"
    manifest["source_commit"] = "deadbeefcafebabe"
    manifest["dataset"]["raw_source_sha256"] = digest
    manifest["splits"]["ledger_sha256"] = digest
    manifest["config"]["frozen_config_sha256"] = digest
    manifest["environment"]["lock_sha256"] = digest
    manifest["features"]["feature_order_sha256"] = digest
    manifest["artifacts"]["pretest_manifest_sha256"] = digest
    manifest["commands"] = ["python -m clean_baseline.future_runner --config frozen.json"]
    manifest["leakage_audit"]["pretest_status"] = "PASS"
    manifest["batch_invariance"]["pretest_status"] = "PASS"
    manifest["final_test"]["sealed"] = True
    manifest["final_test"]["decisions_frozen"] = True
    return manifest


def test_preflight_passes_complete_manifest_without_touching_test(tmp_path):
    manifest = _ready_manifest()
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert run_preflight(path).startswith("PASS:")


def test_preflight_checks_actual_split_ledger_hash_when_path_is_supplied(tmp_path):
    ledger = tmp_path / "split_ledger.csv"
    ledger.write_bytes(b"sample_id,label\n")
    manifest = _ready_manifest()
    manifest["splits"]["ledger_sha256"] = sha256(ledger.read_bytes()).hexdigest()
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert run_preflight(path, split_ledger_path=ledger).startswith("PASS:")

    ledger.write_bytes(b"tampered\n")
    with pytest.raises(LeakageError, match="split ledger hash mismatch"):
        run_preflight(path, split_ledger_path=ledger)


def test_preflight_fails_if_decisions_are_not_frozen(tmp_path):
    manifest = _ready_manifest()
    manifest["final_test"]["decisions_frozen"] = False
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(LeakageError, match="not frozen"):
        run_preflight(path)
