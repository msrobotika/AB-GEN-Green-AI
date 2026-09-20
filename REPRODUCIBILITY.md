# AB-GEN Reproducibility Protocol

This document defines the minimum evidence required before an AB-GEN experimental result is promoted from **reported** to **reproduced/validated**.

## 1. Scope

A reproducible result must identify the exact relationship between:

`dataset -> split -> preprocessing -> PCA -> Fisher weighting -> geometric/spectral features -> N1 -> N2 -> evaluation`

No stage may rely on undocumented local state, manually selected files, hidden notebook state, or test-set information used during training/model selection.

## 2. Source freeze

For every candidate baseline:

- record the Git commit SHA or immutable source snapshot hash;
- record the exact entry point used for training and evaluation;
- preserve the original source unchanged;
- record all configuration files and command-line arguments;
- record all random seeds;
- record the Python version, OS, package versions and relevant driver/runtime versions.

## 3. Dataset integrity

Record:

- dataset name and version/source;
- checksum where practical;
- exact train/validation/calibration/test partitions;
- class counts per partition;
- any augmentation or filtering;
- any sample exclusions and the reason.

The final test partition must not influence feature fitting, model selection, stacking, calibration or hyperparameter selection.

## 4. Leakage audit

The following must be fitted only on permitted training data unless an explicitly documented nested protocol says otherwise:

- normalization statistics;
- PCA;
- Fisher weights;
- class centroids;
- feature-selection steps;
- N1 learners;
- N2/meta-learner transformations and estimators.

For stacking, N2 training inputs should be generated out-of-fold or from a clean holdout rather than from in-sample N1 predictions.

## 5. Artifact freeze

Every runtime-critical artifact must appear in an artifact manifest with:

- filename;
- role;
- format;
- size;
- SHA-256;
- producing source commit;
- producing command/config;
- dataset/split provenance;
- library versions needed to deserialize/use it.

Persist exact preprocessing artifacts whenever possible rather than refitting them at inference time.

## 6. Evaluation package

At minimum, a classification baseline should report:

- total accuracy;
- per-class precision/recall/F1;
- macro F1;
- confusion matrix;
- sample count;
- deterministic/repeated-run details;
- wall-clock training and inference timing with measurement boundary stated.

Where confidence values are exposed, also report calibration metrics such as ECE, Brier score and NLL before referring to them as calibrated probabilities.

## 7. Green AI evidence

Energy claims require a separate controlled benchmark. Report:

- exact hardware;
- CPU/GPU mode;
- OS, drivers and runtime;
- warm-up protocol;
- input set;
- preprocessing boundary;
- batch size;
- latency and throughput;
- repeated measurements;
- joules/image or joules/inference;
- RAM/VRAM;
- artifact size;
- the same measurement boundary for every baseline.

Carbon estimates are derived metrics and must be reported separately from measured energy.

## 8. Publication states

Use these states consistently:

- **Reported** — recorded by the project but not yet reproduced from frozen source/artifacts.
- **Reproduced** — reproduced from frozen source/artifacts under a documented environment.
- **Validated** — reproduced and additionally checked against the relevant audit/benchmark gates.
- **External validation** — independently reproduced or evaluated by a separate party/environment.

## 9. V24 Slow Burn golden-baseline gate

The recorded CIFAR-10 V24 Slow Burn result of **80.14%** remains **reported** until all of the following are complete:

- original source and artifacts recovered;
- hashes recorded;
- split and leakage audit completed;
- environment frozen;
- clean rerun completed;
- evaluation package generated;
- result linked to an immutable commit/release.

The purpose of this protocol is to make every future AB-GEN claim traceable to evidence rather than memory or local state.
