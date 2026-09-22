"""Leakage guardrails and deterministic contracts for AB-GEN Clean Baseline v1.

Importing this package does not load datasets, train models, run inference or
access historical artifacts. Dataset access remains explicit and hash-bound.
"""

from .candidate_freeze import freeze_candidate
from .candidate_verify import verify_frozen_candidate
from .contracts import (
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
from .final_test_authorize import authorize_final_test
from .gate_evidence import (
    BATCH_GATE_SCHEMA,
    LEAKAGE_GATE_SCHEMA,
    REQUIRED_INVARIANCE_CONTEXTS,
    REQUIRED_LEAKAGE_CHECKS,
    build_batch_invariance_gate,
    build_leakage_gate,
)
from .gate_validate import validate_batch_invariance_gate, validate_leakage_gate
from .ledger_io import read_ledger_rows, verify_ledger_package
from .oof_plan import build_oof_fold_sets, verify_oof_plan, write_oof_plan
from .pca_stage import (
    PCAArtifact,
    PCAConfig,
    PCATransformedBatch,
    fit_pca,
    load_pca_artifact,
    pca_feature_names,
    save_pca_artifact,
    transform_pca,
)
from .raw_store import (
    NormalizedBatch,
    RawBatch,
    VerifiedCifarRawStore,
    cifar_raw_feature_names,
    normalize_unit_float32,
)
from .split_ledger import LedgerRow, SourceSample, build_ledger_rows, inventory_cifar_python_dir
from .stage_audit import (
    FitAuthorization,
    OOFProducerAuthorization,
    StageReceipt,
    TensorSignature,
    authorize_fit,
    authorize_oof_producer,
    authorize_transform,
    hash_feature_order,
    hash_sample_id_order,
    make_stage_receipt,
    tensor_signature,
    write_stage_receipts,
)

__all__ = [
    "BATCH_GATE_SCHEMA",
    "FIT_PHASE_ALLOWED_SPLITS",
    "FitAuthorization",
    "LEAKAGE_GATE_SCHEMA",
    "LedgerRow",
    "LeakageError",
    "NormalizedBatch",
    "OOFProducerAuthorization",
    "PCAArtifact",
    "PCAConfig",
    "PCATransformedBatch",
    "REQUIRED_INVARIANCE_CONTEXTS",
    "REQUIRED_LEAKAGE_CHECKS",
    "RawBatch",
    "RawSample",
    "SampleRecord",
    "SourceSample",
    "SplitLedger",
    "StageReceipt",
    "TensorSignature",
    "VerifiedCifarRawStore",
    "assign_development_splits",
    "assign_oof_folds",
    "assert_manifest_ready_for_final_test",
    "assert_oof_exclusion",
    "authorize_final_test",
    "authorize_fit",
    "authorize_oof_producer",
    "authorize_transform",
    "build_batch_invariance_gate",
    "build_leakage_gate",
    "build_ledger_rows",
    "build_oof_fold_sets",
    "cifar_raw_feature_names",
    "fit_pca",
    "freeze_candidate",
    "hash_feature_order",
    "hash_sample_bytes",
    "hash_sample_id_order",
    "inventory_cifar_python_dir",
    "load_pca_artifact",
    "make_stage_receipt",
    "normalize_unit_float32",
    "pca_feature_names",
    "read_ledger_rows",
    "save_pca_artifact",
    "tensor_signature",
    "transform_pca",
    "validate_batch_invariance_gate",
    "validate_leakage_gate",
    "verify_frozen_candidate",
    "verify_ledger_package",
    "verify_oof_plan",
    "write_oof_plan",
    "write_stage_receipts",
]
