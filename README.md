# AB-GEN — Geometric-Polynomial Vision Research

> **Hybrid geometric + spectral + polynomial ensemble for image classification**

AB-GEN is an experimental computer-vision architecture built around dimensional reduction, Fisher weighting, multi-scale spectral features, geometric class structure, an N1 learner ensemble and an N2 polynomial meta-learner.

The project is currently undergoing a reproducibility and engineering audit. Public claims are intentionally separated into **reported** and **reproduced/validated** results.

**Official research site:** https://msrobotikaabgenresearch.wordpress.com

## Validation status

- **CIFAR-10 V24 Slow Burn:** internal project records report **80.14% accuracy** and a recorded runtime of approximately **420 min**.
- **CIFAR-10 V23 M4 Purist:** internal project records report **78.05% accuracy**.
- **MNIST Universal V24:** internal project records report **97.79% accuracy**.
- Full reproduction from the original training source and artifacts is in progress.
- Previously published Green AI energy figures are being re-benchmarked under a controlled, reproducible measurement protocol.

Evidence and release gates:

- **[MILESTONES.md](MILESTONES.md)** — public evidence status and roadmap.
- **[REPRODUCIBILITY.md](REPRODUCIBILITY.md)** — minimum protocol for promoting a result from reported to reproduced/validated.
- **[ARTIFACT_MANIFEST_TEMPLATE.md](ARTIFACT_MANIFEST_TEMPLATE.md)** — source/artifact/environment/hash manifest template.
- **[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)** — pre-publication gate for releases, benchmark claims and public communications.
- **[SECURITY.md](SECURITY.md)** — trusted-artifact and serialized-model security boundary.

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

1. Recover and freeze **V24 Slow Burn** as the golden baseline.
2. Verify train/validation/test separation and rule out leakage.
3. Reproduce the reported **80.14% CIFAR-10** result from clean source.
4. Persist the exact preprocessing/PCA artifacts required for standalone inference.
5. Extend deterministic tests and CI beyond the first regression test.
6. Build a raw-image end-to-end inference path.
7. Evaluate calibration using ECE, Brier score, NLL and reliability diagrams.
8. Measure energy on identical hardware and inference boundaries against baselines.
9. Package reproducible releases with environment locks, hashes and benchmark metadata.

---

## Green AI benchmark status

Earlier project material reports approximately **0.31 mJ/inference** for AB-GEN and a large reduction relative to a ResNet-18 reference. These values are retained as **historical/reported project figures**, not as independently reproduced measurements.

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

---

## Research direction

AB-GEN is not currently positioned as a replacement for state-of-the-art CNNs or Vision Transformers on raw accuracy alone. The research question is different:

> **How far can a geometric/spectral ensemble architecture go in computer vision while reducing computational cost and retaining a more inspectable decision pipeline?**

The next meaningful milestone is not a marketing number; it is a third party being able to reproduce the same result from a clean environment.

---

Built with Python, PyTorch, LightGBM, scikit-learn and Flask.
