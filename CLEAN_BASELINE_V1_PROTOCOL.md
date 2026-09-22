# AB-GEN Clean Baseline v1 — Frozen Pre-Execution Protocol

**Status:** PRE-EXECUTION / NO TRAINING AUTHORIZED BY THIS DOCUMENT ALONE  
**Parent issue:** #39 — Clean Baseline v1: leakage-free RAW→prediction reference

This protocol freezes the data boundary and evidence rules for the first new AB-GEN CIFAR-10 reference whose scientific validity does not depend on recovering the historical V24 80.14% route.

The purpose of this phase is to make leakage and provenance failures structurally difficult before any final training is executed. A lower clean result is acceptable. The final test must never become a tuning dashboard.

## 1. Scope and non-goals

Clean Baseline v1 is a **new experiment**. It is not:

- a reconstruction of the historical 80.14% route;
- a seed search for a preferred score;
- an attempt to reuse recovered PCA caches as the baseline input;
- evidence that historical Green-AI or XAI claims were valid;
- a Connectome experiment.

Historical recovery remains a separate evidence track.

## 2. Immutable input identity

Dataset: CIFAR-10.

Before any data-dependent fitting, the execution package must bind the exact verified RAW source to an immutable cryptographic hash and record the source path/version.

Stable sample identity for Clean Baseline v1 is:

```text
sample_id = SHA256(exact raw image bytes)
```

The split builder must reject duplicate `sample_id` values. The existing exact-duplicate audit is useful prior evidence, but the execution manifest must independently bind the exact RAW source used by this baseline.

The official CIFAR-10 test partition remains the final test partition. It is not repartitioned and its labels are unavailable to preprocessing, fitting, topology/model selection, stacking, calibration or threshold selection.

## 3. Deterministic development split — no RNG

The official 50,000-image CIFAR-10 training partition is divided deterministically, class by class, using the stable `sample_id`.

For each class independently:

1. sort the 5,000 official-training samples by lowercase hexadecimal `sample_id` in ascending lexicographic order;
2. assign ranks `0..3999` to `train_core`;
3. assign ranks `4000..4499` to `validation`;
4. assign ranks `4500..4999` to `calibration_reserved`.

Expected totals:

| Split | Per class | Total | Clean Baseline v1 use |
|---|---:|---:|---|
| `train_core` | 4,000 | 40,000 | development fitting and model construction |
| `validation` | 500 | 5,000 | development/model-selection feedback only |
| `calibration_reserved` | 500 | 5,000 | sealed for downstream calibration work (#9); not used to improve Clean Baseline v1 accuracy |
| `test` | official 1,000 | 10,000 | final evaluation only after freeze |

This split algorithm is deliberately independent of scikit-learn RNG behavior and library version.

The generated split ledger must be persisted and SHA-256 hashed before model fitting begins.

## 4. Development/model-selection boundary

During development:

- normalization/statistics are fitted on `train_core` only;
- PCA is fitted on `train_core` only;
- Fisher weights are fitted on `train_core` only;
- class centroids are fitted on `train_core` only;
- augmentation/noise statistics are fitted on `train_core` only;
- N1 estimators are fitted on `train_core` only;
- architecture/hyperparameter/model-composition decisions may inspect `validation` metrics;
- `calibration_reserved` and `test` remain sealed.

Every validation access that influences a later choice must be recorded in the run/evidence log.

No decision may be changed because of final-test performance.

## 5. Choice freeze before stacking/final refit

Before the final OOF stacking build starts, freeze:

- preprocessing definitions and numerical options;
- PCA dimensionality and solver/settings;
- Fisher/centroid definitions;
- spectral/geometric feature definitions and feature order;
- N1 estimator types, hyperparameters and ensemble composition;
- N2 input definition, transforms, estimator type and hyperparameters;
- dtypes;
- deterministic flags;
- all explicit seeds still required by stochastic training algorithms;
- metric implementation and reporting precision.

The freeze must be represented in a machine-readable manifest/config and bound to the source commit.

## 6. N2 stacking — five-fold deterministic OOF

After model choices are frozen, form the `fit_pool` as:

```text
fit_pool = train_core ∪ validation = 45,000 samples
```

Create five deterministic stratified OOF folds. For each class independently:

1. take only `fit_pool` samples;
2. sort by `sample_id` ascending;
3. assign `fold = rank mod 5`.

Expected fold size: 9,000 samples total, 900 per class.

For every OOF fold:

- the complete data-dependent preprocessing path must be fitted using only the other four producer folds;
- this includes normalization, PCA, Fisher weights, centroids and any learned augmentation/noise statistics;
- N1 must be fitted only on the producer folds;
- the held-out fold is transformed/predicted without being used to fit any component in that fold-specific pipeline;
- every N2 training row must therefore come from a pipeline that did not fit on that row.

**Prohibited shortcut:** fitting PCA or another data-dependent preprocessing stage once on all 45,000 fit-pool rows and then generating “OOF” N1 outputs. That would contaminate the held-out OOF rows.

Persist for every OOF row:

- `sample_id`;
- true label;
- OOF fold;
- N1/meta-feature values in frozen order;
- producer configuration identifier/hash.

The N2 scaler/polynomial transform/estimator must be fitted only on the complete 45,000-row OOF meta-feature table.

## 7. Final N1 refit

After OOF generation and N2 fitting are complete, refit the final preprocessing + N1 route on the full 45,000-row `fit_pool` using the already frozen choices.

No hyperparameter, topology, feature or threshold decision may be changed after this refit because of `calibration_reserved` or final-test outcomes.

`calibration_reserved` remains unused by the core Clean Baseline v1 accuracy result. It is reserved for the separate calibration issue #9.

## 8. Deterministic inference contract

The clean route must not inherit the recovered historical batch-position noise behavior.

For stable sample IDs, the accepted candidate must test the same sample under:

- exact repeated calls;
- individual inference;
- batch sizes 2, 4, 8, 16, 32 and 64 where memory permits;
- multiple positions within a batch;
- different companion samples.

Default gate:

- predicted class must be invariant to accidental batch context;
- score/logit drift must remain within a documented numerical tolerance frozen before the test;
- no hidden RNG reset or position-dependent perturbation may alter a sample's inference result.

If a future model intentionally uses context, that context must be part of the declared model input. Clean Baseline v1 does not.

## 9. Final-test seal

The final test may be evaluated only after all model decisions are frozen and the preflight manifest is complete.

Immediately before final-test execution, the evidence package must contain:

- source commit;
- exact RAW source hash;
- split-ledger hash;
- frozen config hash;
- environment export/lock hash;
- seeds and deterministic flags;
- dtype/device mode;
- feature-order definition/hash;
- all preprocessing/model artifact hashes produced before test;
- completed pre-test leakage checklist;
- batch-invariance gate result on non-test/development evidence where applicable;
- declaration that `calibration_reserved` has not been used to tune Clean Baseline v1 accuracy.

After the seal, execute the final test as obtained. Do not retune to recover a preferred historical number.

## 10. Required final evidence package

Retain at minimum:

- immutable source commit;
- exact command/config;
- environment export and dependency lock;
- RAW source hash;
- split ledger + hash;
- feature-order specification;
- preprocessing/model artifact manifest with SHA-256;
- OOF fold ledger and OOF meta-features;
- final predictions keyed by stable `sample_id`;
- final class scores/logits with semantics documented;
- exact correct count and denominator;
- accuracy, macro F1, per-class metrics and confusion matrix;
- batch-invariance report;
- completed leakage audit;
- final-test access log;
- clean-environment rerun evidence.

## 11. Evidence-state promotion

Clean Baseline v1 is not `Reproduced` merely because one run completes.

Promotion to `Reproduced` requires the gates in `BASELINE_ACCEPTANCE.md`, including a fresh-environment rerun that reproduces the accepted outputs within predeclared tolerances.

Calibration, Green-AI benchmarking and external validation remain downstream gates and must not be silently conflated with this result.

## 12. Stop conditions

Stop the candidate and preserve evidence if any of the following occurs:

- any final-test sample/label enters a fit or selection scope;
- a supposedly OOF row was used by its producer pipeline during fitting;
- split identities change after fitting begins;
- a fitted transform has unknown training scope;
- the final test is inspected and then a model/feature/hyperparameter choice is changed;
- batch context changes the predicted class without being an explicit model input;
- required hashes/config/environment evidence cannot be bound to the candidate.

Do not repair a failed candidate by silently overwriting it. Record the failure and start a new candidate identifier if remediation changes the scientific path.

## 13. Current implementation phase

This branch initially implements only:

- the frozen protocol;
- deterministic split/fold contracts;
- leakage guards;
- a pre-execution manifest template;
- unit tests for those guardrails.

It does **not** execute training, download datasets, generate a new performance metric, run the historical exporters, or start Connectome experiments.
