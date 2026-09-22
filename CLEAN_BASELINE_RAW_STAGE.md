# AB-GEN Clean Baseline v1 — RAW execution boundary

This document describes the first executable data stage after the Clean Baseline v1 split/OOF/final-test guardrails.

It does **not** train PCA, Fisher, N1 or N2, and it does not authorize final-test evaluation.

## Purpose

`clean_baseline.raw_store.VerifiedCifarRawStore` turns the frozen split ledger into a hash-bound RAW reader for the official CIFAR-10 Python batches.

The contract is deliberately strict:

1. verify the split-ledger package and its SHA-256 binding;
2. read the six source-batch SHA-256 values from the frozen ledger manifest;
3. hash all six local CIFAR batch files before any pickle deserialization;
4. reject any source hash mismatch;
5. validate that every ledger row references the expected CIFAR source file/partition and an in-range source index;
6. lazily load only the source batch needed by an authorized sample request;
7. re-hash that batch immediately before its first `pickle.load` to close the hash-check/deserialization TOCTOU window;
8. for every returned row, recompute `sample_id = SHA256(exact 3072 uint8 bytes)` and compare it with the frozen ledger;
9. compare the source label with the frozen ledger label;
10. preserve the caller's requested sample-ID order exactly.

A mismatch at any step is a hard failure.

## Final-test seal

RAW reads pass through the existing `authorize_transform` contract. Test rows are rejected unless the caller is operating on the separately authorized final-test path.

The ordinary development/OOF code path must therefore leave final-test authorization disabled.

The future final evaluator must not expose a convenience switch that bypasses `candidate.authorized.manifest.json` preflight. The boolean plumbing currently used by the low-level transform contract is an internal boundary, not a user-facing authorization mechanism.

## Frozen RAW representation

CIFAR-10 Python batch rows are retained exactly as stored:

- shape per sample: `3072`;
- dtype: `uint8`;
- order: channel-major `R[1024], G[1024], B[1024]`;
- stable identity: SHA-256 of those exact 3072 bytes.

`cifar_raw_feature_names()` publishes the explicit 3,072-column order so stage receipts can bind it cryptographically.

## Stateless normalization

`normalize_unit_float32()` performs only:

```text
float32(raw_uint8) / float32(255.0)
```

It has no fitted state and therefore cannot learn from validation/test data.

The transform:

- requires `uint8 (N, 3072)` input;
- produces `float32 (N, 3072)` output;
- verifies finite values inside `[0, 1]`;
- preserves labels and sample order;
- emits a `StageReceipt` named `raw_unit_scale`;
- binds the explicit input/output feature order.

No dataset mean/std, whitening, PCA or other fitted preprocessing is hidden in this stage.

## Next implementation gate

After this RAW boundary is accepted, the next code should implement the first **fitted** preprocessing component under `authorize_fit` / `authorize_oof_producer`:

```text
RAW uint8
  -> unit float32
  -> fold-local fitted preprocessing/PCA
  -> fold-local Fisher weights + centroids
  -> frozen feature construction
  -> N1
  -> OOF meta-features
  -> N2
```

For OOF, PCA/Fisher/centroids must be fitted independently inside each producer fold. A single fit over all 45,000 fit-pool rows remains prohibited.

No performance number should be generated merely by merging this RAW-stage implementation.
