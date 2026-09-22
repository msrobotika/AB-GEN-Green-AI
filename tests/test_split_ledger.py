from __future__ import annotations

from functools import lru_cache
from hashlib import sha256

import pytest

from clean_baseline.contracts import LeakageError
from clean_baseline.split_ledger import (
    CIFAR_BATCH_SPECS,
    SourceSample,
    build_ledger_rows,
    inventory_cifar_python_dir,
    ledger_csv_bytes,
    load_verified_cifar_python_batches,
)


def _sid(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _full_source_samples() -> tuple[SourceSample, ...]:
    samples: list[SourceSample] = []
    source_index = 0
    for label in range(10):
        for index in range(5_000):
            samples.append(
                SourceSample(
                    sample_id=_sid(f"train:{label}:{index}"),
                    label=label,
                    source_partition="train",
                    source_file=f"synthetic-train-{index % 5}",
                    source_index=source_index,
                )
            )
            source_index += 1
        for index in range(1_000):
            samples.append(
                SourceSample(
                    sample_id=_sid(f"test:{label}:{index}"),
                    label=label,
                    source_partition="test",
                    source_file="synthetic-test",
                    source_index=index + label * 1_000,
                )
            )
    return tuple(samples)


def test_inventory_hashes_expected_six_files_without_unpickling(tmp_path):
    for filename, _partition in CIFAR_BATCH_SPECS:
        (tmp_path / filename).write_bytes(f"bytes:{filename}".encode("utf-8"))

    observed = inventory_cifar_python_dir(tmp_path)
    assert set(observed) == {filename for filename, _ in CIFAR_BATCH_SPECS}
    for filename, digest in observed.items():
        assert digest == sha256((tmp_path / filename).read_bytes()).hexdigest()


def test_hash_mismatch_stops_before_pickle_load(tmp_path, monkeypatch):
    for filename, _partition in CIFAR_BATCH_SPECS:
        (tmp_path / filename).write_bytes(f"bytes:{filename}".encode("utf-8"))

    expected = inventory_cifar_python_dir(tmp_path)
    expected["data_batch_3"] = "0" * 64

    def forbidden_loader(*_args, **_kwargs):
        raise AssertionError("pickle loader must not run before all hashes match")

    monkeypatch.setattr("clean_baseline.split_ledger._load_trusted_batch", forbidden_loader)
    with pytest.raises(LeakageError, match="source hash mismatch"):
        load_verified_cifar_python_batches(tmp_path, expected)


def test_verified_loader_requires_60000_unique_sample_ids(tmp_path, monkeypatch):
    for filename, _partition in CIFAR_BATCH_SPECS:
        (tmp_path / filename).write_bytes(f"verified:{filename}".encode("utf-8"))
    expected = inventory_cifar_python_dir(tmp_path)

    offsets = {name: batch_index * 10_000 for batch_index, (name, _) in enumerate(CIFAR_BATCH_SPECS)}

    def fake_loader(path, partition):
        offset = offsets[path.name]
        return tuple(
            SourceSample(
                sample_id=_sid(f"source:{offset + index}"),
                label=index % 10,
                source_partition=partition,
                source_file=path.name,
                source_index=index,
            )
            for index in range(10_000)
        )

    monkeypatch.setattr("clean_baseline.split_ledger._load_trusted_batch", fake_loader)
    samples, observed = load_verified_cifar_python_batches(tmp_path, expected)
    assert len(samples) == 60_000
    assert len({sample.sample_id for sample in samples}) == 60_000
    assert observed == expected


def test_ledger_rows_have_frozen_counts_oof_and_test_separation():
    rows = build_ledger_rows(_full_source_samples())
    assert len(rows) == 60_000
    assert rows == tuple(sorted(rows, key=lambda row: row.sample_id))

    counts = {split: 0 for split in ("train_core", "validation", "calibration_reserved", "test")}
    folds = {fold: 0 for fold in range(5)}
    for row in rows:
        counts[row.split] += 1
        if row.oof_fold is not None:
            folds[row.oof_fold] += 1
        if row.split == "test":
            assert row.source_partition == "test"
            assert row.oof_fold is None

    assert counts == {
        "train_core": 40_000,
        "validation": 5_000,
        "calibration_reserved": 5_000,
        "test": 10_000,
    }
    assert folds == {0: 9_000, 1: 9_000, 2: 9_000, 3: 9_000, 4: 9_000}


def test_ledger_serialization_is_deterministic_for_same_frozen_rows():
    rows = build_ledger_rows(_full_source_samples())
    payload_a = ledger_csv_bytes(rows)
    payload_b = ledger_csv_bytes(tuple(rows))
    assert payload_a == payload_b
    assert sha256(payload_a).hexdigest() == sha256(payload_b).hexdigest()
