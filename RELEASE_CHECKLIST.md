# AB-GEN Release Evidence Checklist

Use this checklist before publishing a release, benchmark result, website claim, paper/preprint figure, or social/visual asset that presents a technical result.

## Technical identity

- [ ] Release/tag points to an immutable commit.
- [ ] Exact training/evaluation entry points are documented.
- [ ] Environment is frozen or reproducibly specified.
- [ ] Random seeds and configuration are recorded.
- [ ] Runtime-required artifacts are listed in a completed artifact manifest.
- [ ] SHA-256 hashes are recorded for critical artifacts.

## Data and leakage

- [ ] Dataset source/version is identified.
- [ ] Split definition is recorded.
- [ ] PCA fit scope is verified.
- [ ] Fisher fit scope is verified.
- [ ] Centroid construction scope is verified.
- [ ] N1 model-selection scope is verified.
- [ ] N2 stacking/OOF or holdout protocol is verified.
- [ ] Final test set was not used for tuning or selection.

## Metrics

- [ ] Aggregate metric is generated from the frozen evaluation run.
- [ ] Per-class metrics are retained.
- [ ] Confusion matrix is retained.
- [ ] Evaluation sample count is reported.
- [ ] Variance/repeated-run information is reported where stochasticity matters.
- [ ] Confidence values are not called calibrated probabilities unless calibration has been evaluated.

## Green AI claims

- [ ] Energy is measured rather than copied from a fixed constant/reference.
- [ ] Hardware is identified.
- [ ] Measurement boundary is identical for compared systems.
- [ ] Warm-up and batch size are documented.
- [ ] Repeated measurements are retained.
- [ ] Joules/image and latency/throughput are reported together.
- [ ] Carbon estimates are separated from measured energy.

## Public communication

- [ ] Claim wording matches evidence status: Reported / Reproduced / Validated / External validation.
- [ ] README, repository metadata, website and visual assets use consistent wording.
- [ ] Historical claims that have not been reproduced are clearly marked as such.
- [ ] Limitations are visible next to the claim, not buried in unrelated documentation.
- [ ] No medical/clinical claim exceeds the available validation evidence.

## Release gate

A release may be called a **Golden Baseline** only when all mandatory reproducibility, data-integrity and evaluation items above are complete.
