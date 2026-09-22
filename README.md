# AB-GEN — Geometric / Spectral / Polynomial Vision Research

> **Experimental image-classification research with an evidence-first reproducibility policy**

AB-GEN is an experimental computer-vision architecture built around dimensional reduction, Fisher weighting, multi-scale spectral features, geometric class structure, an N1 learner ensemble and an N2 meta-learner.

The project is under an active reproducibility and engineering audit. Public claims are deliberately separated into **Reported**, **Recovered**, **Reconstructed**, **Reproduced** and **Validated** evidence states. A nearby accuracy number is not treated as proof of historical reproduction.

**Official research site:** https://msrobotikaabgenresearch.wordpress.com

> **Metadata note:** the repository's short GitHub “About” description is tracked in issue #11 because it still contains older unconditional performance/energy wording. This README and `MILESTONES.md` define the current evidence status.

## Current evidence status

| Route | Result | Evidence state | What it means |
|---|---:|---|---|
| V24 Slow Burn historical record | **80.14%** | **REPORTED** | Internal project record; exact historical RAW→PCA→model reproduction is not established. |
| Elite / Slow Burn recovered bundle | **8,017 / 10,000 = 80.17%** | **RECOVERED** | Recovered PCA-cache execution; not proof of the exact historical 80.14% route. |
| M5 MASTER | **7,955 / 10,000 = 79.55%** | **RECONSTRUCTED / EXECUTED** | Original frozen N1 plus reconstructed polynomial N2. |
| M4 original | **7,805 / 10,000 = 78.05%** | **RECOVERED** | Recovered PCA-cache evaluation matching the recorded project result. |
| V24 rescue screenshot | **79.37%** | **HISTORICAL DOCUMENTARY EVIDENCE** | Screenshot of a rescued linear N2 route; exact checkpoint/script not identified. |
| MNIST Universal V24 | **97.79%** | **REPORTED** | Historical project record; exact reproduction remains pending. |

No current CIFAR-10 figure in this repository is presented as a clean, leakage-audited RAW-image reproduction.

## 2026-09-22 evidence continuity update

Phase 1 remains **documentarily closed**, not historically reproduced end to end. The following additional evidence was produced without modifying recovered originals.

### RAW dataset duplicate audit

The verified CIFAR-10 source contains **50,000 train + 10,000 test images = 60,000 byte-distinct images**. No exact duplicate image was found within either partition or across train/test, and the archive hash remained unchanged before and after the audit.

This result is deliberately narrow: it does **not** rule out perceptual similarity, augmentation dependence, fitting leakage, or an incorrect cache→RAW association. It also does not recover the historical RAW→PCA producer.

### Prediction and score exports

- Three preserved routes now have **30,000 prediction rows** with stable IDs derived from hashes of the official RAW image bytes.
- Frozen M4 and M5 MASTER reruns matched the previously preserved predicted classes **20,000 / 20,000** while retaining **7,805** and **7,955** correct respectively. These checks do not promote either route to exact historical reproduction.
- Elite score extraction reproduced the preserved class on **10,000 / 10,000** rows while retaining **8,017** correct.
- Across M4, M5 MASTER and Elite, the current evidence package contains **300,000 class scores** for 30,000 evaluated rows.
- M4 score vectors are softmax outputs from its recovered N2 and are **not calibration-certified probabilities**. M5 MASTER and Elite use Ridge `decision_function` values and are **not probabilities**.
- A standalone Python verifier passes all **30,000 rows / 300,000 scores** and rejects three deliberately corrupted copies. This verifies internal package consistency and integrity; it is not external validation, cache→RAW provenance proof or historical reproduction.

### Sample-level comparison of recovered routes

The preserved predictions show substantial route-level disagreement even when net accuracy differences are small:

| Comparison | B corrects A | B loses an A correct | Different predictions | Net correct |
|---|---:|---:|---:|---:|
| M4 → M5 MASTER | 419 | 269 | 957 | +150 |
| M4 → Elite | 628 | 416 | 1,413 | +212 |
| M5 MASTER → Elite | 445 | 383 | 1,131 | +62 |

For M5 MASTER → Elite, another 303 samples change predicted class while both routes are wrong. Therefore the +62 net gain does not imply only 62 changed predictions. This comparison describes preserved recovered executions; it is not a causal ablation and cannot be extended to the missing historical 80.14% predictions.

### Expanded batch-dependence characterization

The targeted audit retained the same 32 low-margin Ridge cases selected without labels and expanded the matrix to batch sizes 1/2/4/8/16/32/64, multiple positions and two companion groups:

- **1,120 configurations** and **2,240 executions**;
- **344 class changes** relative to individual inference, affecting 31 of the 32 targeted cases;
- **0 class changes** with fixed noise;
- **0 class changes** with noise removed;
- **0 differences** between identical repeated calls;
- transferring the noise assigned in batch to the same sample in individual inference reproduced the batch class in **1,120 / 1,120** configurations;
- changing only companion samples produced **0 changes in 544 paired comparisons**.

The recovered engine resets its RNG on every inference call and assigns perturbation noise according to array shape and sample position. These interventions demonstrate the cause of the class changes **within the tested matrix**. They do not establish population-wide frequency and do not prove the historical 80.14% versus recovered 80.17% gap was caused by this mechanism.

### Additional provenance findings

- Binary inspection of the Elite bundle found `_sklearn_version` followed by **1.8.0**. This is a demonstrated serialization marker and only an **environment clue**, not proof of the full training environment.
- Historical M4 screenshots corroborate **Python 3.13.7 / GTX 1050 Ti** for that M4 context; that environment is not automatically attributed to Elite.
- The historical V24 rescue screenshot documents `N1 + TTA = 78.45%` and a rescued linear N2 at **79.37%**. The preserved `v24_n2.pkl` is an MLP, M4 N2 has 30 inputs, and the polynomial M5/Elite bundles are different routes. No recovered candidate is currently identified as the exact 79.37% rescue checkpoint.
- Seven export inputs expected at historical paths are absent there. Recovered bundle/cache/RAW copies elsewhere do not by themselves prove regeneration of the historical export chain.

## Important audit boundaries

- The exact historical RAW→preprocessing/augmentation→PCA producer remains unresolved. PCA test leakage is **not demonstrated**, but cannot be ruled out from the recovered cache alone.
- Recovered MASTER logic contains class-dependent preprocessing/augmentation-state concerns before its final train/validation split. Do not automatically transfer those exact indices or defects to Elite without evidence.
- A separate `demo_inferencia.py` route was found by code review to fit N2 with test labels. It was kept separate and is not a valid estimate of generalization on that same test set.
- The historical medical/XAI heatmap accesses PCA/Fisher state but not N1/N2 or a target class in its heatmap generator. It is evidence of weighted PCA reconstruction/visualization, not demonstrated faithful classifier attribution.
- Historical energy figures are constants/derived arithmetic, not controlled measurements. The corrected arithmetic from those constants is approximately **0.001080555 kWh per one million inferences saved**, but even a correct calculation from assumed constants is not an energy benchmark.
- Connectome remains a future experimental track. No Connectome training or performance result is claimed.

## Immediate technical priority: Clean Baseline v1

Historical recovery remains important for provenance, but the next scientifically defensible performance result must come from a **new clean baseline** with a completely controlled data boundary:

1. start from raw CIFAR-10 data with immutable sample identities;
2. define train/validation/calibration/test identities before any data-dependent fitting;
3. fit PCA on training data only;
4. fit Fisher weights, centroids and any augmentation statistics on training data only;
5. generate N2 stacking features without target leakage using documented OOF/holdout logic;
6. use deterministic inference with no hidden batch-position-dependent randomness;
7. freeze source commit, environment, seeds, dtypes, feature order and artifact hashes;
8. store full test predictions, class metrics, confusion matrix and calibration evidence where applicable;
9. execute the final test only after model-selection decisions are frozen;
10. reproduce the accepted output from a clean environment before promotion.

A lower clean score is more valuable than a higher score whose data lineage cannot be defended.

## Two research tracks, kept separate

### A. Historical recovery / forensics

Purpose: reconstruct what the historical AB-GEN artifacts actually did without rewriting history.

Open questions include:
- exact RAW→PCA transformer and preprocessing lineage;
- historical V24 split/script/prediction identity;
- exact 79.37% rescued-linear-N2 checkpoint/script;
- leakage scope in class-dependent preprocessing and stacking;
- exact historical environment and artifact provenance;
- controlled CPU/GPU comparison of recovered behavior.

Recovered originals stay unchanged; analysis is performed on copies/branches.

### B. Clean baseline / future research

Purpose: create the first leakage-audited, deterministic, reproducible AB-GEN reference from raw inputs. This clean baseline will become the comparison target for controlled Green AI measurements and later architecture experiments.

The separate **Connectome Edge R&D** track remains documentary/future research until explicitly advanced. Any future C1 performance comparison must use the clean baseline and matched evaluation gates.

## Evidence and release gates

- **[MILESTONES.md](MILESTONES.md)** — evidence status and roadmap.
- **[AUDIT_NOTES.md](AUDIT_NOTES.md)** — current technical audit boundaries.
- **[BASELINE_ACCEPTANCE.md](BASELINE_ACCEPTANCE.md)** — evidence-state promotion rules.
- **[REPRODUCIBILITY.md](REPRODUCIBILITY.md)** — reproducibility requirements.
- **[LEAKAGE_AUDIT_TEMPLATE.md](LEAKAGE_AUDIT_TEMPLATE.md)** — required leakage review.
- **[GREEN_AI_BENCHMARK_PROTOCOL.md](GREEN_AI_BENCHMARK_PROTOCOL.md)** — controlled energy/latency protocol.
- **[ARTIFACT_MANIFEST_TEMPLATE.md](ARTIFACT_MANIFEST_TEMPLATE.md)** — source/artifact/environment/hash manifest.
- **[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)** — pre-publication gate.
- **[SECURITY.md](SECURITY.md)** — serialized-artifact trust boundary.
- **[CONNECTOME_EDGE_RND.md](CONNECTOME_EDGE_RND.md)** — isolated connectome-inspired Edge-AI research protocol.

---

## Recovered architecture

| Stage | Technique | Purpose |
|---|---|---|
| PCA 1200D | dimensional reduction | Recovered cache is 1200D; exact historical RAW→PCA transformer remains open. |
| Fisher weighting | class-discriminant scaling | Must be fit strictly inside training data in a clean baseline. |
| Multi-scale FFT | spectral features | Frequency-domain expansion. |
| Geometric features | centroid similarities / higher-order terms | Class-structure representation. |
| N1 ensemble | LR + MLPs + LightGBM | Diverse learner pool. |
| N2 | route-dependent recovered meta-learner | M4, M5 MASTER and Elite have distinct recovered N2 evidence and must not be conflated. |

The public demo operates on cached PCA-projected inputs. It is a **diagnostic recovered path**, not arbitrary raw-image inference.

---

## Public demo boundary

```bash
pip install -r requirements_demo.txt
python app.py
```

The demo requires trusted runtime artifacts that are **not distributed** in the public repository. A fresh clone is therefore not a standalone model reproduction.

The diagnostic UI:
- traverses cached samples in deterministic stored order rather than randomly sampling them;
- labels live accuracy as diagnostic only;
- exposes normalized decision scores as uncalibrated scores, not probabilities;
- explicitly reports the known batch-invariance failure;
- does **not** calculate or display unvalidated historical energy-savings percentages.

### Docker runtime boundary

The Docker image contains public application code only. Runtime model/data/compatibility artifacts are mounted read-only and remain trusted-code objects.

Expected local runtime files:
- `artifacts/abgen_bundle.pkl`
- `artifacts/sample_data.pkl`
- `artifacts/training_module.py`

Before a validated release uses serialized artifacts, their provenance and SHA-256 hashes must be bound to an immutable accepted manifest.

```bash
docker compose build
docker compose up
```

If required artifacts are absent, container preflight fails rather than guessing paths or downloading unknown serialized objects.

---

## Green AI status

Historical project material contains energy-efficiency claims, but those values are **not validated benchmark results**. Percentage-savings headlines are withheld until measurement is repeated under the controlled protocol.

A valid Green AI comparison must report, on identical hardware and equivalent accuracy/evaluation boundaries:
- model-only and end-to-end inference separately;
- CPU and GPU execution separately;
- warm-up and batch size;
- p50/p95 latency and throughput;
- peak RAM/VRAM;
- repeated joules/image measurements with uncertainty;
- baseline measurements collected under the same protocol;
- carbon conversion only after measured energy is established.

---

## Repository engineering

- `engine.py` — recovered historical inference engine; batch-dependent noise behavior is explicitly documented.
- `app.py` — diagnostic Flask API/UI backend with deterministic cache traversal.
- `serve.py` — production WSGI entry point.
- `docker_entrypoint.py` — runtime artifact preflight.
- `artifacts/README.md` — trusted runtime-artifact contract.
- `templates/` and `static/` — diagnostic UI.
- `tests/` — regression tests for evidence semantics, public claims, runtime boundaries and deterministic tooling.
- `.github/workflows/ci.yml` — CPU regression CI.
- `AUDIT_NOTES.md` — current technical audit state.
- `tools/artifact_manifest.py` — SHA-256 manifest creation/verification.
- `tools/compare_predictions.py` — sample-level prediction comparator.

---

## Research direction

AB-GEN is not currently positioned as a replacement for state-of-the-art CNNs or Vision Transformers on raw accuracy alone. The primary questions are testable:

> **Can the architecture retain useful accuracy under a leakage-free, deterministic RAW→prediction pipeline, and if so, does it offer measurable resource or structural advantages under controlled comparison?**

A second, explicitly experimental line studies sparse, modular and connectome-inspired computation for Edge AI. It remains isolated from historical recovery and must beat matched controls before any advantage is claimed.

The next meaningful milestone is not a headline number. It is a clean result that another party can reproduce from frozen source, inputs and artifacts.

---

Built with Python, PyTorch, LightGBM, scikit-learn and Flask.
