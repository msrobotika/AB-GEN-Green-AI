from __future__ import annotations

from hashlib import sha256

import numpy as np
import pytest

from clean_baseline.contracts import LeakageError
from clean_baseline.raw_store import (
    VerifiedCifarRawStore,
    cifar_raw_feature_names,
    normalize_unit_float32,
)
from clean_baseline.split_ledger import CIFAR_BATCH_SPECS, LedgerRow


def _source_hashes() -> dict[str, str]:
    return {name: sha256(name.encode("utf-8")).hexdigest() for name, _ in CIFAR_BATCH_SPECS}


def _raw(seed: int) -> np.ndarray:
    base = np.arange(32 * 32 * 3, dtype=np.uint16)
    return ((base + seed) % 256).astype(np.uint8)


def _row(raw: np.ndarray, *, label: int, source_file: str, source_index: int, split: str) -> LedgerRow:
    partition = dict(CIFAR_BATCH_SPECS)[source_file]
    return LedgerRow(
        sample_id=sha256(raw.tobytes(order="C")).hexdigest(),
        label=label,
        source_partition=partition,
        source_file=source_file,
        source_index=source_index,
        split=split,
        oof_fold=0 if split in {"train_core", "validation"} else None,
    )


def _store_and_batches():
    train_a = _raw(1)
    train_b = _raw(2)
    test = _raw(3)
    rows = (
        _row(train_a, label=1, source_file="data_batch_1", source_index=0, split="train_core"),
        _row(train_b, label=2, source_file="data_batch_1", source_index=1, split="validation"),
        _row(test, label=3, source_file="test_batch", source_index=0, split="test"),
    )
    store = VerifiedCifarRawStore(root=".", rows=rows, expected_source_hashes=_source_hashes())
    batches = {
        "data_batch_1": (
            np.stack([train_a, train_b]),
            np.asarray([1, 2], dtype=np.int64),
        ),
        "test_batch": (
            np.stack([test]),
            np.asarray([3], dtype=np.int64),
        ),
    }
    return store, rows, batches


def _allow_bound_hashes(monkeypatch, store: VerifiedCifarRawStore) -> None:
    monkeypatch.setattr(
        "clean_baseline.raw_store.sha256_file",
        lambda path: store.expected_source_hashes[path.name],
    )


def test_open_rejects_changed_raw_source_before_deserialization(monkeypatch, tmp_path):
    expected = _source_hashes()
    rows = (_row(_raw(1), label=1, source_file="data_batch_1", source_index=0, split="train_core"),)

    monkeypatch.setattr(
        "clean_baseline.raw_store.verify_ledger_package",
        lambda *_args, **_kwargs: {"source_batch_sha256": expected},
    )
    monkeypatch.setattr("clean_baseline.raw_store.read_ledger_rows", lambda *_args, **_kwargs: rows)

    observed = dict(expected)
    observed["data_batch_3"] = "0" * 64
    monkeypatch.setattr("clean_baseline.raw_store.inventory_cifar_python_dir", lambda *_args, **_kwargs: observed)

    def forbidden_loader(*_args, **_kwargs):
        raise AssertionError("pickle deserialization must not occur before source hashes match")

    monkeypatch.setattr("clean_baseline.raw_store._load_verified_batch", forbidden_loader)

    with pytest.raises(LeakageError, match="RAW source hash mismatch"):
        VerifiedCifarRawStore.open(
            cifar_python_dir=tmp_path,
            ledger_path=tmp_path / "split_ledger.csv",
            ledger_manifest_path=tmp_path / "split_ledger.manifest.json",
        )


def test_batch_is_rehashed_immediately_before_pickle_deserialization(monkeypatch):
    store, rows, _batches = _store_and_batches()
    monkeypatch.setattr("clean_baseline.raw_store.sha256_file", lambda _path: "0" * 64)

    def forbidden_loader(*_args, **_kwargs):
        raise AssertionError("pickle load must not run after a just-in-time hash mismatch")

    monkeypatch.setattr("clean_baseline.raw_store._load_verified_batch", forbidden_loader)

    with pytest.raises(LeakageError, match="RAW source changed before deserialization"):
        store.read((rows[0].sample_id,), purpose="development preprocessing")


def test_read_preserves_requested_sample_order_and_rechecks_identity(monkeypatch):
    store, rows, batches = _store_and_batches()
    _allow_bound_hashes(monkeypatch, store)
    monkeypatch.setattr(
        "clean_baseline.raw_store._load_verified_batch",
        lambda path: batches[path.name],
    )

    requested = (rows[1].sample_id, rows[0].sample_id)
    batch = store.read(requested, purpose="development preprocessing")

    assert batch.sample_ids == requested
    assert batch.values.dtype == np.uint8
    assert batch.values.shape == (2, 3072)
    assert batch.labels.tolist() == [2, 1]
    assert batch.values.flags.writeable is False
    assert batch.labels.flags.writeable is False
    assert sha256(batch.values[0].tobytes(order="C")).hexdigest() == requested[0]
    assert sha256(batch.values[1].tobytes(order="C")).hexdigest() == requested[1]


def test_read_keeps_final_test_sealed_without_authorization(monkeypatch):
    store, rows, batches = _store_and_batches()
    _allow_bound_hashes(monkeypatch, store)
    monkeypatch.setattr(
        "clean_baseline.raw_store._load_verified_batch",
        lambda path: batches[path.name],
    )

    test_id = rows[2].sample_id
    with pytest.raises(LeakageError, match="FINAL TEST SEALED"):
        store.read((test_id,), purpose="unauthorized evaluation")

    batch = store.read(
        (test_id,),
        purpose="authorized final evaluation",
        final_test_authorized=True,
    )
    assert batch.labels.tolist() == [3]


def test_read_rejects_raw_bytes_that_no_longer_match_ledger(monkeypatch):
    store, rows, batches = _store_and_batches()
    _allow_bound_hashes(monkeypatch, store)
    corrupted = batches["data_batch_1"][0].copy()
    corrupted[0, 0] ^= np.uint8(1)
    batches["data_batch_1"] = (corrupted, batches["data_batch_1"][1])
    monkeypatch.setattr(
        "clean_baseline.raw_store._load_verified_batch",
        lambda path: batches[path.name],
    )

    with pytest.raises(LeakageError, match="RAW sample identity mismatch"):
        store.read((rows[0].sample_id,), purpose="development preprocessing")


def test_normalization_is_stateless_float32_and_receipted(monkeypatch):
    store, rows, batches = _store_and_batches()
    _allow_bound_hashes(monkeypatch, store)
    monkeypatch.setattr(
        "clean_baseline.raw_store._load_verified_batch",
        lambda path: batches[path.name],
    )

    raw = store.read((rows[0].sample_id, rows[1].sample_id), purpose="development preprocessing")
    normalized = normalize_unit_float32(raw, purpose="development preprocessing")

    assert normalized.values.dtype == np.float32
    assert normalized.values.shape == raw.values.shape
    assert normalized.values.flags.writeable is False
    assert normalized.labels.flags.writeable is False
    assert float(normalized.values.min()) >= 0.0
    assert float(normalized.values.max()) <= 1.0
    np.testing.assert_allclose(normalized.values, raw.values.astype(np.float32) / np.float32(255.0))

    assert normalized.receipt.stage == "raw_unit_scale"
    assert normalized.receipt.operation == "transform"
    assert normalized.receipt.fit_authorization_sha256 is None
    assert normalized.receipt.input_signature.sample_id_order_sha256 == normalized.receipt.output_signature.sample_id_order_sha256
    assert normalized.receipt.input_signature.feature_order_sha256 == normalized.receipt.output_signature.feature_order_sha256


def test_constructor_rejects_incomplete_source_hash_map():
    raw = _raw(1)
    rows = (_row(raw, label=1, source_file="data_batch_1", source_index=0, split="train_core"),)
    incomplete = _source_hashes()
    incomplete.pop("test_batch")

    with pytest.raises(LeakageError, match="source hash map mismatch"):
        VerifiedCifarRawStore(root=".", rows=rows, expected_source_hashes=incomplete)


def test_cifar_raw_feature_order_is_explicit_and_unique():
    names = cifar_raw_feature_names()
    assert len(names) == 3072
    assert len(set(names)) == 3072
    assert names[0] == "raw_R_0000"
    assert names[1023] == "raw_R_1023"
    assert names[1024] == "raw_G_0000"
    assert names[-1] == "raw_B_1023"
