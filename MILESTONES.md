# AB-GEN Milestones

This file tracks public milestones for AB-GEN using an evidence-first standard. A milestone is only promoted here once the supporting result is reproducible or otherwise documented well enough to audit.

## Verified engineering milestones

### 2026-09-20 — Repository audit initiated
- Added a non-destructive technical audit of the public demo.
- Identified reproducibility, calibration, energy-benchmark, deployment, and end-to-end inference gaps.
- Established the rule that reported performance and Green AI claims must be tied to reproducible evidence before being promoted as validated results.

### 2026-09-20 — Session reset defect fixed
- Fixed `/api/reset` so per-class CIFAR-10 statistics retain their fixed array length.
- Added a regression test covering the reset behavior.
- Change merged through PR #3.

## Results currently under validation

### CIFAR-10 — AB-GEN V24 Slow Burn
Internal project documentation records:
- Accuracy: **80.14%**
- Version: **V24 Slow Burn**
- Runtime recorded: **~420 min**

Status: **reported result, pending full reproduction from the original training source and artifacts**.

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
9. model and preprocessing artifact hashes.

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
- Reproduce the 80.14% CIFAR-10 result from clean source.
- Build a complete raw-image inference path.
- Add deterministic tests and CI.
- Create a measured Green AI benchmark suite.
- Add calibration and reliability evaluation.
- Develop class-conditioned AB-GEN attribution maps.
- Package reproducible releases with checksums and environment locks.
- Publish technical notes / preprint once the evidence package is complete.

## Communication principle

AB-GEN should be presented as strongly as the evidence allows, but never more strongly than the evidence supports. Reported results and independently reproduced results are kept clearly distinct.
