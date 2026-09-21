# AB-GEN Milestones

This file tracks AB-GEN using an evidence-first standard. A performance claim is promoted only when the evidence package satisfies the relevant acceptance gate.

## Verified engineering milestones

### 2026-09-21 — Public diagnostic path hardened
- Removed UI/API calculations that exposed historical energy constants as numerical savings metrics.
- Energy status is now `unavailable_pending_controlled_measurement` until the controlled benchmark is executed.
- Removed ambiguous legacy API aliases such as generic `accuracy`, `confidence`, `prob` and `saving_pct` from the diagnostic contract.
- Replaced random cached-batch sampling with deterministic stored-order traversal, resettable to sample 0.
- Added explicit API/status fields for the recovered historical path and the known batch-invariance failure.
- Corrected the visible recovered inference ordering to PCA → Fisher weighting → FFT/geometric expansion → N1 → polynomial N2.
- Added regression guards preventing unvalidated energy headlines from reappearing in the public diagnostic UI.
- Source now documents the historical noise-averaging mechanism instead of hiding it behind a generic helper name.

### 2026-09-21 — Recovery audit produced executable evidence
- Recovered **M4** evaluation from the PCA-cache path at **7,805 / 10,000 = 78.05%**, matching the documented project result.
- Completed **M5 MASTER** evaluation with the original frozen N1 and reconstructed polynomial N2 at **7,955 / 10,000 = 79.55%**; saved prediction counts were checked.
- Evaluated the recovered **Elite / Slow Burn** bundle from cache at **8,017 / 10,000 = 80.17%**.
- The historical **80.14% V24 Slow Burn** headline remains **REPORTED** because the exact historical RAW→PCA transformer, split, script and prediction lineage have not been recovered end to end.
- Demonstrated a deterministic batch-dependent inference path on a targeted set of 32 low-margin Ridge samples: 18 changed class between full-batch and individual inference, 17 changed between full-batch and batch-32, while exact repeated batches produced zero changes.
- The recovered engine resets its RNG per call and assigns noise according to batch shape/position. This demonstrates batch dependence for the targeted subset, but does not establish that it explains the 80.14% versus 80.17% difference or generalize to the whole test set.
- Recovered elite fingerprints include Fisher and centroid structures matching MASTER, N2 scaler metadata for 21,000 rows, an MLP configured for 250 epochs with BatchNorm counters at 3,750, and 50 `logspace(-3,5,50)` N2 alpha candidates. These are provenance clues, not proof of exact historical split identity.

### 2026-09-21 — Baseline acceptance and leakage gates established
- Added `BASELINE_ACCEPTANCE.md` to separate **Reported**, **Recovered**, **Pipeline reconstructed**, **Metric reproduced**, **Prediction reproduced**, and **Reproduced** evidence states.
- Added `LEAKAGE_AUDIT_TEMPLATE.md` with mandatory `PASS` / `FAIL` / `UNKNOWN` review across dataset lineage, PCA, Fisher weighting, class centroids, N1 model selection, N2 stacking, augmentation/noise, calibration, and final-test access.
- Added `tools/compare_predictions.py` for deterministic sample-level comparison by stable `sample_id`, including optional score comparison and JSON evidence output.
- Added regression tests for row-order independence, label mismatches, score tolerances, sample-set mismatches, duplicate identifiers, and malformed scores.
- Merged through PR #33 after CI passed.

### 2026-09-21 — Controlled Green AI benchmark protocol added
- Added `GREEN_AI_BENCHMARK_PROTOCOL.md` defining model-only, end-to-end, and optional cold-start measurement boundaries.
- Defined hardware/environment freeze, warm-up, repeated-run statistics, batch-size matrix, synchronization, CPU/GPU separation, thermal/background-load controls, and raw evidence retention.
- Defined an energy-evidence hierarchy prioritizing direct measurement and requiring joules/image alongside any percentage comparison.
- This milestone establishes the protocol only; it does **not** validate historical energy-saving figures.

### 2026-09-20 — Repository hardening initiated
- Fixed `/api/reset` fixed-length class counters and added regression coverage.
- Established CPU regression CI on pushes and pull requests.
- Corrected missing clean-install dependencies.
- Established runtime/serialized-artifact security boundaries.
- Separated public Docker code from private runtime artifacts.
- Added SHA-256 manifest tooling and trusted-artifact documentation.
- Hardened public wording around reported accuracy and uncalibrated decision scores.

## Results currently under validation

### CIFAR-10 — V24 Slow Burn historical result
- Historical project record: **80.14%**.
- Evidence state: **REPORTED**.
- Exact RAW→PCA→model historical reproduction: **not established**.

### CIFAR-10 — Elite / Slow Burn recovered bundle
- Recovered cache-path result: **8,017 / 10,000 = 80.17%**.
- Evidence state: **RECOVERED**.
- Must not be presented as exact reproduction of the historical 80.14% route.

### CIFAR-10 — M5 MASTER reconstructed path
- Result: **7,955 / 10,000 = 79.55%**.
- Original N1 frozen; polynomial N2 reconstructed and executed.
- Evidence state: **RECONSTRUCTED / EXECUTED**.

### CIFAR-10 — M4
- Recovered cache-path result: **7,805 / 10,000 = 78.05%**.
- Evidence state: **RECOVERED**.

### MNIST — Universal V24
- Historical project record: **97.79%**.
- Evidence state: **REPORTED**.

## Current audit risks

### RAW→PCA provenance
The exact historical transformer and raw preprocessing lineage remain unresolved. PCA test leakage is not demonstrated, but cannot yet be ruled out.

### Leakage
Recovered MASTER logic contains class-dependent processing / augmentation state created before the final train-validation split. This is a material leakage concern for that route and requires independent audit. A separate demo route using test labels is invalid and must not be generalized to all routes without evidence.

### Batch dependence
The recovered historical meta-feature path is not sample-context invariant because per-call noise is assigned by array shape/position. Scope on the full test set remains unquantified.

### Energy
Historical energy figures are unvalidated and at least one derived million-inference calculation contains a factor-of-1,000 discrepancy. No percentage-saving headline is currently accepted.

### XAI / calibration
Softmax-normalized Ridge decision scores are not calibrated probabilities. PCA/geometric visualizations are not, by themselves, evidence of faithful attribution.

## Clean Baseline v1 acceptance gate

The next performance result eligible for `Reproduced` status must come from a clean pipeline that satisfies all of the following:

1. raw dataset version and immutable sample identities recorded;
2. split identities frozen before any data-dependent fitting;
3. PCA fit on training data only;
4. Fisher weights / centroids / augmentation statistics fit on training data only;
5. N2 meta-features generated with leakage-safe OOF or documented holdout logic;
6. deterministic sample inference with no hidden batch-position dependence;
7. exact source commit, seeds, dtype, feature ordering and dependency environment frozen;
8. model/preprocessing artifact hashes stored;
9. full test predictions and per-class metrics retained;
10. final test accessed only after model-selection decisions are frozen;
11. completed leakage audit contains no unresolved material `FAIL` or `UNKNOWN`;
12. rerun from a clean environment reproduces the accepted output within documented tolerances.

The clean baseline may score below historical records; evidence quality takes precedence over headline accuracy.

## Green AI gate

Any future efficiency claim additionally requires:
- same hardware / OS / software boundary for AB-GEN and baselines;
- model-only and end-to-end results separated;
- warm-up and fixed input set;
- batch size and repeated runs;
- latency / throughput / RAM / VRAM;
- measured joules per image and uncertainty;
- baseline accuracy under the same evaluation protocol;
- carbon conversion kept separate from measured energy.

## Connectome Edge R&D gate

The Connectome track is separate from historical recovery.
- **C0** literature/data/topology mapping may proceed.
- **C1** model-performance experiments should use the clean AB-GEN baseline as the reference.
- Biological topology must be compared against matched sparse-random, degree-preserving shuffled and parameter-matched dense controls.
- No superiority, neuromorphic or efficiency claim is accepted without controlled archived evidence.

## Roadmap — priority order

1. Finish repository/public evidence hardening and keep CI green.
2. Recover and freeze exact RAW→PCA provenance if possible.
3. Complete the independent historical leakage audit.
4. Implement and execute **Clean Baseline v1** from raw data.
5. Freeze clean source/environment/artifacts/predictions and reproduce them from a clean environment.
6. Characterize batch sensitivity of the historical route for forensic completeness; do not import that behavior into the clean baseline.
7. Execute controlled Green AI benchmarks against compact conventional baselines.
8. Evaluate calibration and explanation fidelity.
9. Continue Connectome C0 in parallel; advance to C1 only against the clean baseline and matched controls.
10. Package reproducible releases with checksums and environment locks.
11. Publish technical notes or a preprint only when claims trace directly to archived evidence.

## Communication principle

AB-GEN should be presented as strongly as the evidence allows, and never more strongly. Historical records, recovered execution, reconstructed pipelines, clean reproduction and independent validation are distinct states and must stay distinct.
