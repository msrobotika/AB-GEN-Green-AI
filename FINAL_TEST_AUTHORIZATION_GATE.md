# AB-GEN Clean Baseline v1 — Final-Test Authorization Gate

The final CIFAR-10 test set is not an interactive tuning dashboard. Clean Baseline v1 therefore uses a two-manifest process:

1. `candidate.manifest.json` — frozen model/config/artifact state, still **not authorized** for final-test execution.
2. `candidate.authorized.manifest.json` — created only after machine-readable leakage and batch-invariance gates both report `PASS` for the same candidate.

The original frozen candidate manifest is preserved unchanged.

## Required gate evidence JSON

### Leakage gate

```json
{
  "protocol_id": "abgen-clean-baseline-v1",
  "candidate_id": "<CANDIDATE_ID>",
  "status": "PASS"
}
```

The JSON is a machine gate record. The full human-readable leakage audit and its supporting evidence should remain retained alongside it.

### Batch-invariance gate

```json
{
  "protocol_id": "abgen-clean-baseline-v1",
  "candidate_id": "<CANDIDATE_ID>",
  "status": "PASS",
  "frozen_score_tolerance": 1e-8
}
```

The tolerance must be frozen before final-test access. A `PASS` requires class invariance under the accepted same-sample batch-context matrix and score/logit drift within the documented tolerance.

## Authorization command

After the frozen candidate package passes integrity verification:

```bash
python -m clean_baseline.candidate_verify \
  evidence/candidate/candidate.manifest.json
```

create the authorized copy:

```bash
python -m clean_baseline.final_test_authorize \
  --frozen-candidate evidence/candidate/candidate.manifest.json \
  --leakage-gate evidence/candidate/leakage_gate.json \
  --batch-invariance-gate evidence/candidate/batch_invariance_gate.json \
  --split-ledger evidence/splits/split_ledger.csv \
  --first-authorized-command "python <FINAL_EVALUATOR> --manifest evidence/candidate/candidate.authorized.manifest.json" \
  --out evidence/candidate/candidate.authorized.manifest.json
```

This command:
- re-verifies the complete frozen candidate evidence package;
- requires both gate files to refer to the same candidate and report `PASS`;
- freezes the score tolerance;
- re-checks the split-ledger SHA-256;
- records the exact first authorized evaluation command;
- writes `final_test_authorization.json` with hashes of the evidence used for authorization;
- produces a new authorized manifest rather than overwriting the frozen pretest manifest.

## Independent preflight

The authorized manifest must then pass the existing independent preflight:

```bash
python -m clean_baseline.preflight \
  evidence/candidate/candidate.authorized.manifest.json \
  --split-ledger evidence/splits/split_ledger.csv
```

Required result:

```text
PASS: Clean Baseline v1 candidate is sealed for final-test evaluation.
```

Only then may the exact `first_authorized_command` be executed.

## Invalid authorization conditions

Authorization must fail if any of the following is true:
- frozen candidate evidence has been modified;
- fitted artifact hash or size changed;
- split ledger changed;
- candidate/source commit identity changed;
- leakage gate is not `PASS`;
- batch-invariance gate is not `PASS`;
- either gate refers to a different candidate;
- batch score tolerance is missing or invalid;
- any final-test access was recorded before authorization.

If model code, config, fitted artifacts, feature order, environment lock or decision logic changes after candidate freeze, create a **new candidate ID and new freeze**. Do not reuse the previous authorization.
