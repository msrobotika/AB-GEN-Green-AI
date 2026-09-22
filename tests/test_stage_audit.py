from __future__ import annotations

from hashlib import sha256

import numpy as np
import pytest

from clean_baseline.contracts import LeakageError, SampleRecord, SplitLedger
from clean_baseline.stage_audit import (
    authorize_fit,
    authorize_oof_producer,
    authorize_transform,
    hash_feature_order,
    make_stage_receipt,
    tensor_signature,
)


def _sid(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _ledger() -> SplitLedger:
    return SplitLedger(
        [
            SampleRecord(_sid("train-a"), 0, "train_core"),
            SampleRecord(_sid("train-b"), 1, "train_core"),
            SampleRecord(_sid("val-a"), 0, "validation"),
            SampleRecord(_sid("cal-a"), 0, "calibration_reserved"),
            SampleRecord(_sid("test-a"), 0, "test"),
        ]
    )


def test_fit_authorization_records_scope_and_rejects_test():
    ledger = _ledger()
    train = [_sid("train-a"), _sid("train-b")]
    auth = authorize_fit(
        ledger,
        train,
        stage="pca",
        phase="development_preprocessing_fit",
    )
    assert auth.sample_count == 2
    assert auth.split_counts == {"train_core": 2}

    with pytest.raises(LeakageError, match="FINAL TEST LEAKAGE"):
        authorize_fit(
            ledger,
            [_sid("test-a")],
            stage="pca",
            phase="development_preprocessing_fit",
        )


def test_oof_authorization_proves_heldout_exclusion():
    ledger = _ledger()
    auth = authorize_oof_producer(
        ledger,
        [_sid("train-a"), _sid("train-b")],
        [_sid("val-a")],
        stage="fold-local-pca",
        fold_id=0,
    )
    assert auth.producer_sample_count == 2
    assert auth.held_out_sample_count == 1

    with pytest.raises(LeakageError, match="OOF LEAKAGE"):
        authorize_oof_producer(
            ledger,
            [_sid("train-a"), _sid("val-a")],
            [_sid("val-a")],
            stage="fold-local-pca",
            fold_id=0,
        )


def test_transform_blocks_test_until_final_preflight_authorizes_it():
    ledger = _ledger()
    with pytest.raises(LeakageError, match="FINAL TEST SEALED"):
        authorize_transform(ledger, [_sid("test-a")], purpose="final-evaluation")

    ids = authorize_transform(
        ledger,
        [_sid("test-a")],
        purpose="final-evaluation",
        final_test_authorized=True,
    )
    assert ids == (_sid("test-a"),)


def test_tensor_signature_requires_row_identity_alignment():
    values = np.zeros((2, 3), dtype=np.float32)
    sig = tensor_signature(values, [_sid("train-a"), _sid("train-b")], feature_names=["a", "b", "c"])
    assert sig.shape == (2, 3)
    assert sig.dtype == "float32"
    assert sig.feature_order_sha256 == hash_feature_order(["a", "b", "c"])

    with pytest.raises(LeakageError, match="row/sample mismatch"):
        tensor_signature(values, [_sid("train-a")])


def test_stage_receipt_binds_shapes_dtypes_sample_order_features_and_fit_scope():
    ledger = _ledger()
    ids = [_sid("train-a"), _sid("train-b")]
    auth = authorize_fit(
        ledger,
        ids,
        stage="pca",
        phase="development_preprocessing_fit",
    )
    x = np.zeros((2, 3072), dtype=np.uint8)
    z = np.zeros((2, 1200), dtype=np.float32)
    receipt = make_stage_receipt(
        stage="pca",
        operation="fit_transform",
        purpose="development",
        input_values=x,
        output_values=z,
        sample_ids=ids,
        output_feature_names=[f"pca_{index:04d}" for index in range(1200)],
        fit_authorization=auth,
        artifact_sha256="a" * 64,
    )
    assert receipt.protocol_id == "abgen-clean-baseline-v1"
    assert receipt.input_signature.shape == (2, 3072)
    assert receipt.output_signature.shape == (2, 1200)
    assert receipt.fit_authorization_sha256 is not None
    assert receipt.artifact_sha256 == "a" * 64
