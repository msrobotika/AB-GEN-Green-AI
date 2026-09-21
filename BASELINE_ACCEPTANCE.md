# AB-GEN Baseline Acceptance Gates

This document defines what may be claimed during historical recovery and what is required for a new clean AB-GEN baseline. It prevents a recovered artifact, successful run or rounded metric match from being mistaken for exact reproduction.

## Part A — Historical recovery evidence states

### 1. Reported
A historical result is recorded in notes, logs, spreadsheets, screenshots or other project evidence, but has not been rerun from a fully frozen evidence package.

Example: V24 Slow Burn CIFAR-10 **80.14%** remains `Reported`.

### 2. Recovered
Use `Recovered` only when candidate source/artifacts have been located and preserved without modifying originals.

Required evidence:
- private original paths/provenance retained;
- working copies separated from originals;
- SHA-256 hashes and sizes recorded;
- timestamps captured where available;
- producing environment/configuration recorded when recoverable;
- ambiguity between competing candidate artifacts stated explicitly.

Recovery does not prove that the artifact set produced the historical metric.

### 3. Pipeline reconstructed
Use `Pipeline reconstructed` when a materially complete historical path can be executed from the recovered evidence with transformation stages identified.

For V24, as applicable:

`raw input -> preprocessing -> PCA -> Fisher weighting -> spectral/geometric features -> N1 -> N2 -> output`

Required evidence:
- preprocessing boundaries identified;
- fitted transforms identified/frozen;
- feature dimensions documented;
- N1/N2 artifacts/config identified;
- noise/augmentation/inference averaging behavior documented;
- seeds and deterministic/non-deterministic operations recorded;
- no silently substituted newly trained component.

### 4. Metric reproduced
Use `Metric reproduced` only when a clean evaluation run on the proven historical evaluation split matches the historical metric at documented reporting precision.

Required evidence:
- split provenance proven;
- denominator and exact correct count retained;
- metric implementation documented;
- run log/environment retained;
- no known material leakage failure.

Metric reproduction alone does not prove prediction identity.

### 5. Prediction reproduced
Use `Prediction reproduced` when retained historical sample-level outputs can be compared against a rerun and satisfy the declared comparison contract.

Required evidence:
- stable `sample_id` mapping;
- row-order-independent comparison;
- exact predicted-label comparison;
- true-label comparison where available;
- comparable score columns checked with explicit tolerance;
- machine-readable report retained;
- all mismatches documented.

Use `tools/compare_predictions.py` for the standard comparison format.

### 6. Reproduced historical route
Use `Reproduced` for a historical route only when all applicable gates pass:

1. source/artifacts frozen and hashed;
2. dataset/split provenance established;
3. environment/seeds recorded;
4. pipeline reconstructed from frozen evidence;
5. leakage audit has no `FAIL` and no unresolved material `UNKNOWN`;
6. metric evidence retained;
7. prediction-level comparison retained when historical outputs exist;
8. manifest/logs linked to the evidence package;
9. limitations stated explicitly.

If historical sample-level outputs no longer exist, exact prediction reproduction may be impossible; that limitation must be stated.

## Current historical classification

- V24 Slow Burn **80.14%** — `Reported`.
- Elite / Slow Burn **80.17%** — `Recovered` PCA-cache execution.
- M5 MASTER **79.55%** — `Reconstructed / executed`.
- M4 **78.05%** — `Recovered` PCA-cache execution.

None of these classifications may be silently upgraded because a nearby aggregate accuracy is obtained.

## Historical batch-dependence finding

The recovered historical meta-feature path resets an RNG per call and assigns perturbation noise according to array shape/batch position. A targeted low-margin audit demonstrated prediction changes under different batch contexts.

This behavior is part of the recovered forensic record. It is not an acceptable hidden dependency for a new clean baseline.

## Part B — Clean Baseline v1 acceptance

A new clean baseline is not required to reproduce 80.14%. It is required to produce a defensible result from raw data under controlled boundaries.

### Data gate

- raw dataset source/version recorded;
- stable sample IDs retained;
- train/validation/calibration/test identities frozen before fitting;
- class counts recorded;
- final test excluded from all fitting, tuning and topology/model selection.

### Preprocessing gate

- normalization fit scope recorded;
- PCA fit on permitted training data only;
- Fisher weights fit on permitted training data only;
- class centroids fit on permitted training data only;
- augmentation/noise statistics fit on permitted training data only;
- exact preprocessing artifacts persisted and hashed.

### Stacking gate

- N1 model-selection scope documented;
- N2 training features generated OOF or from a clean holdout;
- no in-sample stacking leakage;
- final test predictions generated only after decisions are frozen.

### Determinism / invariance gate

For the same stable sample, compare logits/predictions under:
- repeated identical calls;
- individual inference;
- multiple batch sizes;
- multiple positions;
- different companion samples.

Default acceptance:
- class prediction invariant to accidental batch context;
- logit drift inside documented numerical tolerance;
- no hidden RNG reset/position assignment affecting a sample's inference result.

Any intentional contextual model must declare that context as part of the model input and evaluate it explicitly.

### Evidence freeze gate

- source commit immutable;
- exact command/config retained;
- seeds/dtypes/device mode recorded;
- dependency lock/environment export retained;
- preprocessing/model hashes retained;
- full final predictions retained;
- confusion matrix/per-class metrics retained;
- clean rerun from a fresh environment reproduces accepted outputs within tolerance.

### Promotion rule

A Clean Baseline v1 result becomes `Reproduced` only after the above gates pass. It becomes `Validated` only after additional calibration/benchmark/domain gates relevant to the claim also pass.

A clean result lower than historical project records is still accepted and must be reported without tuning the final test to recover a preferred headline.

## Failure handling

If any candidate fails a gate:
- preserve the result and logs;
- record the failed gate;
- do not overwrite historical evidence;
- do not tune against the final test to force a match;
- classify the candidate at the highest evidence state actually supported;
- convert the failure into a test or explicit open issue where practical.
