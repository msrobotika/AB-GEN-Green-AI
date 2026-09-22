# AB-GEN Clean Baseline v1 — Final-Test Authorization Gate

The final CIFAR-10 test set is not an interactive tuning dashboard. Clean Baseline v1 therefore uses a two-manifest process:

1. `candidate.manifest.json` — frozen model/config/artifact state, still **not authorized** for final-test execution.
2. `candidate.authorized.manifest.json` — created only after derived machine-readable leakage and batch-invariance gates both pass for the same frozen candidate.

The original frozen candidate manifest is preserved unchanged.

## Gate principle

A hand-written JSON object containing only `"status": "PASS"` is **not sufficient**. Both authorization gates must be derived from source evidence bound to the SHA-256 of the exact frozen candidate manifest. Authorization re-opens and re-hashes the gate source evidence before accepting it.

## Leakage gate source

Prepare a structured leakage-audit JSON containing:
- `protocol_id = abgen-clean-baseline-v1`;
- the exact frozen `candidate_id`;
- `frozen_candidate_manifest_sha256`;
- all required checklist IDs from `LEAKAGE_AUDIT_TEMPLATE.md`;
- `status = PASS` for every required check;
- at least one retained evidence file with SHA-256 for every check.

Required machine-check IDs are:

`D1 D2 D3 D4 P1 P2 F1 F2 N1-1 N1-2 N1-3 N2-1 N2-2 N2-3 A1 A2 C1 C2 E1 E2 E3`

Generate the gate; do not write `leakage_gate.json` manually:

```bash
python -m clean_baseline.gate_evidence leakage \
  --frozen-candidate evidence/candidate/candidate.manifest.json \
  --audit evidence/candidate/structured_leakage_audit.json \
  --out evidence/candidate/leakage_gate.json
```

The generator refuses any missing, `FAIL` or `UNKNOWN` required check and re-hashes every referenced evidence file.

## Batch-invariance gate source

Prepare a structured batch-invariance report bound to the same frozen candidate. It must retain:
- frozen score/logit tolerance;
- maximum observed score/logit drift;
- positive sample/configuration/repeat-pair counts;
- `class_changes = 0`;
- `identical_repeat_class_changes = 0`;
- `hidden_rng_position_dependency_detected = false`;
- all required context families:
  - repeated identical calls;
  - individual inference;
  - multiple batch sizes;
  - multiple batch positions;
  - different companion samples;
- at least one hash-verified evidence file.

Generate the gate:

```bash
python -m clean_baseline.gate_evidence batch-invariance \
  --frozen-candidate evidence/candidate/candidate.manifest.json \
  --report evidence/candidate/batch_invariance_report.json \
  --out evidence/candidate/batch_invariance_gate.json
```

The generator refuses class instability, hidden RNG/position dependence, missing contexts or score drift above the frozen tolerance.

## Authorization command

After the frozen candidate package passes integrity verification:

```bash
python -m clean_baseline.candidate_verify \
  evidence/candidate/candidate.manifest.json
```

and both machine gates have been derived successfully, create the authorized copy:

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
- requires both gates to be bound to the exact SHA-256 of that frozen candidate manifest;
- re-opens and hashes the structured leakage audit, invariance report and their referenced evidence files;
- re-evaluates the required PASS/check/invariance conditions rather than trusting a bare gate status;
- freezes the score tolerance;
- re-checks the split-ledger SHA-256;
- records the exact first authorized evaluation command;
- writes `final_test_authorization.json` with hashes of the source evidence used for authorization;
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
- a machine gate is not bound to the exact frozen candidate manifest;
- structured leakage audit changed after gate generation;
- any required leakage check is missing or not `PASS`;
- referenced leakage evidence changed or disappeared;
- batch-invariance report changed after gate generation;
- class instability is present;
- score/logit drift exceeds the frozen tolerance;
- required invariance contexts are missing;
- hidden RNG/position dependence is detected or not ruled out under the accepted test contract;
- referenced invariance evidence changed or disappeared;
- any final-test access was recorded before authorization.

If model code, config, fitted artifacts, feature order, environment lock or decision logic changes after candidate freeze, create a **new candidate ID and new freeze**. Do not reuse the previous authorization.
