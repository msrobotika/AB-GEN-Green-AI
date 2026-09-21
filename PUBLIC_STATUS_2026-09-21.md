# AB-GEN Public Status — 2026-09-21

AB-GEN remains in its reproducibility phase. The project now has executable recovered evidence, but it does **not** yet have a certified clean RAW→prediction CIFAR-10 baseline.

## Current evidence states

- **V24 Slow Burn 80.14%** — `REPORTED` historical project result.
- **Elite / Slow Burn 80.17%** — `RECOVERED` PCA-cache execution; not exact historical reproduction.
- **M5 MASTER 79.55%** — original frozen N1 plus reconstructed polynomial N2; execution completed and saved prediction counts checked.
- **M4 78.05%** — recovered PCA-cache execution matching the recorded project result.

## Demonstrated audit finding

A targeted low-margin audit demonstrated batch-dependent inference in the recovered historical path. The engine resets its RNG on each call and assigns perturbation noise by array shape / batch position. Exact repeated batches are stable, but the same sample can change prediction in a different batch context.

This finding:
- is demonstrated for the targeted subset;
- is not representative evidence for the complete test set;
- does not prove the 80.14% versus 80.17% difference is caused by this mechanism.

## Leakage / provenance status

- Some recovered MASTER preprocessing/class-dependent structures create material train/validation leakage concerns.
- A separate `demo_inferencia.py` route was found to use test labels and is not a valid evaluation route.
- The exact historical RAW→PCA transformer remains unresolved, so PCA test leakage is **not demonstrated but cannot yet be ruled out**.

## Green AI status

Historical energy-efficiency numbers are **not validated benchmark results**. At least one derived million-inference calculation contains a factor-of-1,000 discrepancy. Public diagnostic code no longer calculates/displays those historical constants as if they were measured savings.

A new energy claim requires same-hardware controlled measurement under `GREEN_AI_BENCHMARK_PROTOCOL.md`.

## Immediate priority: Clean Baseline v1

The next performance figure promoted beyond recovery status must come from a new clean pipeline:

RAW data → frozen split → train-only PCA → train-only class-dependent transforms → leakage-safe N1/N2 training → deterministic inference → frozen predictions/hashes/environment.

The final test set must not be used for hyperparameter selection, topology selection, calibration fitting or preprocessing fitting.

## Connectome Edge R&D

Connectome work is a separate hypothesis-driven research track. C0 literature/data/topology mapping may continue, but C1 performance experiments should wait for a clean AB-GEN baseline and must use matched controls.

## Standing evidence rule

A matching or nearby rounded accuracy is not enough to establish reproduction. Where historical sample-level outputs exist, prediction identity is checked sample by sample. Public claims must not exceed the strongest archived evidence state.
