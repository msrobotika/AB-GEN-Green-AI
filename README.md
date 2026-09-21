# AB-GEN — Geometric-Polynomial Vision Research

> **Hybrid geometric + spectral + polynomial ensemble for image classification**

AB-GEN is an experimental computer-vision architecture built around dimensional reduction, Fisher weighting, multi-scale spectral features, geometric class structure, an N1 learner ensemble and an N2 polynomial meta-learner.

The project is currently undergoing a reproducibility and engineering audit. Public claims are intentionally separated into **reported**, **recovered/reconstructed**, and **reproduced/validated** results.

**Official research site:** https://msrobotikaabgenresearch.wordpress.com

## Validation status

- **CIFAR-10 V24 Slow Burn — historical headline:** internal project records report **80.14% accuracy**. This remains **REPORTED**, not yet exactly reproduced from the original raw training pipeline.
- **Elite / Slow Burn bundle — current recovery:** **8,017 / 10,000 = 80.17%** from the recovered PCA-cache path. This is a recovered execution result, not proof of exact historical V24 reproduction.
- **M5 MASTER — reconstructed path:** **7,955 / 10,000 = 79.55%**, using the original frozen N1 with a reconstructed polynomial N2. The execution completed and prediction counts were verified.
- **M4 original — recovered metric:** **7,805 / 10,000 = 78.05%**, matching the documented result when evaluated from the recovered PCA cache.
- **MNIST Universal V24:** internal project records report **97.79% accuracy**; exact reproduction remains pending.
- Full reproduction from raw images through the exact historical preprocessing/training path is **not yet certified**.
- Previously published Green AI energy figures are being re-benchmarked under a controlled, reproducible measurement protocol.

### Recovery finding: deterministic batch dependence

During the 2026-09-21 recovery audit, 32 low-margin Ridge cases were selected **without labels** for a targeted invariance check. For those selected cases:

- 18 predictions changed between full-batch and single-sample inference;
- 17 changed between full-batch and a batch of 32;
- repeating the exact same batch produced zero changes.

The recovered engine resets its random generator per call and assigns noise according to batch shape/position, so a **batch-dependent inference path is demonstrated** for this targeted subset. The subset is not representative of the whole test set, and this finding has **not** been shown to explain the historical 80.14% versus recovered 80.17% difference.

Evidence and release gates:

- **[MILESTONES.md](MILESTONES.md)** — public evidence status and roadmap.
- **[REPRODUCIBILITY.md](REPRODUCIBILITY.md)** — minimum protocol for promoting a result from reported to reproduced/validated.
- **[ARTIFACT_MANIFEST_TEMPLATE.md](ARTIFACT_MANIFEST_TEMPLATE.md)** — source/artifact/environment/hash manifest template.
- **[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)** — pre-publication gate for releases, benchmark claims and public communications.
- **[SECURITY.md](SECURITY.md)** — trusted-artifact and serialized-model security boundary.
- **[CONNECTOME_EDGE_RND.md](CONNECTOME_EDGE_RND.md)** — separate hypothesis-driven research plan for sparse, modular, connectome-inspired Edge AI.

### 🎥 Live demo
[![AB-GEN Live Demo](https://img.youtube.com/vi/5gtssh9VvI4/maxresdefault.jpg)](https://youtu.be/5gtssh9VvI4)

---

## Architecture

| Stage | Technique | Purpose |
|---|---|---|
| PCA 1200D | Geometric embedding | Dimensional reduction |
| Fisher Weighting | Class-discriminant scaling | Emphasise informative PCA dimensions |
| Multi-scale FFT | Spectral analysis | Frequency-domain structure |
| Geometric features | Centroid similarities, topology, higher-order terms | Class-structure representation |
| Swarm N1 | LR + MLPs + LightGBM ensemble | Diverse learner pool |
| Poly Ridge N2 | Degree-2 polynomial meta-learner | Cross-learner interaction and fusion |

The public inference engine operates on PCA-projected inputs and reconstructs the geometric/spectral feature path used by the deployed model. A complete raw-image-to-prediction reproducible pipeline is one of the current engineering goals.

---

## Current audit priorities

1. Recover the exact **RAW → PCA** transformer, preprocessing lineage and environment used by the historical runs.
2. Link the exact **V24 Slow Burn 80.14%** script, split, predictions and model artifacts to the recovered elite bundle.
3. Complete an independent leakage audit, keeping historical reconstruction separate from clean validation.
4. Characterize the demonstrated batch-dependent noise path across batch size, position, composition and deterministic repeats.
5. Freeze exact dependency versions, seeds, dtypes, feature ordering and artifact hashes for every recovered path.
6. Build a raw-image end-to-end inference path that does not depend on undocumented cache state.
7. Evaluate calibration using ECE, Brier score, NLL and reliability diagrams.
8. Measure energy on identical hardware and inference boundaries against controlled baselines.
9. Validate XAI fidelity against the actual decision path rather than treating PCA/geometric visualisation alone as proof of explanation.
10. Package reproducible releases with environment locks, hashes and benchmark metadata.

---

## Green AI benchmark status

Earlier project material reports approximately **0.31 mJ/inference** for AB-GEN and a large reduction relative to a ResNet-18 reference. These values are retained as **historical/reported project figures**, not as independently reproduced measurements.

The current audit also found that at least one historical million-inference energy-saving calculation contains a factor-of-1,000 discrepancy. No public Green AI claim should therefore be promoted until the controlled benchmark protocol is executed on measured hardware.

The validation benchmark will separate:
- model-only inference;
- preprocessing + model end-to-end inference;
- CPU and GPU execution;
- latency and throughput;
- joules per image;
- RAM/VRAM use;
- accuracy under the same evaluation protocol.

Carbon figures will only be derived after measured energy is established and the grid-intensity source is explicitly documented.

---

## Demo quick start

```bash
pip install -r requirements_demo.txt
python app.py
```

The demo requires the model bundle and sample-data artifacts used by the inference engine. Those artifacts are not currently distributed in the public repository, so a fresh clone is **not yet a complete reproducible package**.

### Docker runtime boundary

The Docker image intentionally contains **public application code only**. It does not bake private model/data artifacts or the serialization-compatibility module into the image.

A validated runtime will use a local `artifacts/` directory mounted read-only. The current runtime contract expects:

- `artifacts/abgen_bundle.pkl`
- `artifacts/sample_data.pkl`
- `artifacts/training_module.py`

These files are excluded from Git. Their provenance and SHA-256 hashes must be recorded by the validated release process before use.

Once a trusted artifact set exists locally:

```bash
docker compose build
docker compose up
```

If the validated artifacts are absent, the container exits during preflight with a clear error. It does **not** guess parent directories, download unknown bundles or deserialize arbitrary third-party files.

At present, the public repository does not distribute the validated V24 Slow Burn artifact set, so Docker should be treated as deployment scaffolding rather than a standalone reproducible model release.

---

## Repository engineering

- `engine.py` — inference engine
- `app.py` — Flask demo/API
- `serve.py` — production WSGI entry point
- `docker_entrypoint.py` — runtime artifact preflight for containers
- `artifacts/README.md` — trusted runtime-artifact contract
- `templates/` and `static/` — dashboard UI
- `tests/` — regression tests being expanded during the audit
- `.github/workflows/ci.yml` — automated regression CI on pushes and pull requests to `main`
- `AUDIT_NOTES.md` — initial technical audit findings
- `MILESTONES.md` — evidence-first progress tracker
- `REPRODUCIBILITY.md` — reproducibility and leakage protocol
- `ARTIFACT_MANIFEST_TEMPLATE.md` — immutable artifact/evidence manifest template
- `RELEASE_CHECKLIST.md` — release and public-claim gate
- `SECURITY.md` — serialized-artifact and deployment security policy
- `CONNECTOME_EDGE_RND.md` — experimental connectome-inspired Edge-AI research protocol and stop conditions

---

## Research direction

AB-GEN is not currently positioned as a replacement for state-of-the-art CNNs or Vision Transformers on raw accuracy alone. The research question is different:

> **How far can a geometric/spectral ensemble architecture go in computer vision while reducing computational cost and retaining a more inspectable decision pipeline?**

A second, explicitly experimental research line is now documented around **sparse, modular and connectome-inspired computation for Edge AI**. It is intentionally separated from the recovered historical baseline so new research cannot contaminate the reproducibility audit. Its first requirement is not biological plausibility but a controlled comparison against dense, random, degree-preserving and current AB-GEN baselines.

See **[CONNECTOME_EDGE_RND.md](CONNECTOME_EDGE_RND.md)** for hypotheses, controls, batch-invariance gates, metrics and stop conditions.

The next meaningful milestone is not a marketing number; it is a third party being able to reproduce the same result from a clean environment.

---

Built with Python, PyTorch, LightGBM, scikit-learn and Flask.
