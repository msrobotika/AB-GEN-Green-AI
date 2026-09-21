# AB-GEN Milestones

This file tracks public milestones for AB-GEN using an evidence-first standard. A milestone is only promoted here once the supporting result is reproducible or otherwise documented well enough to audit.

## Verified engineering milestones

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

Status: **reported result, pending full reproduction from the original training source and artifacts**.

A rounded 80.14% match by itself will not be treated as exact historical reproduction. The project now distinguishes artifact recovery, pipeline reconstruction, metric reproduction and prediction-level reproduction where historical outputs are available.

### CIFAR-10 — V23 M4 Purist
Internal project documentation records:
- Accuracy: **78.05%**
- Runtime recorded: **481.5 min**

Status: **reported result, pending reproduction**.

### MNIST — Universal V24
Internal project documentation records:
- Accuracy: **97.79%**

Status: **reported result, pending reproduction**.

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

- Recover and freeze V24 Slow Burn as the golden baseline.
- Generate the first immutable V24 artifact manifest and preserve the originals unchanged.
- Resolve the historical N1/N2 path and M4/M5 probability/noise behavior.
- Complete the formal leakage audit.
- Reproduce the 80.14% CIFAR-10 result from clean source and classify the evidence state precisely.
- Freeze the dependency environment for the reproduced baseline.
- Build a complete raw-image inference path.
- Expand deterministic tests and CI to model/preprocessing fixtures and container smoke tests.
- Execute the controlled Green AI benchmark suite.
- Add calibration and reliability evaluation.
- Develop class-conditioned AB-GEN attribution maps.
- Package reproducible releases with checksums and environment locks.
- Publish technical notes / preprint once the evidence package is complete.

## Communication principle

AB-GEN should be presented as strongly as the evidence allows, but never more strongly than the evidence supports. Reported results and independently reproduced results are kept clearly distinct.
