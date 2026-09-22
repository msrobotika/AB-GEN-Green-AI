# AB-GEN Clean Baseline v1 — Work Execution Handoff

This handoff is the execution order for the first leakage-audited AB-GEN RAW→prediction baseline. It is intentionally procedural: Work should follow the gates rather than improvise around them.

## Scope

Allowed:
- verify the frozen RAW source;
- create and verify the split ledger;
- create and verify the deterministic OOF plan;
- implement/fill the clean RAW→preprocessing→PCA→Fisher/centroids→features→N1→N2 route under the frozen fit scopes;
- run development/OOF training using only permitted samples;
- retain stage receipts, fitted artifacts, exact commands, environment and hashes;
- run pre-test leakage and batch-invariance checks;
- freeze a candidate evidence package;
- execute the final test only after the explicit preflight gate passes.

Not allowed:
- tune against final-test labels or final-test accuracy;
- reuse a historical PCA/cache as the Clean Baseline v1 input;
- fit PCA/Fisher/centroids once on all 45k before generating OOF rows;
- use `calibration_reserved` to improve Clean Baseline v1 accuracy;
- inherit hidden batch-position-dependent RNG behavior;
- alter recovered historical originals;
- start Connectome training/architecture experiments as part of this run;
- force a target such as 80.14%, 80.17% or 79.37%.

## Gate 0 — Start from an immutable source commit

Record the exact Git commit before any execution. The commit must include the current Clean Baseline v1 contracts and tests.

Do not modify the protocol after seeing final-test performance. Any later code/config change is a new candidate.

## Gate 1 — Inventory RAW source without deserializing it

For the local extracted CIFAR-10 Python distribution:

```bash
python -m clean_baseline.split_ledger \
  --cifar-python-dir <CIFAR10_PYTHON_DIR> \
  --inventory-only evidence/source_batch_sha256.json
```

Review/freeze `source_batch_sha256.json` before any pickle load. The ledger builder will refuse to deserialize the six Python batch files unless every hash matches this frozen map.

The hash-only inventory is evidence of the actual files supplied to the run. It is not by itself proof of historical AB-GEN provenance.

## Gate 2 — Build the frozen 60,000-row split ledger

```bash
python -m clean_baseline.split_ledger \
  --cifar-python-dir <CIFAR10_PYTHON_DIR> \
  --expected-source-hashes evidence/source_batch_sha256.json \
  --out-dir evidence/splits
```

Required output:
- `split_ledger.csv`
- `split_ledger.manifest.json`

Frozen counts:
- train_core: 40,000
- validation: 5,000
- calibration_reserved: 5,000
- test: 10,000

The official test remains test. Development partitions are derived only from official train, class-balanced, by deterministic `sample_id` ordering. Sample identity is SHA-256 of the exact 3,072 uint8 bytes stored for that image in the verified CIFAR-10 Python batch row.

Do not regenerate a different split after observing performance.

## Gate 3 — Generate and verify the five-fold OOF plan

```bash
python -m clean_baseline.oof_plan generate \
  --ledger evidence/splits/split_ledger.csv \
  --ledger-manifest evidence/splits/split_ledger.manifest.json \
  --out-dir evidence/oof

python -m clean_baseline.oof_plan verify \
  --ledger evidence/splits/split_ledger.csv \
  --plan evidence/oof/oof_plan.json
```

For each fold:
- producer: 36,000 samples;
- held-out: 9,000 samples;
- producer: 3,600 per class;
- held-out: 900 per class.

Across five folds, every one of the 45,000 train_core+validation samples must appear as held-out exactly once.

## Gate 4 — Fold-local preprocessing is mandatory

For every OOF fold, all data-dependent stages producing the held-out meta-features must be fitted only on that fold's producer IDs.

This includes, where applicable:
- normalization/statistics;
- PCA;
- Fisher weights;
- class centroids;
- augmentation/noise statistics;
- feature transforms with fitted state;
- N1 estimators.

The prohibited shortcut is:

```text
fit PCA/Fisher/centroids on all 45,000 → split only N1 into folds
```

That is not clean OOF stacking because each held-out row would already have influenced fitted preprocessing.

Every fit call must pass through the Clean Baseline fit-scope/OOF authorization contracts.

## Gate 5 — Stage receipts

Every material transformation must retain an auditable receipt binding:
- stage name;
- operation and purpose;
- exact ordered sample-ID hash;
- input shape and dtype;
- output shape and dtype;
- feature-order hash where applicable;
- fit-authorization hash for fitted stages;
- fitted-artifact SHA-256 when applicable.

Use the helpers in `clean_baseline.stage_audit`.

If a stage changes sample order, silently drops rows, changes dtype unexpectedly, accesses a forbidden split, or receives final-test samples before authorization, stop the run and preserve the failure.

## Gate 6 — N2 stacking boundary

N2 training rows must come only from OOF predictions/meta-features produced by a pipeline that did not fit on that row.

Before fitting N2, verify:
- exactly 45,000 OOF rows;
- one row per fit-pool sample ID;
- no missing or duplicate IDs;
- each row mapped to its frozen fold;
- every producer/held-out exclusion check passed;
- scaler/polynomial/N2 fitted only on the allowed N2 training data.

Do not use final-test labels to select N2 type, polynomial degree, regularization or ensemble weights.

## Gate 7 — Final refit and batch invariance

After development choices are frozen, final preprocessing/N1 may be refitted on the permitted 45,000 train_core+validation fit pool under the frozen protocol. `calibration_reserved` remains separate for downstream calibration work and is not an accuracy-tuning pool.

Before final-test authorization, run same-sample invariance checks over representative non-test data:
- repeated identical calls;
- individual inference;
- multiple batch sizes;
- multiple positions;
- different companion samples.

Default acceptance:
- exact class invariance to accidental batch context;
- score/logit drift within a documented frozen numerical tolerance;
- no hidden RNG reset/position assignment affecting the same sample's result.

A failure blocks final-test preflight. Do not tune against test to fix it.

## Gate 8 — Leakage audit

Complete `LEAKAGE_AUDIT_TEMPLATE.md` with evidence paths/hashes.

Any material `FAIL` or unresolved material `UNKNOWN` blocks `Reproduced` status and blocks the intended final-test authorization path.

## Gate 9 — Freeze the candidate before final test

Once fitted artifacts, feature order, config and environment are frozen, create the candidate evidence package:

```bash
python -m clean_baseline.candidate_freeze \
  --candidate-id <CANDIDATE_ID> \
  --source-commit <40_CHAR_GIT_SHA> \
  --dataset-source-description "<SOURCE_DESCRIPTION>" \
  --raw-source-sha256 <FROZEN_RAW_SOURCE_SHA256> \
  --ledger evidence/splits/split_ledger.csv \
  --ledger-manifest evidence/splits/split_ledger.manifest.json \
  --oof-plan evidence/oof/oof_plan.json \
  --frozen-config <FROZEN_CONFIG> \
  --environment-lock <ENVIRONMENT_LOCK> \
  --feature-order <FEATURE_ORDER_FILE> \
  --artifact <FITTED_ARTIFACT_1> \
  --artifact <FITTED_ARTIFACT_2> \
  --command "<EXACT_EXECUTION_COMMAND>" \
  --out-dir evidence/candidate
```

Then verify integrity:

```bash
python -m clean_baseline.candidate_verify evidence/candidate/candidate.manifest.json
```

The freeze command deliberately keeps `final_test.sealed = false` in the sense of **not authorized/opened** for evaluation and leaves leakage/batch gates unresolved until their evidence is explicitly recorded. Freezing decisions does not itself authorize final-test access.

## Gate 10 — Final-test preflight

Only after the candidate manifest has:
- complete required hashes;
- decisions frozen;
- pre-test leakage audit = PASS;
- pre-test batch invariance = PASS;
- zero prior final-test access;
- final-test authorization explicitly sealed/opened under the project convention;

run:

```bash
python -m clean_baseline.preflight \
  evidence/candidate/candidate.manifest.json \
  --split-ledger evidence/splits/split_ledger.csv
```

The required output is `PASS`. Any `FAIL` means stop. Do not bypass the preflight in the evaluation runner.

## Gate 11 — Execute final test once the candidate is frozen

Retain:
- full 10,000 predictions with stable sample IDs;
- all class scores/logits with semantics documented;
- exact correct count and denominator;
- accuracy;
- per-class precision/recall/F1;
- macro F1;
- confusion matrix;
- exact command;
- elapsed time and resource metadata as observations, not yet a Green AI benchmark;
- complete stage receipts;
- output hashes.

Do not change the model/config after reading the final result. A different configuration is a new candidate with a new freeze and a disclosed test-access history.

## Gate 12 — Fresh-environment rerun

Before promotion to `Reproduced`, execute the accepted frozen candidate from a fresh environment using the retained lock, source commit, split ledger, config and artifacts. Compare full outputs under the acceptance tolerances.

Only after this gate and all `BASELINE_ACCEPTANCE.md` requirements pass may Clean Baseline v1 be described as `Reproduced`.

## Stop conditions

Stop and preserve evidence if any of the following occurs:
- source hash mismatch;
- split/OOF count mismatch;
- duplicate/missing sample ID;
- forbidden split enters fitting;
- OOF held-out/producer overlap;
- stage row/order mismatch;
- material leakage `FAIL` or unresolved material `UNKNOWN`;
- batch-context class instability;
- candidate artifact/config/environment changes after freeze;
- final-test access before authorization.

A failed run is evidence. Do not erase it and do not tune the final test until a preferred historical number appears.
