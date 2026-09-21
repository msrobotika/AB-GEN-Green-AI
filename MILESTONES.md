# AB-GEN Milestones

This file tracks public milestones for AB-GEN using an evidence-first standard. A milestone is only promoted here once the supporting result is reproducible or otherwise documented well enough to audit.

## Verified engineering milestones

### 2026-09-21 — Recovery audit produced executable evidence
- Recovered **M4** evaluation from the PCA-cache path at **7,805 / 10,000 = 78.05%**, matching the documented project result.
- Completed **M5 MASTER** evaluation with the original frozen N1 and reconstructed polynomial N2 at **7,955 / 10,000 = 79.55%**; saved prediction counts were checked.
- Evaluated the recovered **Elite / Slow Burn** bundle from cache at **8,017 / 10,000 = 80.17%**.
- The historical **80.14% V24 Slow Burn** headline remains **REPORTED** because the exact historical RAW→PCA transformer, split, script and prediction lineage have not yet been recovered end to end.
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
- Merged through PR #27.
- This milestone establishes the protocol only; it does **not** validate historical energy-saving figures.

### 2026-09-20 — Repository audit initiated
- Added a non-destructive technical audit of the public demo.
- Identified reproducibility, calibration, energy-benchmark, deployment, and end-to-end inference gaps.
- Established the rule that reported performance and Green AI claims must be tied to reproducible evidence before being promoted as validated results.

### 2026-09-20 — Session reset defect fixed
- Fixed `/api/reset` so per-class CIFAR-10 statistics retain their fixed array length.
- Added a regression test covering the reset behavior.
- Change merged through PR #3.

### 2026-09-20 — Automated regression CI established
- Added GitHub Actions regression CI for pushes and pull requests to `main`.
- Corrected the missing Pillow dependency discovered by clean-install validation.
- Moved CI to CPU-only PyTorch wheels to avoid unnecessary CUDA downloads during CPU regression testing.
- CI is now used as a merge gate for repository hardening work.

### 2026-09-20 — Public research portal launched
- Published the official **MS Robotika — AB-GEN Research** site.
- Added public pages for architecture, research methodology, milestones/benchmarks and project background.
- Published the first technical note: **“AB-GEN enters its reproducibility phase.”**
- Public site: https://msrobotikaabgenresearch.wordpress.com/

### 2026-09-20 — Public demo evidence semantics hardened
- Separated live session measurements from reported V24 accuracy and historical energy references.
- Renamed probability/confidence presentation to normalized decision-score terminology pending calibration.
- Added explicit evidence-status metadata to the API while preserving temporary compatibility aliases.
- Added regression coverage for public wording and API evidence semantics.

### 2026-09-20 — Runtime and serialized-artifact security boundary established
- Added `SECURITY.md` warning that pickle/joblib model bundles are trusted-code artifacts and must never be loaded from unverifiable sources.
- Windows launchers now fail safely when required runtime artifacts are absent rather than guessing private parent-folder layouts.
- Docker no longer copies private artifacts or files outside the build context.
- The public Docker image contains application code only; runtime model/data/compatibility artifacts are mounted read-only.
- Added `.gitignore` protection for private runtime artifacts and tests covering deployment preflight behavior.

### 2026-09-20 — Artifact manifest integrity tooling added
- Added `tools/artifact_manifest.py` to create and verify SHA-256 manifests for recovered/runtime-critical files.
- The manifest records filenames, byte sizes, hashes and environment/source metadata without publishing absolute workstation paths.
- Added tests for round-trip verification, tamper detection and duplicate-label rejection.
- Integrated the tooling into the reproducibility protocol so recovered V24 artifacts can be frozen before modification.

## Results currently under validation

### CIFAR-10 — AB-GEN V24 Slow Burn
Internal project documentation records:
- Accuracy: **80.14%**
- Version: **V24 Slow Burn**
- Runtime recorded: **~420 min**

Status: **REPORTED historical result, pending exact reproduction from the original RAW→PCA→model path**.

A recovered Elite / Slow Burn bundle currently evaluates to **80.17%** from the PCA-cache path. That result is deliberately kept separate from the historical 80.14% claim until the exact historical transformer, split, script and prediction-level lineage are recovered.

A rounded or nearby metric match by itself will not be treated as exact historical reproduction. The project distinguishes artifact recovery, pipeline reconstruction, metric reproduction and prediction-level reproduction where historical outputs are available.

### CIFAR-10 — M5 MASTER reconstructed path
- Accuracy: **79.55%**
- Count: **7,955 / 10,000**
- Configuration: original N1 frozen, polynomial N2 reconstructed from recovered project evidence.

Status: **reconstructed and executed; not equivalent to exact historical V24 reproduction**.

### CIFAR-10 — V23 M4 Purist
Internal project documentation records:
- Accuracy: **78.05%**
- Runtime recorded: **481.5 min**

Current recovery status: **78.05% matched from the recovered PCA-cache inference path**. Full raw-image training reproduction remains pending.

### MNIST — Universal V24
Internal project documentation records:
- Accuracy: **97.79%**

Status: **reported result, pending reproduction**.

## Current audit risks and open questions

- **RAW→PCA provenance:** the cache exists, but the exact historical transformer and preprocessing lineage are not yet fully recovered.
- **Leakage:** historical MASTER code computes some class-dependent structures / augmentation logic before the final train-validation split. This requires independent audit; the same indices or defect must not be attributed automatically to every elite route.
- **Batch dependence:** demonstrated on a targeted low-margin subset and traced to per-call RNG/noise assignment. Scope and impact on the complete test set remain unproven.
- **Historical 80.14% identity:** exact V24 script, split and prediction lineage remain unresolved.
- **Energy:** historical energy figures remain unvalidated; controlled measurement is still required, and at least one million-inference savings calculation was found to contain a factor-of-1,000 discrepancy.
- **XAI:** geometric/PCA visualisation alone is not evidence of faithful explanation. Attribution fidelity must be tested against the actual decision path.

## Validation gates for future public claims

A performance milestone should normally include:
1. exact dataset and split;
2. source/version tag or commit;
3. random seed(s);
4. train/validation/test separation;
5. leakage checks;
6. per-class metrics where relevant;
7. repeated-run statistics where practical;
8. exact dependency environment;
9. model and preprocessing artifact hashes;
10. prediction-level comparison when historical sample outputs exist.

A Green AI milestone should additionally include:
1. exact hardware and OS;
2. model-only and end-to-end measurements separated;
3. warm-up protocol;
4. batch size and throughput;
5. repeated power/energy measurements;
6. joules per inference;
7. baseline measured under the same boundary and hardware;
8. carbon conversion methodology stated separately from measured energy.

A Medical/XAI milestone should additionally include:
1. class-wise sensitivity/specificity and macro metrics;
2. calibration metrics such as ECE, Brier score and NLL;
3. external or independent validation when making clinically relevant claims;
4. explanation method tied to the actual predicted class and decision path.

## Roadmap

- Recover the exact RAW→PCA transformer, preprocessing lineage and environment.
- Link the historical V24 Slow Burn 80.14% script, split, model artifacts and predictions to the recovered elite bundle.
- Freeze originals and preserve SHA-256 provenance without modifying recovered source artifacts.
- Complete the formal independent leakage audit.
- Characterize batch sensitivity across batch size, sample position, batch composition and repeated deterministic runs.
- Reproduce the exact historical 80.14% CIFAR-10 result from clean source and classify the evidence state precisely.
- Freeze the dependency environment for the reproduced baseline.
- Build a complete raw-image inference path.
- Expand deterministic tests and CI to model/preprocessing fixtures and container smoke tests.
- Execute the controlled Green AI benchmark suite.
- Add calibration and reliability evaluation.
- Validate explanation fidelity and develop class-conditioned AB-GEN attribution maps.
- Keep future sparse/modular/bio-inspired Edge-AI research isolated from the historical baseline until the recovery audit is closed.
- Package reproducible releases with checksums and environment locks.
- Publish technical notes / preprint once the evidence package is complete.

## Communication principle

AB-GEN should be presented as strongly as the evidence allows, but never more strongly than the evidence supports. Reported results and independently reproduced results are kept clearly distinct.
