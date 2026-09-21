# AB-GEN Reproducibility Protocol

This document defines the minimum evidence required before an AB-GEN result is promoted between evidence states.

## 1. Scope

A reproducible result must identify the exact relationship between:

`dataset -> split -> preprocessing -> PCA -> Fisher weighting -> geometric/spectral features -> N1 -> N2 -> evaluation`

No stage may rely on undocumented local state, manually selected files, hidden notebook state, or test-set information used during training/model selection.

Historical recovery and clean reproduction are different activities. Recovery may preserve defects for forensic fidelity; a clean baseline must remove undocumented leakage and hidden sample-context dependence.

## 2. Evidence states

Use these states consistently:

- **Reported** — recorded by the project but not yet recovered/reproduced from a frozen pipeline.
- **Recovered** — an original artifact or executable historical route has been located and evaluated, but the complete producing pipeline is not proven.
- **Reconstructed** — one or more missing stages have been rebuilt from evidence and executed; reconstruction must remain distinguishable from original artifacts.
- **Metric reproduced** — a clean run reaches the same aggregate metric, but historical prediction identity or exact pipeline identity may remain unproven.
- **Prediction reproduced** — sample-level predictions match the historical reference within the documented comparison rule.
- **Reproduced** — frozen source/artifacts/environment and the relevant data-integrity gates reproduce the accepted result.
- **Validated** — reproduced and additionally passed the relevant leakage, calibration, benchmark or domain-specific gates.
- **Independent validation** — reproduced/evaluated by a separate party, environment or external validation process.

A nearby rounded accuracy is never sufficient by itself to skip these distinctions.

## 3. Source freeze

For every candidate baseline:

- record the Git commit SHA or immutable source snapshot hash;
- record the exact training/evaluation entry points;
- preserve recovered originals unchanged;
- record configuration and command-line arguments;
- record all seeds and deterministic flags;
- record dtype, feature order and device mode where relevant;
- record Python, OS, package versions and relevant drivers/runtime versions.

## 4. Dataset integrity

Record:

- dataset name and version/source;
- checksums where practical;
- stable sample identities;
- exact train/validation/calibration/test partitions;
- class counts per partition;
- augmentation/filtering;
- exclusions and reason.

The split must be frozen before data-dependent fitting. The final test partition must not influence preprocessing fitting, feature fitting, topology/model selection, stacking, calibration or hyperparameter selection.

## 5. Leakage audit

Unless an explicitly documented nested protocol says otherwise, the following must be fit only on permitted training data:

- normalization statistics;
- PCA;
- Fisher weights;
- class centroids;
- augmentation/noise statistics;
- feature-selection steps;
- N1 learners;
- N2/meta-learner transformations and estimators;
- calibration transforms.

For stacking, N2 training inputs should be generated out-of-fold or from a clean holdout rather than from in-sample N1 predictions.

A clean reproduced/validated result requires `LEAKAGE_AUDIT_TEMPLATE.md` to contain no unresolved material `FAIL` or `UNKNOWN` item.

## 6. Determinism and batch invariance

The recovered historical V24-related path contains a per-call perturbation mechanism that has demonstrated sample-context dependence on a targeted subset. Therefore every clean baseline must explicitly test inference invariance.

For stable sample identities, compare prediction/logits under:

- repeated identical calls;
- single-sample inference;
- multiple batch sizes;
- multiple positions within a batch;
- different companion samples;
- CPU/GPU modes where both are supported.

A clean baseline must not contain hidden batch-position-dependent randomness. If a context-dependent mechanism is intentionally part of a future model, it must be explicit, reproducible and evaluated as part of the model definition.

## 7. Artifact freeze

Every runtime-critical artifact must appear in an artifact manifest with:

- filename and role;
- format and size;
- SHA-256;
- producing source commit;
- producing command/config;
- dataset/split provenance;
- library versions needed to deserialize/use it.

Persist exact preprocessing artifacts rather than refitting them at inference time.

### Hash-manifest tooling

Create a manifest:

```bash
python tools/artifact_manifest.py create --artifact model_bundle=abgen_bundle.pkl --artifact sample_data=sample_data.pkl --artifact training_module=training_module.py --output v24-artifacts.json
```

Verify it:

```bash
python tools/artifact_manifest.py verify --manifest v24-artifacts.json --artifact model_bundle=abgen_bundle.pkl --artifact sample_data=sample_data.pkl --artifact training_module=training_module.py
```

A verification failure means the artifact set must not be treated as the same frozen baseline. A manifest stored beside arbitrary untrusted artifacts does not establish provenance; a validated release must bind the accepted manifest to an immutable trusted release/commit and follow `SECURITY.md`.

## 8. Evaluation package

At minimum retain:

- correct count and denominator;
- aggregate accuracy;
- per-class precision/recall/F1;
- macro F1;
- confusion matrix;
- stable sample IDs and full predictions;
- raw decision scores when available;
- deterministic/repeated-run details;
- batch-invariance test output;
- wall-clock training/inference timing with measurement boundary stated.

Where score/probability language is used, report calibration metrics such as ECE, Brier score and NLL before calling outputs calibrated probabilities.

## 9. Green AI evidence

Energy claims require a separate controlled benchmark. Report:

- exact hardware;
- CPU/GPU mode;
- OS, drivers and runtime;
- measurement tool and sampling method;
- warm-up protocol;
- fixed input set;
- preprocessing boundary;
- batch size;
- latency and throughput;
- repeated measurements and uncertainty;
- joules/image or joules/inference;
- RAM/VRAM;
- artifact size;
- the same measurement boundary and accuracy protocol for every baseline.

Carbon is derived from measured energy and must be reported separately.

Historical constants or estimates must not be promoted as measured benchmark evidence.

## 10. Historical V24 gate

The recorded CIFAR-10 V24 Slow Burn result of **80.14%** remains `Reported` until the exact historical source/artifact/prediction chain is demonstrated to the applicable evidence level.

Recovered **80.17%**, reconstructed **79.55%** and recovered **78.05%** routes remain separate evidence states and must not be merged into the 80.14% historical claim.

## 11. Clean Baseline v1 gate

The next baseline eligible for `Reproduced` status must:

- start from raw data with stable identities;
- freeze split identities before fitting;
- fit PCA and all class-dependent transforms on training data only;
- use leakage-safe stacking;
- use deterministic batch-invariant inference;
- freeze source/environment/seeds/dtype/feature order;
- retain model/preprocessing hashes and full predictions;
- access the final test only after model-selection choices are frozen;
- rerun successfully from a clean environment within documented tolerances.

A lower clean accuracy must be reported as-is. Evidence quality takes precedence over preserving a historical headline.

The purpose of this protocol is to make future AB-GEN claims traceable to immutable evidence rather than memory, local state or metric coincidence.
