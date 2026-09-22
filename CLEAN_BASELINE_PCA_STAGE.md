# AB-GEN Clean Baseline v1 — audited PCA stage

This document defines the first fitted transformation in the new Clean Baseline v1 RAW→prediction route.

It is **not** a recovery of the unknown historical RAW→PCA transformer and it does not upgrade the historical 80.14% claim. It is a new, explicitly auditable PCA stage for the clean baseline.

## Input boundary

The stage accepts only the explicit normalized RAW representation produced by the Clean Baseline RAW stage:

```text
verified CIFAR RAW uint8 (N, 3072)
  -> stateless float32 / 255
  -> audited PCA
```

The input feature order is frozen as the exact CIFAR Python-batch channel-major order:

```text
R[0..1023], G[0..1023], B[0..1023]
```

The PCA artifact stores and validates the SHA-256 of that feature order.

## Fit authorization

Every PCA fit must declare one of these existing Clean Baseline phases:

- `development_preprocessing_fit`
- `oof_producer_fit`
- `final_preprocessing_refit`

The stage calls the existing fit-scope contracts before `sklearn.decomposition.PCA.fit` is allowed to execute.

### Development

`development_preprocessing_fit` accepts `train_core` only.

Validation, `calibration_reserved` and test samples are rejected by the fit authorization layer.

### OOF

`oof_producer_fit` requires:

- the exact ordered producer IDs;
- the held-out IDs;
- the frozen fold ID.

The PCA fit is rejected if any held-out sample appears in the producer set.

This is the critical anti-leakage rule:

```text
WRONG:
fit PCA once on all 45,000 rows -> split only N1 into OOF folds

REQUIRED:
for every OOF fold:
    fit PCA on that fold's 36,000 producer rows only
    transform that fold's 9,000 held-out rows with that fitted artifact
```

### Final refit

After model choices are frozen, `final_preprocessing_refit` may fit on the allowed `train_core + validation` fit pool. The test split remains forbidden to fitting.

## Explicit PCA configuration

`PCAConfig` freezes all settings that can materially change the transform:

- `n_components`;
- `svd_solver`;
- fit dtype;
- whitening flag;
- randomized seed and randomized-SVD controls when applicable.

Implicit solver selection is deliberately forbidden. `svd_solver="auto"` is rejected.

Supported solvers in this stage:

- `full` — deterministic, requires `random_state=None`;
- `randomized` — requires an explicit integer seed plus explicit power-iteration controls.

Whitening is rejected in this version rather than silently implementing a different numerical contract.

No particular `n_components` value is selected merely by this implementation. The value used by a real candidate must be frozen before the final OOF build under the Clean Baseline protocol.

## Portable fitted artifact

The fitted PCA is not persisted as an opaque sklearn pickle/joblib object.

Instead, AB-GEN writes a deterministic binary artifact containing:

- protocol/schema ID;
- full `PCAConfig`;
- number of fit samples;
- input dimension;
- input/output feature-order hashes;
- complete fit authorization record;
- PCA mean;
- components;
- explained variance;
- explained variance ratio;
- singular values.

Float arrays use a canonical little-endian representation inside the artifact.

The resulting bytes have a stable SHA-256 for the same fitted numerical state and authorization record. Stage receipts bind transforms to that artifact SHA-256 and to the fit-authorization hash.

The artifact format deliberately contains only the mathematical state required for the transform. Inference therefore does not depend on unpickling a particular sklearn estimator class.

## Transform contract

Inference is executed directly as:

```text
(X - mean) @ components.T
```

for the frozen dtype and component order.

For every transform the stage verifies:

- input shape `(N, 3072)`;
- input dtype is float32/float64;
- finite values;
- explicit sample IDs with no duplicates;
- final-test transform authorization through the existing seal;
- artifact dimensions and feature-order hashes;
- finite PCA output.

The output is returned read-only with feature names:

```text
pca_0000, pca_0001, ...
```

and a `StageReceipt` retaining the input/output signatures, fit-authorization hash and PCA artifact SHA-256.

## What this stage does not do

This change does not:

- choose a winning PCA dimensionality from final-test performance;
- fit Fisher weights or class centroids;
- construct the AB-GEN spectral/geometric feature vector;
- fit N1 or N2;
- generate a new final-test accuracy;
- reproduce the unknown historical RAW→PCA transformer;
- alter recovered M4/M5/Elite artifacts.

## Next execution gate

After this PCA stage is accepted, the next fitted stage is:

```text
fold-local PCA output
  -> fold-local Fisher statistics
  -> fold-local class centroids
  -> frozen feature construction
```

Fisher weights and centroids must inherit the same producer/held-out exclusion discipline before N1 and OOF meta-features are implemented.
