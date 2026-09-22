# AB-GEN Technical Audit Notes

Audit state: **2026-09-22**

This file is the current engineering audit summary for the public repository. It distinguishes resolved engineering defects from unresolved scientific/reproducibility risks. It does not certify unpublished training artifacts or upgrade historical results beyond the formal acceptance gates.

## Current evidence boundary

- **80.14% V24 Slow Burn** — historical project record, `Reported`.
- **80.17% Elite / Slow Burn** — recovered PCA-cache execution, `Recovered`.
- **79.55% M5 MASTER** — original frozen N1 plus reconstructed polynomial N2, `Reconstructed / executed`.
- **78.05% M4** — recovered PCA-cache execution, `Recovered`.
- **79.37% V24 rescued linear N2** — historical documentary evidence from screenshot; exact checkpoint/script not identified.
- No current CIFAR-10 number is certified as a clean RAW→prediction historical reproduction.

## Newly demonstrated continuity evidence

### RAW duplicate audit

The verified official CIFAR-10 source contains 60,000 byte-distinct images:
- 50,000 train;
- 10,000 test;
- zero exact duplicate image bytes within train;
- zero exact duplicate image bytes within test;
- zero exact duplicate image bytes across train/test.

The archive hash remained unchanged before and after inspection.

This narrows one leakage hypothesis only. It does **not** rule out perceptual-near duplicates, augmentation dependence, fitted-transform leakage, label leakage or an incorrect cache→RAW association.

### Preserved prediction exports

Three 10,000-row recovered prediction sets now use stable `sample_id` values derived from SHA-256 of the official RAW image bytes. Source row counts and hashes remain intact.

The mapping still inherits the declared cache/test index association. Therefore these IDs provide a stable comparison key but do **not** independently prove that the recovered PCA cache was generated from those exact RAW samples by the missing historical producer.

### Score extraction and frozen consistency checks

- M4 frozen inference matched preserved predicted classes **10,000 / 10,000**, retaining **7,805 / 10,000** correct.
- M5 MASTER frozen inference matched preserved predicted classes **10,000 / 10,000**, retaining **7,955 / 10,000** correct.
- Elite N2 score extraction matched preserved predicted classes **10,000 / 10,000**, retaining **8,017 / 10,000** correct.
- The current package contains **300,000 class scores** over 30,000 evaluated rows.

Score semantics differ by route:
- M4: recovered N2 softmax outputs; calibration unverified;
- M5 MASTER: Ridge `decision_function`; not probabilities;
- Elite: Ridge `decision_function`; not probabilities.

The M4/M5 reruns use copied checkpoints and extracted historical function snapshots and preserve the tested batch composition/noise behavior. These are exact consistency checks against preserved **recovery outputs**, not identification of the missing historical 80.14% or 79.37% prediction sets.

A standalone standard-library verifier passes all 30,000 rows / 300,000 scores, validates hashes/IDs/labels/argmax/metrics, and rejects three deliberately corrupted copies. This is strong internal package verification, but **not external validation** and not historical provenance proof.

### Sample-level disagreement between recovered routes

| A → B | Both correct | B corrects A | B loses A correct | Both wrong | Different predictions | Net correct |
|---|---:|---:|---:|---:|---:|---:|
| M4 → M5 MASTER | 7,536 | 419 | 269 | 1,776 | 957 | +150 |
| M4 → Elite | 7,389 | 628 | 416 | 1,567 | 1,413 | +212 |
| M5 MASTER → Elite | 7,572 | 445 | 383 | 1,600 | 1,131 | +62 |

For M5 MASTER → Elite, 303 rows change predicted class while both routes remain wrong. The +62 net gain therefore does not mean only 62 predictions changed. The same distinction between net accuracy and behavioral disagreement applies to the other pairs.

These comparisons are descriptive only. The routes differ in more than one component, so they are not causal ablations.

## Critical unresolved risks

### 1. RAW→PCA provenance is incomplete

The recovered cache contains PCA-projected samples, but the exact historical raw-image preprocessing and fitted PCA transformer remain unresolved.

Consequences:
- historical PCA fit scope cannot be certified;
- PCA leakage from test data is **not demonstrated**, but cannot be ruled out;
- cache→RAW identity is not independently certified;
- the public demo remains cache-to-prediction diagnostics, not arbitrary raw-image inference.

Required closure evidence includes the exact preprocessing order/dtype/scaling, fitted PCA artifact/hash, fit scope and known RAW→PCA reference vectors.

### 2. Historical class-dependent preprocessing has leakage concerns

Recovered MASTER logic creates some class-dependent structures / augmentation-related state before its final train-validation split. This creates material train/validation dependence for that reconstructed route.

Scope rule:
- do not automatically attribute the same exact indices, split identity or defect to Elite without evidence;
- `demo_inferencia.py` using test labels to fit N2 is a separate invalid route found by code review and is not evidence about every historical route.

### 3. Recovered inference is batch-dependent

The expanded targeted audit uses the same 32 low-margin Ridge cases selected without labels and evaluates batch sizes 1/2/4/8/16/32/64, multiple positions and two companion groups.

Results:
- **1,120 configurations / 2,240 executions**;
- **344 class changes** relative to individual inference, affecting 31 of 32 targeted cases;
- **0 class changes** with fixed noise;
- **0 class changes** with noise removed;
- **0 differences** between exact repeated calls;
- batch-assigned noise transferred to individual inference reproduces the batch class in **1,120 / 1,120** configurations;
- changing only companion samples causes **0 changes in 544 paired comparisons**;
- 35 checks matched the public engine exactly.

The recovered engine resets its RNG per call and assigns perturbation noise according to input shape and position. The interventions establish this noise assignment as the cause of the tested class changes.

This does **not** quantify frequency over the full CIFAR-10 test set, does not resolve CPU/GPU equivalence and does not prove the 80.14% versus 80.17% historical difference was caused by this mechanism.

### 4. Historical Green AI headline is not validated

Historical energy values are constants / derived calculations, not same-hardware measurements. Corrected arithmetic from the recorded constants gives approximately **0.001080555 kWh per one million inferences** for the derived saving calculation, rather than the much larger historical interpretation, but that arithmetic is still not a benchmark.

Repository policy therefore treats energy as **unavailable pending controlled measurement**. No historical percentage-saving headline is accepted as measured evidence.

### 5. XAI fidelity is not established

Structural inspection of the historical medical `_generate_heatmap` path shows accesses to PCA/Fisher state but no N1/N2 classifier decision or target-class input in the heatmap generator.

Current defensible interpretation: **weighted PCA reconstruction/visualization**. It is not evidence of faithful classifier attribution or clinical validity.

### 6. Historical environment and export chain remain incomplete

Binary inspection of the Elite bundle found `_sklearn_version` followed by **1.8.0** at the documented decompressed offset. This is a demonstrated serialization marker and only an environment clue.

Historical M4 screenshots corroborate **Python 3.13.7 / GTX 1050 Ti** for that M4 context. They do not prove Elite used the same environment.

The historical exporter expects seven inputs that are absent at the resolved paths. Recovered bundle/cache/RAW artifacts in other folders do not establish that the original exporter can regenerate the historical package.

### 7. The V24 79.37% rescue route is not identified

Documentary screenshot evidence shows:
- `N1 + TTA = 78.45%`;
- rescued linear N2 = **79.37%**.

Current preserved candidates do not identify that checkpoint:
- `v24_n2.pkl` is an MLP;
- M4 N2 has 30 inputs;
- M5/Elite polynomial bundles are distinct routes.

Additional searches did not recover the exact rescue script/checkpoint. No parameter search or training was used to force 79.37%.

### 8. Serialized artifacts remain a trusted-code boundary

`joblib` / pickle bundles can execute code during deserialization. Documentation, Docker and launchers treat runtime artifacts as trusted inputs, but a validated release still needs an immutable accepted manifest/provenance chain before deserialization.

## Resolved engineering defects

- `/api/reset` fixed so class counters retain fixed length.
- session-stat updates protected by a re-entrant lock.
- automated GitHub Actions regression CI established.
- missing Pillow dependency added after clean-install failure.
- CPU-only PyTorch install path used in CI.
- Docker parent-context copy defect removed.
- public Docker image separated from private runtime artifacts.
- container/runtime artifact preflight added.
- `.gitignore` protects serialized runtime artifacts from accidental commit.
- SHA-256 manifest tooling added and tested.
- sample-level prediction comparator added and tested.
- public probability/confidence language reduced to score semantics.
- diagnostic cached-batch selection changed from random sampling to deterministic stored-order traversal.
- public UI/API no longer exposes unvalidated historical energy savings as live numeric metrics.
- recovered batch-dependent noise behavior is explicitly documented.

## Clean Baseline v1 — required next evidence

Historical reconstruction and a clean future baseline are different objectives.

The next defensible performance result must:
1. start from raw CIFAR-10 sample identities;
2. freeze train/validation/calibration/test identities before any fitting;
3. fit PCA on training data only;
4. fit Fisher weights / centroids / augmentation statistics on training data only;
5. create N2 stacking features using valid OOF or documented holdout logic;
6. remove hidden batch-context dependence from inference;
7. freeze seeds, environment, dtype, feature ordering and source commit;
8. retain full predictions, scores and per-class metrics with explicit score semantics;
9. run the final test only after model-selection decisions are frozen;
10. pass the leakage template with no unresolved material `FAIL` / `UNKNOWN` items;
11. reproduce the accepted output from a clean environment within documented tolerances.

A lower clean accuracy must be reported as-is; it is more scientifically useful than an unreproducible higher figure.

## Metadata inconsistency outside repository-file write surface

The GitHub short “About” description still contains older unconditional 80.14% / 92.6%-energy wording. Issue #11 tracks this because the connected repository tools do not expose repository-description mutation. Until changed, README/MILESTONES/public-status files are the authoritative evidence statements.

## Current priority order

1. Preserve and cross-check recovered evidence without modifying originals.
2. Recover exact RAW→PCA provenance if possible.
3. Recover exact historical V24 80.14% source/config/predictions and the 79.37% rescue checkpoint/script if possible.
4. Complete independent historical leakage/provenance audit.
5. Build and execute Clean Baseline v1.
6. Freeze the clean environment and prediction package.
7. Measure energy against controlled baselines on identical hardware.
8. Validate score calibration and explanation fidelity.
9. Keep Connectome Edge R&D isolated/documentary until an explicit next-phase decision.
