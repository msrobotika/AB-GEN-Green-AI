# AB-GEN Technical Audit Notes

Audit date: 2026-09-20

This file records non-destructive engineering findings from review of the public demo repository. It does not validate the unpublished training pipeline or model artifacts.

## Critical / High priority

1. **Reset endpoint corrupts list-shaped counters**
   - `session_stats` contains `class_correct` and `class_total` as fixed-length lists of 10 elements.
   - `/api/reset` calls `.clear()` on every list, shrinking these two arrays to length 0.
   - The next `/api/analyze` attempts `class_total[c] += 1` and can raise `IndexError`.
   - Fix: reset fixed-length arrays to `[0] * 10`; only clear `history_acc`.

2. **Docker build is not reproducible from repository root**
   - `Dockerfile` contains `COPY ../AB-GEN_80_Accuracy.py /AB-GEN_80_Accuracy.py`.
   - Docker cannot normally copy files outside the build context when running `docker build .`.
   - The public repository also omits the training script/model bundle required by this path.

3. **Public demo is not end-to-end image inference**
   - `/api/analyze` samples precomputed `sample_data["x_pca"]` vectors.
   - The demo therefore validates PCA-vector-to-class inference, not arbitrary raw-image-to-class inference.
   - Add a deterministic raw RGB preprocessing/PCA transform path and an upload endpoint for independent samples.

4. **Energy figures are constants, not runtime measurements**
   - `J_PER_INFERENCE` and the ResNet baseline are hard-coded.
   - Dashboard savings are derived from those constants.
   - Reproducible Green AI claims need a benchmark protocol: hardware, software versions, batch size, warm-up, repeated runs, wall time, power sampling, and joules/inference.

5. **Softmax over Ridge decision scores is not probability calibration**
   - The current implementation converts `decision_function` scores to a simplex using softmax.
   - Treat these as normalized confidence scores unless calibration is evaluated.
   - Add ECE, Brier score and reliability diagrams; use temperature/Platt/isotonic calibration where appropriate.

## Reproducibility / engineering

- Dependencies use open-ended `>=` constraints; add a lockfile or exact tested environment.
- No public test suite or GitHub Actions workflow is present.
- `ACCURACY_TARGET = 80.0` is a configured display value, not a runtime evaluation result.
- In-memory session statistics are shared mutable global state and are not thread-safe under a multi-threaded WSGI server.
- Joblib/pickle model loading should only consume trusted artifacts and should be documented as such.

## Next validation step

The unpublished training source and artifacts are required to audit:

- train/validation/test separation and leakage risk;
- PCA fit scope;
- Fisher weighting fit scope;
- centroid construction;
- N1 training and model selection;
- N2 stacking protocol / out-of-fold generation;
- reported CIFAR-10 accuracy;
- energy benchmark methodology.
