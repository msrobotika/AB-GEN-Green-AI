# AB-GEN Public Status — latest update 2026-09-22

AB-GEN remains in its reproducibility phase. The project has executable recovered evidence and stronger internal verification, but it does **not** yet have a certified clean RAW→prediction historical CIFAR-10 baseline.

## Current evidence states

- **V24 Slow Burn 80.14%** — `REPORTED` historical project result.
- **Elite / Slow Burn 80.17%** — `RECOVERED` PCA-cache execution; not exact historical reproduction.
- **M5 MASTER 79.55%** — original frozen N1 plus reconstructed polynomial N2; `RECONSTRUCTED / EXECUTED`.
- **M4 78.05%** — `RECOVERED` PCA-cache execution matching the recorded M4 result.
- **V24 rescued linear N2 79.37%** — historical documentary screenshot evidence; exact checkpoint/script unresolved.

## What the latest audit adds

### RAW duplicate check

The verified official CIFAR-10 source contains **60,000 byte-distinct images**: 50,000 train and 10,000 test. No exact duplicate image was found within or across those partitions.

This does **not** prove the recovered PCA cache came from the exact RAW samples through the missing historical transformer, and it does not rule out perceptual similarity or fitted-transform leakage.

### Prediction and score evidence

- **30,000 preserved prediction rows** now have stable IDs derived from hashes of official RAW image bytes.
- Frozen M4 and M5 MASTER consistency reruns match the preserved recovery predictions **20,000 / 20,000**.
- Elite score extraction matches the preserved recovery predictions **10,000 / 10,000**.
- The evidence package now contains **300,000 class scores** across M4, M5 MASTER and Elite.
- M4 softmax outputs are not calibration-certified probabilities.
- M5 MASTER and Elite Ridge `decision_function` values are not probabilities.
- A standalone verifier passes the full 30,000-row / 300,000-score package and rejects three deliberately corrupted copies.

These checks strengthen internal consistency. They do **not** reproduce the missing historical 80.14% or 79.37% output sets and do not constitute external validation.

### Route-level disagreement

The preserved routes differ on many more samples than their net accuracy gaps imply:
- M4 → M5 MASTER: **957 different predictions**, net **+150** correct.
- M4 → Elite: **1,413 different predictions**, net **+212** correct.
- M5 MASTER → Elite: **1,131 different predictions**, net **+62** correct.

These are descriptive comparisons, not causal ablations.

## Demonstrated batch-dependence finding

The expanded targeted audit uses the same 32 low-margin Ridge cases selected without labels and evaluates 1/2/4/8/16/32/64 batch sizes, multiple positions and two companion groups:

- **1,120 configurations / 2,240 executions**;
- **344 class changes** relative to individual inference, affecting 31 of 32 targeted cases;
- **0 class changes** with fixed noise;
- **0 class changes** with noise removed;
- **0 differences** between identical repeated calls;
- transferring batch-assigned noise to individual inference reproduces the batch class in **1,120 / 1,120** configurations;
- changing only companion samples produces **0 changes in 544 paired comparisons**.

The recovered engine resets its RNG on each call and assigns perturbation noise by input shape/position. The interventions establish that mechanism as the cause of the tested class changes.

This finding is still deliberately bounded: it does not quantify prevalence over the whole test set and does not prove the historical 80.14% versus recovered 80.17% difference was caused by this mechanism.

## Leakage / provenance status

- Some recovered MASTER class-dependent preprocessing/augmentation state creates material train/validation dependence concerns for that reconstructed route.
- A separate `demo_inferencia.py` route uses test labels to fit N2 and is not a valid evaluation route for generalization on that same test set.
- The exact historical RAW→PCA transformer remains unresolved, so PCA test leakage is **not demonstrated but cannot be ruled out**.
- Binary inspection of the Elite bundle exposes `_sklearn_version = 1.8.0` as a serialization marker only; the complete historical training environment is not established.
- Historical M4 screenshots support Python 3.13.7 / GTX 1050 Ti for that M4 context only, not automatically for Elite.

## XAI status

The historical medical heatmap generator accesses PCA/Fisher state but not N1/N2 classifier output or a target class. Current evidence supports a **weighted PCA reconstruction/visualization**, not demonstrated faithful attribution of the classifier decision and not clinical validation.

## Green AI status

Historical energy-efficiency numbers are **not validated benchmark results**. Corrected arithmetic from the recorded constants is still only arithmetic from assumed constants, not a same-hardware measurement.

A new energy claim requires controlled measurement under `GREEN_AI_BENCHMARK_PROTOCOL.md` using the same hardware and evaluation boundary for AB-GEN and baselines.

## Immediate priority: Clean Baseline v1

The next performance figure promoted beyond recovery/reconstruction status must come from a clean pipeline:

RAW data → frozen split → train-only PCA → train-only class-dependent transforms → leakage-safe N1/N2 training → deterministic inference → frozen predictions/scores/hashes/environment → clean-environment rerun.

The final test set must not be used for hyperparameter selection, topology selection, calibration fitting or preprocessing fitting.

## Connectome Edge R&D

Connectome remains a separate future/documentary research track. No Connectome training or performance result is part of the current evidence base.

## Standing evidence rule

A matching or nearby rounded accuracy is not enough to establish historical reproduction. Internal consistency, historical provenance, clean reproduction and external validation are separate evidence levels. Public claims must not exceed the strongest archived evidence state.
