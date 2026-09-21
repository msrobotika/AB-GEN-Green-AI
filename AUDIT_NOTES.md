# AB-GEN Technical Audit Notes

Audit state: **2026-09-21**

This file is the current engineering audit summary for the public repository. It distinguishes resolved engineering defects from unresolved scientific/reproducibility risks. It does not certify unpublished training artifacts.

## Current evidence boundary

- **80.14% V24 Slow Burn** — historical project record, `Reported`.
- **80.17% Elite / Slow Burn** — recovered PCA-cache execution, `Recovered`.
- **79.55% M5 MASTER** — original frozen N1 plus reconstructed polynomial N2, executed and count-checked.
- **78.05% M4** — recovered PCA-cache execution matching the recorded result.
- No current CIFAR-10 number is certified as a clean RAW→prediction reproduction.

## Critical unresolved risks

### 1. RAW→PCA provenance is incomplete

The recovered cache contains PCA-projected samples, but the exact historical raw-image preprocessing and PCA transformer are not yet fully recovered and frozen.

Consequences:
- the historical PCA fit scope cannot yet be certified;
- PCA leakage from test data is **not demonstrated**, but it cannot currently be ruled out;
- the public demo is cache-to-prediction diagnostics, not arbitrary raw-image inference.

Required closure evidence:
- raw sample identities;
- exact preprocessing order/dtype/scaling;
- fitted PCA artifact and hash;
- proof of PCA fit scope;
- known RAW→PCA reference vectors.

### 2. Historical class-dependent preprocessing has leakage concerns

Recovered MASTER logic computes some class-dependent structures / augmentation-related state before the final train-validation split. That creates a material leakage concern for that route.

Important scope rule:
- do not automatically attribute the same exact defect or indices to every recovered elite route without independent evidence;
- `demo_inferencia.py` using test labels is a separate invalid route found by code review and must not be conflated with every historical evaluation path.

### 3. Recovered inference is batch-dependent

A targeted audit selected 32 low-margin Ridge cases without labels:
- 18 changed class between full-batch and single-sample inference;
- 17 changed between full-batch and batch-32 inference;
- exact repeated batches produced zero changes.

The recovered engine resets its RNG on each call and assigns perturbation noise according to input array shape and batch position. Therefore the historical recovered path is deterministic for an identical batch but is not invariant to sample batch context.

This does not prove the mechanism explains the historical 80.14% versus recovered 80.17% difference, and the 32-case subset must not be extrapolated to the full test set.

### 4. Historical Green AI headline is not validated

Historical energy numbers are constants / derived calculations, not a controlled same-hardware benchmark. The audit also found a factor-of-1,000 discrepancy in at least one million-inference derived calculation.

Repository policy now treats energy as **unavailable pending controlled measurement**. The public diagnostic API/UI no longer computes a historical savings percentage as if it were a benchmark result.

### 5. Serialized artifacts remain a trusted-code boundary

`joblib` / pickle bundles can execute code during deserialization. Documentation, Docker and launchers already treat runtime artifacts as trusted inputs, but a validated release still needs to verify artifact hashes against an immutable accepted manifest **before** deserialization.

## Resolved engineering defects

- `/api/reset` fixed so class counters retain fixed length.
- session-stat updates protected by a re-entrant lock.
- automated GitHub Actions regression CI established.
- missing Pillow dependency discovered by clean-install CI and added.
- CPU-only PyTorch install path used in CI.
- Docker parent-context copy defect removed.
- public Docker image separated from private runtime artifacts.
- container/runtime artifact preflight added.
- `.gitignore` protects serialized runtime artifacts from accidental commit.
- SHA-256 manifest tooling added and tested.
- sample-level prediction comparator added and tested.
- public probability/confidence language reduced to normalized uncalibrated score semantics.
- diagnostic cached-batch selection changed from random sampling to deterministic stored-order traversal.
- public UI/API no longer exposes unvalidated historical energy savings as live numeric metrics.
- recovered batch-dependent noise behavior is explicitly documented in source and public status.

## Clean Baseline v1 — required next evidence

Historical reconstruction and a clean future baseline are different objectives.

The next defensible performance result must:
1. start from raw CIFAR-10 sample identities;
2. freeze split identities before any fitting;
3. fit PCA on training data only;
4. fit Fisher weights / centroids / augmentation statistics on training data only;
5. create N2 stacking features using a valid OOF or documented holdout procedure;
6. remove hidden batch-context dependence from inference;
7. freeze seeds, environment, dtype, feature ordering and source commit;
8. retain full predictions and per-class metrics;
9. run the final test after model-selection decisions are frozen;
10. pass the leakage template with no unresolved material `FAIL` / `UNKNOWN` items.

A lower clean accuracy must be reported as-is; it is more scientifically useful than an unreproducible higher figure.

## Metadata inconsistency still outside repository-file write surface

The GitHub short “About” description still contains older unconditional 80.14% / 92.6%-energy wording. Issue #11 tracks this because the connected repository-file tools do not expose repository-description mutation. Until changed, the README and `MILESTONES.md` are the authoritative public evidence statements.

## Current priority order

1. Clean public evidence semantics and CI regression guards.
2. Recover exact RAW→PCA provenance.
3. Complete independent leakage audit.
4. Build and execute Clean Baseline v1.
5. Freeze the clean environment and prediction package.
6. Measure energy against controlled baselines on identical hardware.
7. Validate score calibration and explanation fidelity.
8. Keep Connectome Edge R&D at C0 until a clean baseline exists; then advance only through matched controls.
