# AB-GEN Artifact Manifest Template

Use one completed manifest per reproducible training/evaluation snapshot.

## Identity

- Experiment name:
- Version:
- Date:
- Source commit SHA:
- Release/tag:
- Dataset:
- Split definition:
- Random seed(s):
- Training entry point:
- Evaluation entry point:

## Environment

- OS:
- Python:
- CPU:
- GPU:
- Driver/runtime:
- Dependency lock/requirements file:
- Container image/digest (if used):

## Artifacts

| Artifact | Role | Format | Size | SHA-256 | Produced by | Dataset/split provenance | Required library/version |
|---|---|---|---:|---|---|---|---|
| | | | | | | | |

Typical AB-GEN artifacts may include:

- PCA object/components/mean;
- Fisher weights;
- normalized class centroids;
- N1 ensemble bundle;
- N2 polynomial transformer/scaler/Ridge bundle;
- class mapping;
- preprocessing configuration;
- evaluation predictions/labels;
- confusion matrix and metric report.

## Data-integrity checks

- [ ] PCA fit only on permitted training data.
- [ ] Fisher weights fit only on permitted training data.
- [ ] Centroids constructed only from permitted training data.
- [ ] Final test set excluded from hyperparameter/model selection.
- [ ] N2/meta-learner uses OOF predictions or a clean holdout.
- [ ] Calibration set is separate from final test where calibration is used.
- [ ] Class ordering is identical across training, serialization and inference.

## Evaluation result

- Accuracy:
- Macro F1:
- Per-class metrics file/hash:
- Confusion matrix file/hash:
- Calibration metrics file/hash:
- Number of evaluated samples:
- Repeated-run statistics:

## Benchmark metadata

- Measurement boundary:
- Warm-up:
- Batch size:
- Latency:
- Throughput:
- Energy measurement method:
- Joules/image:
- RAM/VRAM:
- Baseline comparison commit/config:

## Sign-off

- Status: Reported / Reproduced / Validated / External validation
- Evidence reviewed by:
- Known limitations:
- Notes:
