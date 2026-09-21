# AB-GEN Release Evidence Checklist

Use this checklist before publishing a release, benchmark result, website claim, paper/preprint figure or social/visual asset that presents a technical result.

## Technical identity

- [ ] Release/tag points to an immutable commit.
- [ ] Exact training and evaluation entry points are documented.
- [ ] Environment is frozen or reproducibly specified.
- [ ] Random seeds and deterministic settings are recorded.
- [ ] Dtypes, device mode and feature ordering are recorded where they can affect outputs.
- [ ] Runtime-required artifacts are listed in a completed artifact manifest.
- [ ] SHA-256 hashes are recorded for critical source/preprocessing/model artifacts.
- [ ] Full prediction output is retained when practical.

## Data and leakage

- [ ] Dataset source/version is identified.
- [ ] Stable sample identities are retained.
- [ ] Split definition is frozen before data-dependent fitting.
- [ ] PCA fit scope is verified as train-only for a clean baseline.
- [ ] Fisher fit scope is verified as train-only.
- [ ] Centroid construction scope is verified as train-only.
- [ ] Augmentation/noise statistics are verified as train-only.
- [ ] N1 model-selection scope is verified.
- [ ] N2 stacking uses documented leakage-safe OOF or holdout logic.
- [ ] Calibration fitting does not use final-test labels.
- [ ] Final test set was not used for tuning, topology selection or model selection.
- [ ] `LEAKAGE_AUDIT_TEMPLATE.md` has no unresolved material `FAIL` or `UNKNOWN` for a reproduced/validated claim.

## Determinism and inference integrity

- [ ] Same sample produces the same prediction on repeated identical calls.
- [ ] Sample prediction/logits are tested across batch sizes.
- [ ] Sample prediction/logits are tested across positions within a batch.
- [ ] Sample prediction/logits are tested with different companion samples.
- [ ] Any context-dependent inference mechanism is explicit, intended and documented.
- [ ] No hidden batch-position-dependent random perturbation exists in a clean baseline.
- [ ] CPU/GPU numerical tolerances are documented if both are supported.

## Metrics

- [ ] Aggregate metric is generated from the frozen evaluation run.
- [ ] Correct count and denominator are retained, not only rounded accuracy.
- [ ] Per-class metrics are retained.
- [ ] Confusion matrix is retained.
- [ ] Evaluation sample count is reported.
- [ ] Variance/repeated-run information is reported where stochasticity matters.
- [ ] Decision scores are not called calibrated probabilities unless calibration has been evaluated.
- [ ] Historical/recovered/reconstructed numbers are not merged into a clean reproduced result.

## Green AI claims

- [ ] Energy is measured rather than copied from a fixed constant/reference.
- [ ] Hardware, OS, drivers and measurement tool are identified.
- [ ] Measurement boundary is identical for compared systems.
- [ ] Model-only and end-to-end boundaries are separated.
- [ ] Warm-up and batch size are documented.
- [ ] Repeated measurements and uncertainty are retained.
- [ ] Joules/image and latency/throughput are reported together.
- [ ] RAM/VRAM and artifact size are recorded where relevant.
- [ ] Compared baselines use equivalent accuracy/evaluation conditions.
- [ ] Carbon estimates are separated from measured energy.

## Public communication

- [ ] Claim wording matches the exact evidence state: Reported / Recovered / Reconstructed / Reproduced / Validated / Independently validated.
- [ ] README, `MILESTONES.md`, repository short description, website and visual assets use consistent wording.
- [ ] Historical claims that have not been reproduced are clearly marked next to the number.
- [ ] Limitations are visible next to the claim, not buried in unrelated documentation.
- [ ] No energy-savings percentage is published before the controlled benchmark gate passes.
- [ ] No probability/calibration claim exceeds measured calibration evidence.
- [ ] No medical/clinical claim exceeds the available validation evidence.
- [ ] Connectome-inspired work is described as a hypothesis until matched controls establish a result.

## Release gate

A release may be called a **Golden Baseline** only when all mandatory reproducibility, data-integrity, determinism and evaluation items above are complete.

A recovered historical bundle may be released as archival/recovery evidence, but it must not be labeled a Golden Baseline unless it independently satisfies the clean release gate.
