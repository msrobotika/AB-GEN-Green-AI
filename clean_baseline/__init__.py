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

__all__ = [
    "FIT_PHASE_ALLOWED_SPLITS",
    "LeakageError",
    "RawSample",
    "SampleRecord",
    "SplitLedger",
    "assign_development_splits",
    "assign_oof_folds",
    "assert_manifest_ready_for_final_test",
    "assert_oof_exclusion",
    "hash_sample_bytes",
]
