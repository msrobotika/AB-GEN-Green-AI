# FlyCore C1.20 — Independent-topology KMNIST transport protocol

## Status

**C1.20P: DRAFT / PRE-FREEZE ONLY**

**NO TRAINING. NO PERFORMANCE EXECUTION. NO C1.20 SCIENTIFIC RESULT EXISTS.**

This protocol is the next prospective FlyCore stress test after the frozen C1.19 KMNIST transport PASS. It is intentionally designed to remove the strongest remaining shared-design dependency in C1.19: reuse of the C1.18 confirmation topology bank.

## Precursor evidence

C1.19 is closed, sealed and immutable:

- models: **160**
- repeated cells: **3,200**
- independent structural pairs: **16**
- B1 pair wins: **16/16**
- T_obs: **+0.002128195102507025**
- exact one-sided sign-flip p-value: **1.52587890625e-05**
- upper tail: **1 / 65,536**
- refit: **NO**
- optional stopping: **NO**
- run-tree SHA-256: `36621bbe2f43cf8da6bdb02df8fc2f19400112eb3d88d60bdf1f1f02c1484170`

C1.19 reused the same 16 C1.18 confirmation structural pairs / 32 topologies. C1.20 therefore tests whether the transported predictor survives replacement of that topology bank by a completely independent structural bank.

## Primary scientific question

Does the **frozen C1.18 RDE+FLE predictor** retain lower pair-level prediction error than the **frozen C1.18 RDE-only baseline** on KMNIST when evaluated on a new topology bank that was not used in C1.18 or C1.19?

## Scientific lock proposal

Unless invalidated before freeze, C1.20 will retain:

- architecture: **FlyCore64**
- recurrent steps: **T=14**
- alpha: **0.35**
- epochs: **10**
- batch size: **128**
- optimizer: **Adam**
- learning rate: **0.001**
- loss: **CrossEntropyLoss**
- checkpoint rule: **final epoch only**
- execution target: **CPU**
- dataset: **KMNIST**
- preprocessing: **ToTensor + Normalize(0.1307, 0.3081)**

Not allowed:

- best-epoch selection;
- fine-tuning after outcome inspection;
- damage adaptation;
- predictor coefficient refit;
- functional-feature redefinition;
- performance-driven topology selection;
- rescue models;
- threshold changes after inspection.

## Frozen predictors

C1.20 will reuse the exact B0 and B1 coefficients frozen from C1.18 and transported unchanged in C1.19.

C1.20 is a prediction test. C1.19 and C1.20 outcomes must not update coefficients or preprocessing.

## Proposed independent seed namespace

Topology candidates:

`1830000..1830399`

Training seeds:

`{1831001, 1831002, 1831003, 1831004, 1831005}`

Damage seeds:

`{1832001, 1832002, 1832003, 1832004}`

Calibration seed:

`1833001` with `n=2048`.

All namespaces must be audited as disjoint from prior C1.17, C1.18 and C1.19 namespaces before scientific freeze.

## Topology-bank construction

Reuse the exact structural-only C1.18 confirmation builder and eligibility/pairing rule.

Target:

- **400** fixed candidate topology seeds;
- **16** structural pairs;
- **32** selected topologies.

Eligibility and pairing must use structural information only.

No KMNIST forward pass, FLE value, prediction error, damaged accuracy, or other performance observation may influence topology eligibility or pair selection.

If the fixed candidate range yields fewer than 16 valid pairs, C1.20 is **INVALID / INSUFFICIENT**. The range must not be expanded after inspection.

## Independence requirement

Every selected C1.20 topology hash must have zero overlap with:

- all C1.18 selected topology hashes;
- all C1.19 selected topology hashes;
- and, as an additional audit, prior selected C1.17 topology banks.

Any overlap stops preflight before training.

## NODE-damage lock

Use the existing frozen lesion protocol:

- lesion-eligible nodes: **16..55**
- damage counts: **0 / 2 / 4 / 8 / 12**
- corresponding fractions: **0 / 5 / 10 / 20 / 30%**
- four damage seeds;
- ten independently permuted nested curves per damage seed;
- exact lesion sets paired LOW/HIGH;
- lesion sets shared across training seeds;
- post-training lesion only;
- no retraining after damage.

## Functional importance and FLE

Use the frozen intact-model activation-times-gradient importance over lesion-eligible nodes.

For node `i`, the historical primary definition remains the intact task-relevant activation-times-gradient quantity `q_i`, normalized into `w_i` over nodes 16..55.

For lesion set `L`:

- `FLE(L) = sum(w_i for i in L)`
- `EFLE(L) = FLE(L) - |L|/40`
- `EFLE_AUC` uses the same normalized trapezoidal integration over the frozen damage fractions.

Pair functional contrast:

`X_FLE = EFLE_AUC(LOW_RDE) - EFLE_AUC(HIGH_RDE)`

No fallback functional metric is permitted for the primary test.

## Primary endpoint

Preserve the historical NODE robustness sign convention:

`Y = AUC_NODE_HIGH - AUC_NODE_LOW`

## Primary independent unit

The structural pair is the inferential unit.

For each pair, prediction-error improvement is:

`I_p = MSE_B0,p - MSE_B1,p`

Each pair contains repeated matched cells across:

- 5 training seeds
- × 4 damage seeds
- × 10 lesion curves
- = **200 repeated cells per pair**

The confirmatory inferential sample size remains **n=16 pairs**.

## Primary statistical test

`T_obs = mean(I_p)`

Use an exact one-sided sign-flip test across all:

`2^16 = 65,536`

pair-sign assignments.

C1.20 passes only if both conditions hold:

1. `T_obs > 0`
2. `p_exact < 0.05`

Otherwise the scientific decision is **FAIL**.

No optional stopping, sample expansion, rescue model, secondary endpoint, alternate threshold, or post-hoc refit may change that decision.

## Interpretation boundary

A PASS would add evidence that the frozen FashionMNIST-developed RDE+FLE relation transports jointly across:

1. dataset shift to KMNIST; and
2. an independently generated FlyCore64 topology bank.

A FAIL would establish a concrete boundary: the C1.19 transport result did not survive removal of the original C1.18 topology bank.

Neither result establishes universality, biological equivalence, causality of FLE, arbitrary-architecture generalization, or Edge-AI superiority.

## Mandatory pre-freeze gates

No C1.20 performance execution is authorized until all of the following are frozen and verified:

1. exact C1.20 scientific source;
2. exact structural-bank builder reused from the verified historical implementation;
3. selected topology manifest and hashes;
4. proof of zero topology overlap with prior selected banks;
5. exact frozen B0/B1 coefficients;
6. KMNIST raw-tree and official archive hashes;
7. damage manifest;
8. calibration manifest;
9. training seed manifest;
10. runner hash;
11. source/dependency manifest;
12. a verify-only procedure that fails closed on any mismatch.

The preflight must additionally assert that no C1.20 performance outputs exist before authorization.

## Current next action

Build and audit **C1.20P preflight/freeze only**.

Do not start model training or performance evaluation until the freeze package passes its own verify-only checks and the resulting hashes are recorded.
