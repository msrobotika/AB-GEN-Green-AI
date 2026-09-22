# AB-GEN Milestones

This file tracks AB-GEN using an evidence-first standard. A performance claim is promoted only when the evidence package satisfies the relevant acceptance gate.

## 2026-09-22 — Phase 1 recovery/audit closure

Phase 1 is now closed **documentarily**, not as an end-to-end historical reproduction. The exact historical RAW → preprocessing/augmentation → PCA producer has still not been recovered, so no historical CIFAR-10 route is promoted to `Reproduced`.

### Expanded batch-dependence characterization
- The recovery audit expanded the batch-sensitivity experiment to **1,120 configurations plus 2,240 repeat/control executions**.
- **344 configurations changed predicted class relative to individual inference** under the tested recovered path.
- **0 changes were observed between identical repeated executions**.
- Controlled tests showed that changing the assignment of the recovered inference noise is sufficient to reproduce the observed class changes, while fixing that noise removes the observed batch-induced class changes under the tested conditions.
- This strengthens the conclusion that the recovered historical inference path is deterministic for an identical call but is not sample-context invariant. It still does **not** prove that this mechanism explains the historical 80.14% versus recovered 80.17% difference.

### Stable prediction evidence
- Three 10,000-row prediction CSVs were prepared with `sample_id,predicted_label,true_label`.
- `sample_id` is derived from the SHA-256 of the 3,072 RAW CIFAR-10 image bytes.
- All 10,000 sample identifiers were checked as unique and the label vectors were checked.
- Because the historical PCA producer remains missing, this does not by itself prove complete cache→RAW identity.

### Historical screenshot evidence recovered
Three original screenshots supplied by the project author were archived in the AB-GEN reproducibility evidence store. They are classified as **historical documentary evidence**, not as autonomous reproduction evidence.

They document:
- a V23 / M4 PURIST run using a PCA cache, Fisher weights/centroids, 3,091 constructed features, TorchLR, TorchMLP and LightGBM;
- the historical M4 result `N1 + TTA = 77.02%` and `N2 final = 78.05%`, consistent with the recovered 7,805/10,000 cache-path result;
- a V24 rescue screen showing `N1 + TTA (El Enjambre M5) = 78.45%` and `N2 Rescatado (Linear puro) = 79.37%`.

Original screenshot SHA-256 values:
- `248ab8ad2b6fc1cc99ee7e672c2222397848fcce1e5e05c82cdef7c42c98bf1e`
- `b9e4c95d473dfbae6d9407a786f6a576ccd30bbc0a1edd5d562b3756ab0f4298`
- `7e7893bbc0a4e82587e518b66d3dc54c640af69580b17d35170a8ed2647b1a42`

Visible historical filenames/artifacts such as `ab_gem_v22_1_ramsafe.py` and `v24_n1.pkl` are now provenance search leads. The screenshots do not recover the missing RAW→PCA transformer by themselves.

### Additional audit boundaries
- A recovered M5 demo/evaluation route uses test labels when fitting N2. That route is therefore invalid as an estimate of generalization on that same test set and is kept isolated from accepted evaluation evidence.
- The available historical XAI heatmap is currently supported as a weighted PCA reconstruction/visualization, not as demonstrated faithful attribution of the N1/N2 decision.
- Historical energy constants remain non-measurement evidence. Derived arithmetic from those constants must not be presented as experimentally demonstrated energy savings.
- Connectome remains a future experimental track; no Connectome training/performance result is claimed.

## Verified engineering milestones

### 2026-09-21 — Public diagnostic path hardened
- Removed UI/API calculations that exposed historical energy constants as numerical savings metrics.
- Energy status is now `unavailable_pending_controlled_measurement` until the controlled benchmark is executed.
- Replaced random cached-batch sampling with deterministic stored-order traversal.
- Added explicit status fields for the recovered historical path and known batch-invariance failure.
- Corrected visible recovered inference ordering to PCA → Fisher weighting → FFT/geometric expansion → N1 → polynomial N2.

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
| V24 rescue screenshot | **79.37%** | **HISTORICAL DOCUMENTARY EVIDENCE** | Screenshot of rescue run; not an independently reproduced metric. |
| MNIST Universal V24 | **97.79%** | **REPORTED** | Historical project record; exact reproduction pending. |

## Current audit risks

### RAW→PCA provenance
The exact historical transformer and raw preprocessing lineage remain unresolved. PCA test leakage is not demonstrated, but cannot yet be ruled out.

### Leakage
Recovered MASTER logic contains class-dependent processing/augmentation state created before the final train-validation split. A separate M5 route using test labels to fit N2 is invalid for evaluating generalization on that test set.

### Batch dependence
The recovered historical meta-feature path is not sample-context invariant because per-call noise is assigned by array shape/position. The expanded audit quantifies the effect under tested configurations, but the causal relationship to historical headline differences is not established.

### Energy
Historical energy figures are unvalidated constants/calculations, not accepted measurements. No percentage-saving headline is currently accepted.

### XAI / calibration
Softmax-normalized Ridge decision scores are not calibrated probabilities. PCA/geometric visualizations are not, by themselves, evidence of faithful attribution.

## Clean Baseline v1 acceptance gate

The next performance result eligible for `Reproduced` status must come from a clean pipeline that:
1. starts from frozen raw data and immutable sample identities;
2. freezes split identities before data-dependent fitting;
3. fits PCA, Fisher weights, centroids and augmentation statistics on training data only;
4. generates N2 meta-features with leakage-safe OOF/holdout logic;
5. uses deterministic sample inference with no hidden batch-position dependence;
6. freezes source commit, seeds, dtype, feature ordering, environment and artifact hashes;
7. retains full test predictions and class metrics;
8. passes the leakage audit with no unresolved material failure;
9. reproduces the accepted output from a clean environment within documented tolerances.

A lower clean score is more valuable than a higher score whose data lineage cannot be defended.

## Roadmap — priority order
1. Preserve and hash all historical evidence and newly recovered screenshots.
2. Search historical storage for the RAW→PCA producer using recovered filenames/artifact clues.
3. Complete the independent historical leakage audit.
4. Implement and execute Clean Baseline v1 from raw data.
5. Freeze and reproduce the clean source/environment/artifacts/predictions.
6. Run controlled Green AI benchmarks only after the clean baseline exists.
7. Evaluate calibration and explanation fidelity.
8. Keep Connectome isolated until controlled C1 experiments are justified.

## Communication principle

AB-GEN should be presented as strongly as the evidence allows, and never more strongly. Historical records, documentary evidence, recovered execution, reconstructed pipelines, clean reproduction and independent validation are distinct states and must stay distinct.
