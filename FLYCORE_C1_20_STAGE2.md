# FlyCore C1.20P — Stage2 builder forensics closure

## Status

**C1.20P Stage2: CLOSED PASS — READ-ONLY FORENSICS**

No topology generation, training, dataset forward execution, FLE calculation, damage evaluation, performance execution, or project-code execution occurred.

## Parent freeze

- C1.20P Stage1 freeze SHA-256: `34f0cad1caca4e0032b5b2a40d098fc06b7e3742072188d43820aa6f7c5ce70b`

## Verified Stage2 result

- targets inspected: **7**
- evidence lines extracted: **525**
- strong structural evidence lines: **82**
- Python function/class declarations: **70**
- Stage2 freeze SHA-256: `672e96b10573e2b1b7dae50fc722f49b252b5339a0a67c257c72ce8059cf62d0`
- training: **NONE**
- performance: **NONE**
- topology generation: **NONE**
- project-code execution: **NONE**

The generated verify-only procedure returned PASS with the same Stage2 freeze SHA-256.

## Builder-identity finding

Stage2 does **not** support promoting either inspected runner as the exact historical structural-pair builder.

### c1_18a_runner.py

The source loads an already frozen pair snapshot:

`pairs = load_json(PREFLIGHT / "selected_pairs_snapshot.json")`

It then verifies topology hashes, reconstructs variants, runs functional importance/damage evaluation, fits/predicts B0/B1 and analyzes outcomes. This is an execution/analysis runner consuming a previously selected bank, not evidence that it generated the original candidate bank and pairing itself.

### c1_19r_recovery_runner.py

The recovery source contains the base FlyCore topology construction primitives, including:

- `build_flycore_c0_topology`
- edge/mask conversion
- degree/role/macro structural helpers
- `reconstruct_variants`

But its input path also loads an already recovered pair manifest:

`pairs = load_json(PACKAGE/"selected_pairs_recovered.json")`

Therefore it is the strongest recovered implementation for reconstructing the selected variants and enforcing their hashes, but Stage2 does not show that this file itself performed the original 400-candidate eligibility/pairing selection.

## Recovered structural evidence

`recovery_evidence.json` records the C1.18 confirmation recovery as:

- candidate count: **400**
- eligible-pair count: **91**
- selected pairs: **16**
- status: **EXACT COUNTS / SEEDS / DELTA_RDE MATCH HISTORICAL RECORD**

`selected_pairs_recovered.json` contains the recovered pair-level delta-RDE values and topology SHA-256 bindings.

This is strong evidence that the recovery process reproduced the historical selected bank, but the exact source file that generated/scored/paired the 400 candidates remains to be located or explicitly reconstructed from frozen evidence.

## Decision

Do not call `c1_18a_runner.py` or `c1_19r_recovery_runner.py` the exact historical structural-bank builder.

For C1.20, the next gate is a deeper source/archive provenance search for the code that implements:

1. candidate topology generation;
2. structural eligibility;
3. LOW/HIGH pairing;
4. delta-RDE threshold/order;
5. fixed-range selection;
6. selection of the 16 confirmation pairs.

If no exact historical source survives, the project must explicitly classify the C1.20 structural builder as a **recovered/reconstructed implementation validated against frozen C1.18 invariants**, not as the exact historical source.
