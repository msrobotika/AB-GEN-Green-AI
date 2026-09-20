# AB-GEN Green AI Benchmark Protocol

This document defines the minimum controlled procedure required before AB-GEN publishes measured efficiency or energy-saving claims against another model.

## 1. Purpose

The benchmark must answer two distinct questions:

1. How much compute, latency, memory and energy does the **model-only** inference path require?
2. How much compute, latency, memory and energy does the **complete usable pipeline** require from accepted input to returned prediction?

These boundaries must never be mixed in the same comparison.

## 2. Publication rule

No percentage saving, Green AI superiority claim or joules-per-image comparison is considered validated unless AB-GEN and every baseline are measured:

- on the same physical machine;
- under the same power/performance policy;
- with the same dataset subset and input ordering;
- at the same numerical precision where practical;
- with the same measurement boundary;
- after equivalent warm-up;
- using repeated runs;
- with all raw measurements retained.

Historical project energy constants are reference values only and are not benchmark evidence.

## 3. Hardware and environment freeze

Record before each benchmark campaign:

- machine/manufacturer and model;
- CPU model, core/thread count and relevant power limits;
- GPU model, VRAM and configured power limit;
- total system RAM;
- storage type where preprocessing or model loading is measured;
- operating system and version;
- BIOS/firmware version when material;
- CPU governor/power mode;
- GPU driver and CUDA/runtime versions where applicable;
- Python version;
- package lock/export;
- Git commit/tag for AB-GEN and each baseline wrapper;
- SHA-256 for model and preprocessing artifacts.

Do not compare results from different machines as though they were a controlled head-to-head benchmark.

## 4. Dataset and input set

Use a frozen benchmark input manifest containing:

- dataset name/version;
- exact split;
- sample identifiers or deterministic indices;
- sample count;
- class distribution;
- checksum/hash where practical;
- preprocessing configuration.

The exact same input set must be presented to AB-GEN and every baseline.

## 5. Measurement boundaries

### Boundary A — model-only

Start timing/energy measurement after the model-ready tensor/vector has been produced and end immediately after prediction scores/labels are returned.

Report any model-specific preprocessing excluded from this boundary.

### Boundary B — end-to-end

Start from the common external input representation (for example RGB image bytes/array) and include:

- decoding/conversion;
- resize/normalization;
- PCA or other embedding;
- feature construction;
- model inference;
- post-processing required to produce the returned class/scores.

End-to-end comparison is the preferred boundary for product claims because it reflects actual deployment cost.

### Boundary C — cold start (optional, separate)

Measure process/model startup and artifact loading separately. Never mix cold-start cost into steady-state inference figures unless explicitly labelled.

## 6. Warm-up

Before measured steady-state runs:

- load all runtime artifacts;
- execute at least 20 inference batches or enough iterations to stabilize runtime;
- discard warm-up timing and energy;
- verify no first-run compilation/cache behavior remains in measured iterations.

If a backend uses JIT/graph compilation, document the compilation behavior explicitly.

## 7. Batch-size matrix

At minimum benchmark:

- batch 1 — interactive/edge latency;
- batch 8;
- batch 32;
- the largest practical production batch that fits all compared systems without changing the benchmark meaning.

If a baseline cannot execute a selected batch, report that fact rather than silently changing the comparison.

## 8. Repetitions

For each model, boundary, device mode and batch size:

- run at least 10 measured repetitions after warm-up;
- use the same number of samples per repetition;
- randomize or alternate model execution order where thermal drift could bias one model;
- allow hardware to return to a documented thermal/idle condition when needed;
- retain per-run raw values.

For the final publication benchmark, 30 repetitions are preferred when measurement cost is reasonable.

## 9. Timing metrics

Record at least:

- total wall-clock time;
- latency per batch;
- latency per image;
- throughput in images/second;
- median;
- arithmetic mean;
- standard deviation;
- p95 latency where enough observations exist.

GPU measurements must synchronize the device before stopping the timer.

## 10. Energy measurement

Preferred evidence hierarchy:

1. calibrated external wall-power meter for full-system energy;
2. platform-native energy counters such as Intel RAPL for CPU/package domains;
3. NVML/device energy or sufficiently frequent power sampling for NVIDIA GPU domains;
4. software estimators such as CodeCarbon only as supplemental estimates, not as substitutes for direct energy evidence.

For sampled power, document:

- source/tool;
- sampling interval;
- timestamp synchronization method;
- integration method used to obtain joules.

Report joules directly. Watts alone are not an energy metric.

## 11. Energy metrics

For each measured run derive:

- total joules;
- joules/image;
- joules/batch;
- images/joule;
- mean and standard deviation across runs.

A percentage saving against baseline B may only be calculated after both systems have valid values under the same boundary:

`energy_saving_pct = (J_baseline - J_abgen) / J_baseline * 100`

Always publish the absolute joules values next to the percentage.

## 12. Memory and artifact footprint

Record:

- peak process RAM;
- peak GPU VRAM when applicable;
- serialized model size;
- total runtime artifact size;
- optional container/image size when discussing deployment footprint.

Do not call file size a memory measurement.

## 13. Accuracy parity

Efficiency comparisons must publish task performance from the same frozen evaluation protocol alongside efficiency metrics.

At minimum include:

- accuracy;
- macro F1 where relevant;
- sample count;
- dataset/split;
- model/version.

A faster or lower-energy system with materially different predictive performance must not be presented as an equal-performance comparison without stating the difference.

## 14. Baselines

Initial CIFAR-10 benchmark targets should include at least:

- AB-GEN frozen golden baseline;
- ResNet-18 using a documented implementation/checkpoint;
- one additional lightweight/edge-oriented baseline when practical.

Each baseline must have its source, weights/checkpoint provenance, preprocessing and accuracy documented.

## 15. CPU and GPU separation

Do not mix CPU AB-GEN values with GPU baseline values under a single unlabeled comparison.

Publish separate tables for:

- CPU-only;
- GPU-enabled;
- optional heterogeneous/accelerated deployment.

Cross-device comparisons may be useful commercially but must be labelled as system-level comparisons rather than architectural energy efficiency in isolation.

## 16. Thermal and background-load control

Before final runs:

- close unnecessary applications/services where practical;
- record background-load policy;
- monitor CPU/GPU temperature where available;
- avoid one model consistently running only after the machine has heated from another;
- record plugged-in/battery state and power profile on laptops.

If the machine cannot be controlled well enough, mark the result exploratory rather than validated.

## 17. Raw evidence package

A publishable benchmark must preserve:

- environment manifest;
- hardware manifest;
- source commits/tags;
- artifact hashes;
- frozen input manifest;
- raw timing measurements;
- raw power/energy measurements;
- calculation script/version;
- summarized statistics;
- benchmark command(s);
- failures/exclusions with reasons.

Raw measurements should be retained in machine-readable CSV/JSON form.

## 18. Carbon reporting

Carbon is derived after energy has been measured.

When reporting CO2e, record:

- measured kWh basis;
- grid-intensity source;
- geographic region;
- intensity value and units;
- timestamp/date of the factor;
- whether the factor is average, marginal or another methodology.

Do not imply that a generic grid factor was directly measured by the benchmark.

## 19. Acceptance gate for a validated Green AI claim

All of the following must be true:

- AB-GEN baseline has already passed its reproducibility gate;
- compared model/version and checkpoint are frozen;
- same hardware and measurement boundary are used;
- input set is identical;
- warm-up and repetitions are documented;
- raw evidence is retained;
- accuracy/task performance is reported beside energy;
- uncertainty/spread is reported;
- absolute joules values are published;
- any percentage saving is calculated from those measured values;
- another person can repeat the procedure from the documented package.

If any gate fails, the result remains exploratory/reported and must not be promoted as a validated Green AI claim.

## 20. AB-GEN benchmark sequence

The recommended order is:

1. recover and freeze V24 Slow Burn;
2. reproduce the reported CIFAR-10 accuracy from frozen source/artifacts;
3. establish deterministic raw-image end-to-end inference;
4. freeze the benchmark machine/environment;
5. reproduce baseline-model accuracy;
6. run latency/throughput/memory measurements;
7. run direct energy measurements;
8. analyze uncertainty and parity;
9. package raw evidence;
10. only then publish Green AI conclusions.
