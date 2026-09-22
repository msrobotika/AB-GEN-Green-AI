from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from clean_baseline.contracts import (
    FIT_PHASE_ALLOWED_SPLITS,
    LeakageError,
    RawSample,
    SampleRecord,
    SplitLedger,
    assign_development_splits,
    assign_oof_folds,
    assert_manifest_ready_for_final_test,
    assert_oof_exclusion,
    hash_sample_bytes,
)


ROOT = Path(__file__).resolve().parents[1]


def _sample_id(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _full_raw_samples() -> tuple[RawSample, ...]:
    rows: list[RawSample] = []
    for label in range(10):
        rows.extend(
            RawSample(_sample_id(f"train:{label}:{index}"), label, "train")
            for index in range(5_000)
        )
        rows.extend(
            RawSample(_sample_id(f"test:{label}:{index}"), label, "test")
            for index in range(1_000)
        )
    return tuple(rows)


@lru_cache(maxsize=1)
def _full_ledger() -> SplitLedger:
    return SplitLedger(assign_development_splits(_full_raw_samples()))


def test_hash_sample_bytes_is_stable_sha256():
    raw = b"abgen-clean-baseline-sample"
    assert hash_sample_bytes(raw) == sha256(raw).hexdigest()
    assert hash_sample_bytes(bytearray(raw)) == sha256(raw).hexdigest()


def test_split_builder_is_order_independent_and_exact():
    forward = SplitLedger(assign_development_splits(_full_raw_samples()))
    reverse = SplitLedger(assign_development_splits(tuple(reversed(_full_raw_samples()))))

    forward_map = {record.sample_id: record.split for record in forward.records}
    reverse_map = {record.sample_id: record.split for record in reverse.records}
    assert forward_map == reverse_map

    forward.assert_exact_split_counts()
    assert len(forward.ids_for("train_core")) == 40_000
    assert len(forward.ids_for("validation")) == 5_000
    assert len(forward.ids_for("calibration_reserved")) == 5_000
    assert len(forward.ids_for("test")) == 10_000


def test_duplicate_sample_ids_are_rejected():
    duplicated = _sample_id("same")
    with pytest.raises(LeakageError, match="duplicate sample_id"):
        SplitLedger(
            [
                SampleRecord(duplicated, 0, "train_core"),
                SampleRecord(duplicated, 0, "validation"),
            ]
        )


def test_development_fit_rejects_validation_calibration_and_test():
    ledger = _full_ledger()
    train_id = next(iter(ledger.ids_for("train_core")))
    validation_id = next(iter(ledger.ids_for("validation")))
    calibration_id = next(iter(ledger.ids_for("calibration_reserved")))
    test_id = next(iter(ledger.ids_for("test")))

    ledger.assert_fit_scope([train_id], "development_preprocessing_fit")
    ledger.assert_fit_scope([train_id], "development_n1_fit")

    with pytest.raises(LeakageError, match="fit-scope violation"):
        ledger.assert_fit_scope([validation_id], "development_preprocessing_fit")
    with pytest.raises(LeakageError, match="fit-scope violation"):
        ledger.assert_fit_scope([calibration_id], "development_n1_fit")
    with pytest.raises(LeakageError, match="FINAL TEST LEAKAGE"):
        ledger.assert_fit_scope([test_id], "development_n1_fit")


def test_final_refit_allows_fit_pool_but_not_reserved_or_test():
    ledger = _full_ledger()
    train_id = next(iter(ledger.ids_for("train_core")))
    validation_id = next(iter(ledger.ids_for("validation")))
    calibration_id = next(iter(ledger.ids_for("calibration_reserved")))
    test_id = next(iter(ledger.ids_for("test")))

    ledger.assert_fit_scope([train_id, validation_id], "final_preprocessing_refit")
    ledger.assert_fit_scope([train_id, validation_id], "final_n1_refit")

    with pytest.raises(LeakageError, match="fit-scope violation"):
        ledger.assert_fit_scope([calibration_id], "final_n1_refit")
    with pytest.raises(LeakageError, match="FINAL TEST LEAKAGE"):
        ledger.assert_fit_scope([test_id], "final_preprocessing_refit")


def test_calibration_scope_is_separate_and_test_is_still_forbidden():
    ledger = _full_ledger()
    calibration_id = next(iter(ledger.ids_for("calibration_reserved")))
    test_id = next(iter(ledger.ids_for("test")))

    ledger.assert_fit_scope([calibration_id], "downstream_calibration_fit")
    with pytest.raises(LeakageError, match="FINAL TEST LEAKAGE"):
        ledger.assert_fit_scope([test_id], "downstream_calibration_fit")


def test_oof_fold_assignment_is_stratified_and_deterministic():
    ledger = _full_ledger()
    assignment_a = assign_oof_folds(ledger)
    assignment_b = assign_oof_folds(ledger)
    assert assignment_a == assignment_b
    assert len(assignment_a) == 45_000

    counts = {(label, fold): 0 for label in range(10) for fold in range(5)}
    for record in ledger.records:
        if record.sample_id in assignment_a:
            counts[(record.label, assignment_a[record.sample_id])] += 1

    assert set(counts.values()) == {900}


def test_oof_guard_rejects_any_producer_overlap():
    held_out = {_sample_id("held-out-a"), _sample_id("held-out-b")}
    clean_producer = {_sample_id("producer-a"), _sample_id("producer-b")}
    assert_oof_exclusion(held_out, clean_producer)

    contaminated = set(clean_producer)
    contaminated.add(next(iter(held_out)))
    with pytest.raises(LeakageError, match="OOF LEAKAGE"):
        assert_oof_exclusion(held_out, contaminated)


def test_machine_protocol_matches_code_fit_scopes():
    protocol = json.loads((ROOT / "clean_baseline" / "protocol.v1.json").read_text(encoding="utf-8"))
    assert protocol["protocol_id"] == "abgen-clean-baseline-v1"
    assert protocol["dataset"]["official_train_count"] == 50_000
    assert protocol["dataset"]["official_test_count"] == 10_000
    assert protocol["development_split"]["rng_used"] is False
    assert protocol["oof"]["folds"] == 5
    assert protocol["oof"]["fold_local_preprocessing_required"] is True

    encoded = {key: frozenset(value) for key, value in protocol["fit_scopes"].items()}
    assert encoded == FIT_PHASE_ALLOWED_SPLITS
    assert protocol["forbidden_fit_splits"] == ["test"]


def _ready_manifest() -> dict:
    template = json.loads(
        (ROOT / "clean_baseline" / "manifest.template.json").read_text(encoding="utf-8")
    )
    manifest = deepcopy(template)
    digest = "a" * 64
    manifest["candidate_id"] = "cbv1-ci-contract-test"
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


def test_manifest_template_fails_closed_before_freeze():
    template = json.loads(
        (ROOT / "clean_baseline" / "manifest.template.json").read_text(encoding="utf-8")
    )
    with pytest.raises(LeakageError):
        assert_manifest_ready_for_final_test(template)


def test_manifest_preflight_accepts_complete_sealed_candidate():
    assert_manifest_ready_for_final_test(_ready_manifest())


def test_manifest_preflight_rejects_prior_test_access():
    manifest = _ready_manifest()
    manifest["final_test"]["access_count_before_seal"] = 1
    with pytest.raises(LeakageError, match="accessed before"):
        assert_manifest_ready_for_final_test(manifest)


def test_manifest_preflight_rejects_calibration_tuning_of_accuracy():
    manifest = _ready_manifest()
    manifest["calibration_reserved"]["used_to_tune_clean_baseline_accuracy"] = True
    with pytest.raises(LeakageError, match="calibration_reserved"):
        assert_manifest_ready_for_final_test(manifest)
