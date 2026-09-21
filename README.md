# AB-GEN — Geometric / Spectral / Polynomial Vision Research

> **Experimental image-classification research with an evidence-first reproducibility policy**

AB-GEN is an experimental computer-vision architecture built around dimensional reduction, Fisher weighting, multi-scale spectral features, geometric class structure, an N1 learner ensemble and an N2 polynomial meta-learner.

The project is under an active reproducibility and engineering audit. Public claims are deliberately separated into **Reported**, **Recovered**, **Reconstructed**, **Reproduced** and **Validated** evidence states. A nearby accuracy number is not treated as proof of historical reproduction.

**Official research site:** https://msrobotikaabgenresearch.wordpress.com

> **Metadata note:** the repository's short GitHub “About” description is tracked in issue #11 because it still contains older unconditional performance/energy wording. This README and `MILESTONES.md` define the current evidence status.

## Current evidence status

| Route | Result | Evidence state | What it means |
|---|---:|---|---|
| V24 Slow Burn historical record | **80.14%** | **REPORTED** | Internal project record; exact historical RAW→PCA→model reproduction is not yet established. |
| Elite / Slow Burn recovered bundle | **8,017 / 10,000 = 80.17%** | **RECOVERED** | Recovered PCA-cache execution; not proof of the exact historical 80.14% route. |
| M5 MASTER | **7,955 / 10,000 = 79.55%** | **RECONSTRUCTED / EXECUTED** | Original frozen N1 plus reconstructed polynomial N2; saved prediction counts were checked. |
| M4 original | **7,805 / 10,000 = 78.05%** | **RECOVERED** | Recovered PCA-cache evaluation matching the recorded project result. |
| MNIST Universal V24 | **97.79%** | **REPORTED** | Historical project record; exact reproduction remains pending. |

No current CIFAR-10 figure in this repository is presented as a clean, leakage-audited RAW-image reproduction.

### Demonstrated recovery finding: batch dependence

During the 2026-09-21 recovery audit, 32 low-margin Ridge cases were selected **without labels** for a targeted invariance check:

- 18 predictions changed between full-batch and single-sample inference;
- 17 changed between full-batch and a batch of 32;
- repeating the exact same batch produced zero changes.

The recovered engine resets its RNG on every inference call and assigns noise according to array shape and batch position. That makes the historical recovered path deterministic for an identical batch, but **not invariant to batch composition/position**. The 32-case subset is intentionally difficult and is not representative of the whole test set. The finding does **not** establish that batch dependence explains the 80.14% versus 80.17% difference.

## Immediate technical priority: Clean Baseline v1

Historical recovery remains important for provenance, but the next scientifically defensible performance result must come from a **new clean baseline** with a completely controlled data boundary. The execution gate is tracked in **issue #39**.

1. start from raw CIFAR-10 data with immutable sample identities;
2. define the train/validation/test split before any label-dependent fitting;
3. fit PCA on training data only;
4. fit Fisher weights, centroids and any augmentation statistics on training data only;
5. generate N2 stacking features without target leakage (OOF/holdout as documented);
6. use deterministic inference — no batch-position-dependent random perturbation;
7. freeze source commit, environment, seeds, dtypes, feature order and artifact hashes;
8. store full test predictions, class metrics and confusion matrix;
9. execute the test evaluation once after model-selection decisions are frozen;
10. only after that baseline exists, run controlled energy and Connectome-v0 comparisons.

A lower clean score is more valuable than a higher score whose data lineage cannot be defended.

## Two research tracks, kept separate

### A. Historical recovery / forensics

Purpose: reconstruct what the historical AB-GEN artifacts actually did without rewriting history.

Open questions include:
- exact RAW→PCA transformer and preprocessing lineage;
- historical V24 split/script/prediction identity;
- leakage scope in class-dependent preprocessing and stacking;
- full impact of the recovered batch-dependent noise path;
- exact historical environment and artifact provenance.

Recovered originals stay unchanged; analysis is performed on copies/branches.

### B. Clean baseline / future research

Purpose: create the first leakage-audited, deterministic, reproducible AB-GEN reference from raw inputs. This clean baseline will become the comparison target for controlled Green AI measurements and later architecture experiments.

The separate **Connectome Edge R&D** track may continue at **C0** (literature/data/topology mapping), but no Connectome-v0 performance claim should be compared against historical cache results. C1 training should use the clean baseline and identical evaluation gates.

## Evidence and release gates

- **[MILESTONES.md](MILESTONES.md)** — evidence status and roadmap.
- **[BASELINE_ACCEPTANCE.md](BASELINE_ACCEPTANCE.md)** — exact evidence-state promotion rules.
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
| Polynomial Ridge N2 | degree-2 meta-learner | Fusion of N1 outputs. |

The public demo operates on cached PCA-projected inputs. It is a **diagnostic recovered path**, not arbitrary raw-image inference.

---

## Public demo boundary

The public repository intentionally does **not** distribute the recovered private runtime artifacts. A fresh clone is therefore not a standalone model reproduction.

A local diagnostic run requires this complete trusted set under `artifacts/`:

- `artifacts/abgen_bundle.pkl`
- `artifacts/sample_data.pkl`
- `artifacts/training_module.py`
- `artifacts/runtime-manifest.json`

The manifest must match the artifact bytes and itself come from a trusted evidence/release package. Runtime preflight occurs before compatibility-module import or joblib/pickle deserialization in supported launch paths.

Once that trusted set is present:

```bash
pip install -r requirements_demo.txt
python app.py
```

On Windows, `run_demo.bat` applies the same `artifacts/` contract and anchors execution to the repository directory.

The diagnostic UI:
- traverses cached samples in deterministic stored order rather than randomly sampling them;
- labels live accuracy as diagnostic only;
- exposes normalized decision scores as uncalibrated scores, not probabilities;
- explicitly reports the known batch-invariance failure;
- does **not** calculate or display unvalidated historical energy-savings percentages.

### Docker runtime boundary

The Docker image contains public application code only. Runtime model/data/compatibility artifacts are mounted read-only and remain trusted-code objects.

Docker uses the same four-file contract above, mounted at `/artifacts`. Before deserialization, startup verifies the runtime files against the configured trusted manifest and fails closed on missing files or byte mismatches.

```bash
docker compose build
docker compose up
```

Hash verification establishes byte integrity, not provenance by itself. Issue #21 remains open until the accepted manifest is bound to an immutable trusted release/evidence package.

---

## Green AI status

Historical project material contains energy-efficiency claims, but those values are **not validated benchmark results**. The audit identified at least one derived million-inference calculation with a factor-of-1,000 discrepancy, so percentage-savings headlines are withheld until measurement is repeated under the controlled protocol.

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

- `engine.py` — recovered historical inference engine; batch-dependent noise behavior is explicit and compatibility code is loaded only at engine creation, not module import.
- `app.py` — diagnostic Flask API/UI backend with deterministic cache traversal.
- `runtime_integrity.py` — centralized fail-closed artifact/manifest integrity preflight.
- `serve.py` — explicit Waitress production WSGI entry point.
- `docker_entrypoint.py` — container preflight/launch boundary.
- `artifacts/README.md` — trusted runtime-artifact contract.
- `templates/` and `static/` — diagnostic UI.
- `tests/` — regression tests for evidence semantics, public claims, runtime boundaries and deterministic tooling.
- `.github/workflows/ci.yml` — CPU regression CI with dependency checks, compile checks, tests and exact environment snapshot artifact.
- `AUDIT_NOTES.md` — current technical audit state.
- `tools/artifact_manifest.py` — SHA-256 manifest creation/verification.
- `tools/compare_predictions.py` — sample-level prediction comparator.

---

## Research direction

AB-GEN is not currently positioned as a replacement for state-of-the-art CNNs or Vision Transformers on raw accuracy alone. The primary questions are now testable:

> **Can the architecture retain useful accuracy under a leakage-free, deterministic RAW→prediction pipeline, and if so, does it offer measurable resource or structural advantages under controlled comparison?**

A second, explicitly experimental line studies sparse, modular and connectome-inspired computation for Edge AI. It remains isolated from historical recovery and must beat matched controls before any advantage is claimed.

The next meaningful milestone is not a headline number. It is a clean result that another party can reproduce from frozen source, inputs and artifacts.

---

Built with Python, PyTorch, LightGBM, scikit-learn and Flask.
