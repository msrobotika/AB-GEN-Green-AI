# AB-GEN baseline acceptance gates

This document defines what may be claimed during recovery and reproduction of historical AB-GEN results. It exists to prevent a recovered file set, a successful run, or a rounded accuracy match from being mistaken for exact historical reproduction.

## Evidence states

### 1. Reported
A historical result is recorded in notes, logs, spreadsheets, screenshots, or other evidence, but has not yet been independently rerun from a frozen evidence package.

The recorded V24 Slow Burn CIFAR-10 result remains at this level until the gates below are satisfied.

### 2. Recovered
Use `Recovered` only when the candidate source/artifact set has been located and preserved without modifying the originals.

Required evidence:
- original file paths or provenance references retained privately;
- working copies created separately when modification is needed;
- SHA-256 hashes and file sizes recorded;
- timestamps captured where available;
- the producing environment/configuration is recorded when recoverable;
- unresolved ambiguity between competing candidate artifacts is stated explicitly.

Recovery does **not** prove that the artifact set produced the historical metric.

### 3. Pipeline reconstructed
Use `Pipeline reconstructed` only when the end-to-end historical path can be executed from the frozen evidence set with all material transformation stages identified.

For V24 this includes, as applicable:

`raw input -> preprocessing -> PCA -> Fisher weighting -> spectral/geometric features -> N1 -> N2 -> final output`

Required evidence:
- exact preprocessing boundaries;
- fitted transforms identified and frozen;
- feature dimensions documented at stage boundaries;
- N1/N2 artifacts and configuration identified;
- noise/augmentation/inference averaging behavior documented;
- seeds and deterministic/non-deterministic operations recorded;
- no silent substitution of a newly trained component for a historical artifact without explicit labeling.

### 4. Metric reproduced
Use `Metric reproduced` only when a clean evaluation run on the **proven historical evaluation split** matches the historical metric at its documented reporting precision.

Required evidence:
- split provenance is proven;
- evaluation set size is recorded;
- exact number of correct predictions is retained, not only a rounded percentage;
- metric implementation is documented;
- clean-run log and environment are retained;
- leakage audit has no known failure.

A rounded metric match is evidence of metric reproduction only. It is **not** proof that every historical prediction or internal score was reproduced.

### 5. Prediction reproduced
Use `Prediction reproduced` when a clean run can be compared against retained historical sample-level outputs and the predictions agree according to the declared comparison contract.

Required evidence:
- stable `sample_id` values identify the same evaluation examples;
- historical and reproduced outputs are compared independent of row order;
- predicted labels are compared exactly;
- true labels are compared when present in both exports;
- comparable score columns are checked with an explicit numerical tolerance;
- the machine-readable comparison report is retained;
- all mismatches, if any, are documented.

Use `tools/compare_predictions.py` for the repository-standard comparison format.

### 6. Reproduced
Use the project-level claim `Reproduced` only when all applicable gates below pass:

1. source/artifacts are frozen and hashed;
2. dataset/split provenance is established;
3. environment and seeds are recorded;
4. pipeline is reconstructed from the frozen evidence set;
5. leakage audit is complete with no `FAIL` and no unresolved material `UNKNOWN`;
6. clean-run metric evidence is retained;
7. prediction-level comparison is retained when historical prediction outputs exist;
8. artifact manifest and run logs are linked to the evidence package;
9. limitations are stated explicitly.

If historical sample-level outputs no longer exist, prediction-level reproduction may be impossible. In that case the release must state that limitation and must not imply exact prediction equivalence.

## V24 Slow Burn gate

The recorded **80.14% CIFAR-10** value must remain labeled `Reported` until issue #4 is closed with the required evidence package.

A future run that also prints `80.14%` is not sufficient by itself. Before promotion, verify:
- the evaluation split is the same;
- the metric denominator and correct-count are known;
- no test-set feedback affected PCA/Fisher/centroids/N1/N2 selection;
- the N2 stacking protocol is valid;
- historical outputs are compared sample-by-sample when available.

## Failure handling

If a candidate reconstruction fails a gate:
- preserve the result;
- record what failed;
- do not overwrite the historical evidence;
- do not tune against the final test set to force a match;
- classify the candidate at the highest evidence state it actually satisfies.

A failed exact reconstruction can still be scientifically useful, but it must not be relabeled as the historical V24 baseline.
