# AB-GEN Public Status — 2026-09-21

AB-GEN remains in its reproducibility phase.

## What changed
- Baseline acceptance states are now formally defined.
- A mandatory leakage-audit checklist is in place.
- Prediction-level comparison tooling is available for recovered historical outputs.
- A controlled Green AI benchmark protocol is now documented.

## What has not changed
- CIFAR-10 V24 Slow Burn **80.14% remains a reported historical result**, pending full reproduction from frozen source/artifacts.
- Historical energy-saving figures remain **unvalidated** until AB-GEN and selected baselines are measured on the same hardware under the controlled protocol.

## Current recovery focus
The private recovery work is focused on identifying and proving the exact historical N1/N2 path and resolving M4/M5 probability/noise behavior before any public evidence state is upgraded.

## Evidence rule
A matching rounded accuracy is not enough to establish exact historical reproduction. Where historical sample-level outputs exist, prediction agreement will be checked sample by sample.
