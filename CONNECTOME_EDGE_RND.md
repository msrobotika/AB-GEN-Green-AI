# AB-GEN Connectome Edge R&D

> Status: **future research / hypothesis-driven**. This track is deliberately separate from the historical AB-GEN baseline and must not be used to reinterpret or inflate existing performance claims.

## Why this track exists

AB-GEN is being investigated as a compact, local and inspectable Edge-AI architecture rather than as a small copy of a conventional large model. A new research question is whether selected principles from biological connectomes can produce useful computational structure under strict resource constraints.

The trigger for this line of work is the newly published complete male *Drosophila melanogaster* central nervous system connectome. Google Research reports more than 166,000 neurons and about 125 million synaptic connections; the associated Janelia/Cell publication reports 166,700 neurons and 11,710 neuron types spanning brain and nerve cord. The dataset is openly explorable/downloadable through the Male CNS project.

This does **not** mean that AB-GEN will attempt to copy or emulate an entire fly brain. The first goal is to test whether small, measurable topological motifs or architectural rules extracted from connectome data provide any advantage over matched artificial controls.

## Scientific precedent

This direction is not purely metaphorical. Prior peer-reviewed work has already shown that connectome-constrained, task-optimized neural models can be built from measured fly circuitry:

- Lappalainen et al. (Nature, 2024) built a differentiable model constrained by experimentally measured connectivity across 64 cell types in the fly visual system and optimized its free parameters for optic-flow estimation. The model reproduced known ON/OFF separation and direction-selective responses.
- NeuroMechFly v2 (Nature Methods, 2024) provides an embodied fly simulation and demonstrates closed-loop sensorimotor control, including use of a connectome-constrained visual network. The authors explicitly note the framework can support machine-learning controllers for autonomous artificial agents and robots.

These results establish that biological connectivity can be used as a computational constraint. They do not establish that connectome-derived architectures are generally superior to conventional networks.

## Core research hypothesis

The testable hypothesis is:

> A small, sparse, modular and recurrent graph derived from biological connectivity motifs may achieve competitive task performance with fewer trainable parameters, lower memory/energy cost, and stronger structural traceability than a matched dense baseline.

The null hypothesis must remain equally explicit:

> A degree-matched or randomly wired control performs as well as or better than the connectome-derived topology once parameter count, compute and training protocol are controlled.

If the null hypothesis wins, the biological topology is not useful for that task and should not be retained.

## Proposed architecture: Connectome-v0

Connectome-v0 should be deliberately small and edge-oriented.

### Inputs

Use frozen AB-GEN feature channels rather than raw-image end-to-end training in the first experiment:

- PCA/geometric features;
- spectral/FFT features;
- class-similarity or centroid-derived features;
- selected N1 expert scores where appropriate.

This keeps the first experiment focused on topology rather than mixing topology research with a new feature extractor.

### Graph

Start with 32–128 computational nodes, then scale to 256–512 only if justified.

Each node should have:

- a defined incoming neighborhood;
- sparse signed connections (excitatory/inhibitory interpretation where meaningful);
- a small state vector;
- optional recurrence;
- no hidden dependence on other samples in the batch.

The topology may be obtained from:

1. distilled motifs from connectome modules;
2. type-to-type connectivity statistics;
3. local recurrent motifs;
4. hub-and-spoke motifs;
5. feed-forward + feedback loops observed in sensory pathways.

The biological graph is a constraint or prior, not a sacred structure.

### Dynamics

The first implementation should favor deterministic, inexpensive dynamics:

- affine weighted aggregation;
- bounded nonlinearity;
- optional leaky state update;
- signed recurrent feedback;
- explicit gating;
- per-sample normalization only.

Avoid BatchNorm in v0. If normalization is required, prefer fixed scaling, LayerNorm/RMSNorm or another operation whose inference result does not change with batch composition.

### Output

Two first-use modes are worth testing separately:

1. **Classifier head** — graph outputs class logits directly.
2. **Expert router/gating head** — graph learns how to combine existing AB-GEN experts, turning the connectome layer into a sparse meta-controller rather than a full classifier.

The second option may fit AB-GEN particularly well because the existing architecture already contains specialized learners and a meta-learning stage.

## Required controls

No connectome result is meaningful without matched controls.

Every experiment should include:

- dense MLP with matched trainable parameter count;
- sparse random graph with matched node/edge count;
- degree-preserving shuffled graph;
- same topology with randomized edge signs;
- feed-forward-only ablation;
- recurrence-disabled ablation;
- current frozen AB-GEN baseline;
- compact CNN/TinyML baseline where the task permits.

Training data, split, augmentation, optimizer budget and evaluation protocol must be identical across comparable models.

## Batch-invariance gate

The Slow Burn audit exposed deterministic batch dependence in one historical inference path. Connectome-v0 must therefore include a hard invariance test from day one.

For the same sample, compare predictions/logits under:

- individual inference;
- batch sizes 2, 4, 8, 16, 32, 64;
- multiple positions inside the batch;
- different companion samples;
- repeated identical batches.

The default acceptance criterion should be exact class invariance and numerically bounded logit drift. Any context-dependent mechanism must be explicit and intentional, never an accidental consequence of batch processing.

## Metrics

Accuracy alone is insufficient. Record at minimum:

- top-1 accuracy;
- macro F1;
- confusion matrix;
- NLL, Brier score and ECE;
- parameter count;
- model size on disk;
- peak RAM/VRAM;
- MACs/FLOPs estimate where meaningful;
- p50/p95 latency;
- throughput;
- measured joules/inference under the existing Green AI protocol;
- batch-invariance score;
- perturbation/noise robustness;
- abstention/uncertainty performance if an uncertainty gate is used.

## Uncertainty as a first-class output

A useful Edge-AI system should not only classify; it should identify when its own decision is unstable.

A future AB-GEN Connectome module may emit:

- class prediction;
- confidence/calibration output;
- stability score;
- disagreement score between specialist modules;
- abstain / second-pass trigger.

This is a hypothesis to test, not a claimed capability.

## Research phases

### C0 — literature and data mapping

- identify accessible male/female connectome tables and licenses;
- select candidate motifs/modules;
- document graph statistics;
- define random and degree-preserving controls.

### C1 — synthetic topology benchmark

- implement small sparse recurrent graph engine;
- validate determinism and batch invariance;
- compare connectome-derived versus synthetic controls on frozen AB-GEN features.

### C2 — expert-routing experiment

- use graph as a meta-controller over N1/ensemble outputs;
- compare against polynomial Ridge N2 and matched MLP/router baselines.

### C3 — Edge benchmark

- export the best surviving candidate to CPU-only inference;
- benchmark latency, memory and energy on the same machine and protocol as controls;
- consider microcontroller/embedded targets only if the graph is sufficiently compact.

### C4 — vision-specific bio-inspired front end

Only if C1–C3 justify continuation, test visual-system motifs inspired by fly optic-lobe organization or connectome-constrained models such as FlyVis.

## Stop conditions

This line should be stopped or redesigned if:

- biological topology gives no reproducible advantage over matched random graphs;
- any gain disappears after leakage-free evaluation;
- parameter/energy cost is worse without compensating benefit;
- gains depend on test-set parameter selection;
- behavior is batch-unstable without an explicit intended contextual mechanism.

## Separation from historical AB-GEN

The historical recovery program remains the priority until Phase 1 closes:

- RAW → PCA provenance;
- exact Slow Burn historical path;
- independent leakage audit;
- controlled energy measurement;
- XAI fidelity validation.

Connectome R&D must live in separate code paths, artifacts, manifests and result tables. Historical models remain frozen.

## Primary references

- Google Research, **A connectomics milestone: Mapping the complete male fruit fly brain** (2026-09-03): https://www.research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/
- HHMI Janelia, **Male CNS Connectome Project**: https://male-cns.janelia.org/
- Berg et al., **Sexual dimorphism in the complete connectome of the Drosophila male central nervous system**, Cell (2026), DOI: https://doi.org/10.1016/j.cell.2026.08.015
- Lappalainen et al., **Connectome-constrained networks predict neural activity across the fly visual system**, Nature 634 (2024): https://doi.org/10.1038/s41586-024-07939-3
- FlyVis open-source implementation: https://github.com/TuragaLab/flyvis
- NeuroMechFly v2, **simulating embodied sensorimotor control in adult Drosophila**, Nature Methods (2024): https://doi.org/10.1038/s41592-024-02497-y

## Evidence rule

No statement that AB-GEN is "brain-like", "neuromorphic", "more efficient", "more intelligent" or "superior" should be promoted from hypothesis to result without a controlled experiment and archived evidence.
