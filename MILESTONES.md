# AB-GEN Milestones

This file tracks AB-GEN using an evidence-first standard. A performance claim is promoted only when the evidence package satisfies the relevant acceptance gate.

## 2026-09-22 — Recovery evidence continuity

Phase 1 remains closed **documentarily**, not as an end-to-end historical reproduction. The exact historical RAW → preprocessing/augmentation → PCA producer remains unresolved, so no historical CIFAR-10 route is promoted to `Reproduced historical route`.

### RAW duplicate audit
- Verified CIFAR-10 contains **50,000 train + 10,000 test = 60,000 byte-distinct images**.
- **0 exact duplicate images** were found within train, within test, or across train/test.
- The source archive hash was unchanged before and after the audit.
- This does **not** rule out perceptual similarity, augmentation dependence, fitting leakage or an incorrect cache→RAW association.

### Prediction and score evidence
- Three recovered routes now have **30,000 preserved prediction rows** with stable IDs derived from hashes of official RAW image bytes.
- Frozen M4 and M5 MASTER reruns matched preserved predicted classes **20,000 / 20,000**, retaining **7,805 / 10,000** and **7,955 / 10,000** correct.
- Elite score extraction matched preserved predicted classes **10,000 / 10,000**, retaining **8,017 / 10,000** correct.
- The current package contains **300,000 class scores** across the 30,000 evaluated rows.
- M4 score vectors are softmax outputs from its recovered N2 but are not calibration-certified probabilities.
- M5 MASTER and Elite score vectors are Ridge `decision_function` values and are not probabilities.
- A standalone standard-library verifier passes all **30,000 rows / 300,000 scores** and rejects three deliberately corrupted copies. This establishes internal package consistency, not external validation, RAW provenance or historical reproduction.

The exact-class matches above are checks against **preserved recovery outputs**. They do not identify or reproduce the missing historical 80.14% or 79.37% prediction sets.

### Sample-level route comparison

| Comparison | B corrects A | B loses an A correct | Different predictions | Net correct |
|---|---:|---:|---:|---:|
| M4 → M5 MASTER | 419 | 269 | 957 | +150 |
| M4 → Elite | 628 | 416 | 1,413 | +212 |
| M5 MASTER → Elite | 445 | 383 | 1,131 | +62 |

For M5 MASTER → Elite, another **303** samples change predicted class while both routes remain wrong. Therefore net accuracy differences must not be mistaken for the number of changed predictions. These are descriptive comparisons of recovered executions, not causal ablations.

### Expanded batch-dependence characterization
- Same 32 low-margin Ridge cases selected without labels.
- Batch sizes 1/2/4/8/16/32/64, multiple positions and two companion groups.
- **1,120 configurations / 2,240 executions**.
- **344 class changes** relative to individual inference, affecting 31 of the 32 targeted cases.
- **0 class changes with fixed noise**.
- **0 class changes without noise**.
- **0 differences between identical repeated calls**.
- Transferring the noise assigned in batch to individual inference reproduced the batch class in **1,120 / 1,120** configurations.
- Changing only companion samples produced **0 changes in 544 paired comparisons**.

These interventions demonstrate the cause of the class changes **within the tested matrix**. They do not estimate the frequency over the whole test set and do not prove the historical 80.14% versus recovered 80.17% difference was caused by this mechanism.

### Provenance clues added
- Binary inspection of the Elite bundle found `_sklearn_version` followed by **1.8.0**. This is a demonstrated serialization marker and only an environment clue, not proof of the full training environment.
- Historical M4 screenshots corroborate **Python 3.13.7 / GTX 1050 Ti** for that M4 context. This environment is not attributed to Elite without evidence.
- A V24 rescue screenshot documents `N1 + TTA = 78.45%` and a rescued linear N2 at **79.37%**.
- Preserved `v24_n2.pkl` is an MLP, M4 N2 has 30 inputs, and the polynomial M5/Elite bundles are distinct routes. No current artifact is identified as the exact rescued-linear-N2 checkpoint.
- Seven inputs expected by the historical exporter are absent at their resolved historical paths. Recovered bundle/cache/RAW copies elsewhere do not establish historical regeneration.

### XAI and energy boundaries refined
- Historical `_generate_heatmap` structure accesses PCA/Fisher state but not N1/N2 or a target class. Current evidence therefore supports a weighted PCA reconstruction/visualization, not faithful classifier attribution.
- Historical energy figures remain constants/derived arithmetic, not measured benchmark evidence. Correcting arithmetic from assumed constants does not upgrade the claim to measured efficiency.

## 2026-09-22 — Phase 1 recovery/audit closure

Phase 1 was closed **documentarily**, not as an end-to-end historical reproduction. The exact historical RAW → preprocessing/augmentation → PCA producer was not recovered, so no historical CIFAR-10 route was promoted to `Reproduced`.

### Historical screenshot evidence recovered
Three original screenshots supplied by the project author were archived as **historical documentary evidence**, not autonomous reproduction evidence.

They document:
- a V23 / M4 PURIST run using a PCA cache, Fisher weights/centroids, 3,091 constructed features, TorchLR, TorchMLP and LightGBM;
- historical M4 `N1 + TTA = 77.02%` and `N2 final = 78.05%`, consistent with the recovered 7,805/10,000 cache-path result;
- V24 `N1 + TTA = 78.45%` and `N2 Rescatado (Linear puro) = 79.37%`.

Original screenshot SHA-256 values:
- `248ab8ad2b6fc1cc99ee7e672c2222397848fcce1e5e05c82cdef7c42c98bf1e`
- `b9e4c95d473dfbae6d9407a786f6a576ccd30bbc0a1edd5d562b3756ab0f4298`
- `7e7893bbc0a4e82587e518b66d3dc54c640af69580b17d35170a8ed2647b1a42`

### Additional audit boundaries
- A separate recovered M5 demo/evaluation route uses test labels when fitting N2. It is invalid as an estimate of generalization on that same test set and remains isolated from accepted evaluation evidence.
- Historical energy constants remain non-measurement evidence.
- Connectome remains a future/documentary experimental track; no Connectome training/performance result is claimed.

## Verified engineering milestones

### 2026-09-21 — Public diagnostic path hardened
- Removed UI/API calculations that exposed historical energy constants as numerical savings metrics.
- Energy status is `unavailable_pending_controlled_measurement` until controlled benchmarking is executed.
- Replaced random cached-batch sampling with deterministic stored-order traversal.
- Added explicit status fields for the recovered historical path and known batch-invariance failure.
- Corrected visible recovered inference ordering to PCA → Fisher weighting → FFT/geometric expansion → N1 → N2.

### 2026-09-21 — Recovery audit produced executable evidence
- M4 recovered cache path: **7,805 / 10,000 = 78.05%**.
- M5 MASTER reconstructed/executed path: **7,955 / 10,000 = 79.55%**.
- Elite / Slow Burn recovered cache bundle: **8,017 / 10,000 = 80.17%**.
- Historical V24 Slow Burn: **80.14% REPORTED**, not reproduced end to end.

### 2026-09-21 — Baseline acceptance and leakage gates established
- Added `BASELINE_ACCEPTANCE.md`, `LEAKAGE_AUDIT_TEMPLATE.md` and deterministic prediction comparison tooling.
- Evidence states explicitly separate Reported, Recovered, Reconstructed, Reproduced and Validated claims.

### 2026-09-21 — Controlled Green AI benchmark protocol added
- Added `GREEN_AI_BENCHMARK_PROTOCOL.md`.
- This establishes a measurement protocol only; it does **not** validate historical energy-saving figures.

## Results currently under validation

| Route | Result | Evidence state | Boundary |
|---|---:|---|---|
| V24 Slow Burn historical record | **80.14%** | **REPORTED** | Exact RAW→PCA→model historical reproduction not established. |
| Elite / Slow Burn recovered bundle | **80.17%** | **RECOVERED** | Cache-path result; not exact reproduction of 80.14%. |
| M5 MASTER | **79.55%** | **RECONSTRUCTED / EXECUTED** | Original frozen N1 + reconstructed polynomial N2. |
| M4 | **78.05%** | **RECOVERED** | Cache-path result matching recorded M4 result. |
| V24 rescue screenshot | **79.37%** | **HISTORICAL DOCUMENTARY EVIDENCE** | Screenshot of rescue run; exact checkpoint/script unresolved. |
| MNIST Universal V24 | **97.79%** | **REPORTED** | Historical project record; exact reproduction pending. |

## Current audit risks

### RAW→PCA provenance
The exact historical transformer and raw preprocessing lineage remain unresolved. PCA test leakage is not demonstrated, but cannot yet be ruled out.

### Leakage
Recovered MASTER logic contains class-dependent processing/augmentation state created before its final train-validation split. A separate M5 route using test labels to fit N2 is invalid for evaluating generalization on that same test set. Do not automatically transfer either route's exact indices or defects to Elite without evidence.

### Batch dependence
The recovered historical meta-feature path is not sample-context invariant because per-call noise is assigned by array shape/position. The expanded targeted audit establishes the mechanism for tested class changes but does not establish population-wide prevalence or the cause of the 80.14%/80.17% historical difference.

### Energy
Historical energy figures are unvalidated constants/calculations, not accepted measurements. No percentage-saving headline is accepted.

### XAI / calibration
Recovered score representations are route-dependent and not accepted as calibrated probabilities. PCA/Fisher visualizations are not, by themselves, evidence of faithful classifier attribution.

## Clean Baseline v1 acceptance gate

The next performance result eligible for `Reproduced` status must come from a clean pipeline that:
1. starts from frozen raw data and immutable sample identities;
2. freezes train/validation/calibration/test identities before data-dependent fitting;
3. fits PCA, Fisher weights, centroids and augmentation statistics on training data only;
4. generates N2 meta-features with leakage-safe OOF/holdout logic;
5. uses deterministic sample inference with no hidden batch-position dependence;
6. freezes source commit, seeds, dtype, feature ordering, environment and artifact hashes;
7. retains full test predictions and class metrics;
8. passes the leakage audit with no unresolved material failure;
9. reproduces the accepted output from a clean environment within documented tolerances.

A lower clean score is more valuable than a higher score whose data lineage cannot be defended.

## Roadmap — priority order
1. Preserve and hash historical/recovered evidence without modifying originals.
2. Recover the exact RAW→PCA producer and preprocessing lineage if possible.
3. Recover the exact historical V24 80.14% source/config/predictions and the 79.37% rescued-linear-N2 checkpoint/script if possible.
4. Complete independent leakage/provenance review.
5. Build and execute Clean Baseline v1 from raw data.
6. Freeze and reproduce the clean source/environment/artifacts/predictions.
7. Run controlled Green AI benchmarks only after the clean baseline exists.
8. Evaluate calibration and explanation fidelity.
9. Keep Connectome isolated until controlled experiments are explicitly authorized and matched to the clean baseline.

## Communication principle

AB-GEN should be presented as strongly as the evidence allows, and never more strongly. Historical records, documentary evidence, recovered execution, reconstructed pipelines, clean reproduction and independent validation are distinct states and must stay distinct.
