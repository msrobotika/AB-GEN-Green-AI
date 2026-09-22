from __future__ import annotations

from hashlib import sha256

import numpy as np
import pytest
from sklearn.decomposition import PCA

from clean_baseline.contracts import LeakageError, SampleRecord, SplitLedger
from clean_baseline.pca_stage import (
    PCAConfig,
    fit_pca,
    load_pca_artifact,
    pca_feature_names,
    save_pca_artifact,
    transform_pca,
)
from clean_baseline.raw_store import RawBatch, normalize_unit_float32


def _sid(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _normalized_batch(prefix: str, count: int, *, label_offset: int = 0):
    sample_ids = tuple(_sid(f"{prefix}:{index}") for index in range(count))
    values = np.empty((count, 3072), dtype=np.uint8)
    for row in range(count):
        values[row] = (np.arange(3072, dtype=np.uint16) * (row + 3) + row * 17) % 256
    labels = np.asarray([(row + label_offset) % 10 for row in range(count)], dtype=np.int64)
    raw = RawBatch(sample_ids=sample_ids, labels=labels, values=values)
    return normalize_unit_float32(raw, purpose="synthetic PCA test")


def _ledger_for(batch, split: str) -> SplitLedger:
    return SplitLedger(SampleRecord(sample_id, int(label), split) for sample_id, label in zip(batch.sample_ids, batch.labels))


def _combined_ledger(*items) -> SplitLedger:
    records = []
    for batch, split in items:
        records.extend(
            SampleRecord(sample_id, int(label), split)
            for sample_id, label in zip(batch.sample_ids, batch.labels)
        )
    return SplitLedger(records)


def test_full_pca_development_fit_is_deterministic_and_receipted():
    batch = _normalized_batch("train", 12)
    ledger = _ledger_for(batch, "train_core")
    config = PCAConfig(n_components=4, svd_solver="full", fit_dtype="float64")

    first = fit_pca(batch, ledger=ledger, config=config, phase="development_preprocessing_fit")
    second = fit_pca(batch, ledger=ledger, config=config, phase="development_preprocessing_fit")

    assert first.to_bytes() == second.to_bytes()
    assert first.artifact_sha256 == second.artifact_sha256
    assert first.components.shape == (4, 3072)
    assert first.mean.shape == (3072,)
    assert first.feature_names == pca_feature_names(4)
    assert first.fit_authorization.phase == "development_preprocessing_fit"
    assert first.fit_authorization.split_counts == {"train_core": 12}

    transformed = transform_pca(first, batch, ledger=ledger, purpose="development PCA")
    assert transformed.values.shape == (12, 4)
    assert transformed.values.dtype == np.float64
    assert transformed.values.flags.writeable is False
    assert transformed.labels.flags.writeable is False
    assert transformed.receipt.artifact_sha256 == first.artifact_sha256
    assert transformed.receipt.fit_authorization_sha256 is not None


def test_manual_transform_matches_sklearn_full_pca():
    batch = _normalized_batch("train", 10)
    ledger = _ledger_for(batch, "train_core")
    config = PCAConfig(n_components=3, svd_solver="full", fit_dtype="float64")
    artifact = fit_pca(batch, ledger=ledger, config=config, phase="development_preprocessing_fit")
    observed = transform_pca(artifact, batch, ledger=ledger, purpose="comparison")

    values = batch.values.astype(np.float64)
    expected = PCA(n_components=3, svd_solver="full", whiten=False).fit_transform(values)
    np.testing.assert_allclose(observed.values, expected, rtol=1e-12, atol=1e-12)


def test_development_pca_rejects_validation_rows():
    train = _normalized_batch("train", 8)
    validation = _normalized_batch("validation", 2, label_offset=3)
    merged = type(train)(
        sample_ids=train.sample_ids + validation.sample_ids,
        labels=np.concatenate([train.labels, validation.labels]),
        values=np.concatenate([train.values, validation.values], axis=0),
        receipt=train.receipt,
    )
    ledger = _combined_ledger((train, "train_core"), (validation, "validation"))

    with pytest.raises(LeakageError, match="fit-scope violation"):
        fit_pca(
            merged,
            ledger=ledger,
            config=PCAConfig(n_components=3),
            phase="development_preprocessing_fit",
        )


def test_pca_never_fits_final_test_rows():
    test = _normalized_batch("test", 8)
    ledger = _ledger_for(test, "test")

    with pytest.raises(LeakageError, match="FINAL TEST LEAKAGE"):
        fit_pca(
            test,
            ledger=ledger,
            config=PCAConfig(n_components=3),
            phase="final_preprocessing_refit",
        )


def test_oof_pca_requires_disjoint_producer_and_heldout_ids():
    producer = _normalized_batch("producer", 10)
    held_out = _normalized_batch("heldout", 3, label_offset=2)
    ledger = _combined_ledger((producer, "train_core"), (held_out, "validation"))
    config = PCAConfig(n_components=3)

    artifact = fit_pca(
        producer,
        ledger=ledger,
        config=config,
        phase="oof_producer_fit",
        oof_held_out_ids=held_out.sample_ids,
        fold_id=2,
    )
    assert artifact.fit_authorization.fold_id == 2
    assert artifact.fit_authorization.producer_sample_count == 10
    assert artifact.fit_authorization.held_out_sample_count == 3

    with pytest.raises(LeakageError, match="OOF LEAKAGE"):
        fit_pca(
            producer,
            ledger=ledger,
            config=config,
            phase="oof_producer_fit",
            oof_held_out_ids=(producer.sample_ids[0],) + held_out.sample_ids,
            fold_id=2,
        )


def test_oof_artifact_transforms_heldout_without_refitting():
    producer = _normalized_batch("producer", 10)
    held_out = _normalized_batch("heldout", 3, label_offset=2)
    ledger = _combined_ledger((producer, "train_core"), (held_out, "validation"))
    artifact = fit_pca(
        producer,
        ledger=ledger,
        config=PCAConfig(n_components=3),
        phase="oof_producer_fit",
        oof_held_out_ids=held_out.sample_ids,
        fold_id=1,
    )

    transformed = transform_pca(artifact, held_out, ledger=ledger, purpose="OOF held-out transform")
    assert transformed.sample_ids == held_out.sample_ids
    assert transformed.values.shape == (3, 3)
    assert transformed.receipt.fit_authorization_sha256 is not None


def test_randomized_pca_requires_explicit_seed_and_is_repeatable():
    batch = _normalized_batch("train", 18)
    ledger = _ledger_for(batch, "train_core")

    with pytest.raises(LeakageError, match="explicit integer random_state"):
        fit_pca(
            batch,
            ledger=ledger,
            config=PCAConfig(n_components=5, svd_solver="randomized", random_state=None),
            phase="development_preprocessing_fit",
        )

    config = PCAConfig(
        n_components=5,
        svd_solver="randomized",
        random_state=1729,
        iterated_power=5,
        n_oversamples=8,
        power_iteration_normalizer="QR",
    )
    first = fit_pca(batch, ledger=ledger, config=config, phase="development_preprocessing_fit")
    second = fit_pca(batch, ledger=ledger, config=config, phase="development_preprocessing_fit")
    assert first.to_bytes() == second.to_bytes()


def test_artifact_file_roundtrip_is_byte_stable(tmp_path):
    batch = _normalized_batch("train", 12)
    ledger = _ledger_for(batch, "train_core")
    artifact = fit_pca(
        batch,
        ledger=ledger,
        config=PCAConfig(n_components=4),
        phase="development_preprocessing_fit",
    )
    path = tmp_path / "pca.abgen"
    digest = save_pca_artifact(artifact, path)
    loaded = load_pca_artifact(path)

    assert digest == sha256(path.read_bytes()).hexdigest()
    assert loaded.to_bytes() == path.read_bytes()
    assert loaded.artifact_sha256 == artifact.artifact_sha256
    np.testing.assert_array_equal(loaded.components, artifact.components)
    np.testing.assert_array_equal(loaded.mean, artifact.mean)


def test_pca_config_rejects_implicit_or_unimplemented_modes():
    with pytest.raises(LeakageError, match="must be explicit"):
        PCAConfig(n_components=3, svd_solver="auto").validate()
    with pytest.raises(LeakageError, match="whitening is not implemented"):
        PCAConfig(n_components=3, whiten=True).validate()
    with pytest.raises(LeakageError, match="random_state=None"):
        PCAConfig(n_components=3, svd_solver="full", random_state=7).validate()
