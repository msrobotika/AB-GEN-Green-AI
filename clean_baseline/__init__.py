"""Leakage guardrails and deterministic contracts for AB-GEN Clean Baseline v1.

This package is intentionally pre-execution infrastructure. Importing it does not
load datasets, train models, run inference or access historical artifacts.
"""

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
from .ledger_io import read_ledger_rows, verify_ledger_package
from .oof_plan import build_oof_fold_sets, verify_oof_plan, write_oof_plan
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
    "FIT_PHASE_ALLOWED_SPLITS",
    "FitAuthorization",
    "LedgerRow",
    "LeakageError",
    "OOFProducerAuthorization",
    "RawSample",
    "SampleRecord",
    "SourceSample",
    "SplitLedger",
    "StageReceipt",
    "TensorSignature",
    "assign_development_splits",
    "assign_oof_folds",
    "assert_manifest_ready_for_final_test",
    "assert_oof_exclusion",
    "authorize_fit",
    "authorize_oof_producer",
    "authorize_transform",
    "build_ledger_rows",
    "build_oof_fold_sets",
    "hash_feature_order",
    "hash_sample_bytes",
    "hash_sample_id_order",
    "inventory_cifar_python_dir",
    "make_stage_receipt",
    "read_ledger_rows",
    "tensor_signature",
    "verify_ledger_package",
    "verify_oof_plan",
    "write_oof_plan",
    "write_stage_receipts",
]
