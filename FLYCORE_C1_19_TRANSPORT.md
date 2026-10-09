# FlyCore C1.19 — KMNIST transport result

## Status

**C1.19: CLOSED PASS**

This document records the isolated Mosca-ABGEN / FlyCore research result. It is intentionally kept separate from the historical CIFAR-10 AB-GEN evidence states documented in the main README.

## Scientific question

C1.19 tested whether the **frozen RDE+FLE robustness predictor** that had been developed and prospectively confirmed on FashionMNIST would retain predictive advantage over the frozen RDE-only baseline after transport to **KMNIST**, without coefficient refitting.

The transport test reused the 16 independent C1.18 confirmation topology pairs / 32 topologies, the frozen five training seeds, the frozen node-damage and calibration protocol, and the frozen C1.18 B0/B1 coefficients. The intended scientific domain change was the dataset. The historical normalization was intentionally preserved.

## Frozen result

- Models: **160**
- Repeated cells: **3,200**
- Independent structural pairs: **16**
- B1 pair wins: **16/16**
- T_obs: **+0.002128195102507025**
- Exact one-sided sign-flip p-value: **1.52587890625e-05**
- Upper-tail assignments: **1 / 65,536**
- Refit after transport: **NO**
- Optional stopping: **NO**
- Decision: **PASS**

The last execution cell completed its full node-damage curve and passed empty-lesion parity before the aggregate test was computed.

## C1.18 precursor

The frozen FashionMNIST confirmation that preceded this transport test also closed PASS:

- Models: **160**
- Repeated cells: **3,200**
- B1 pair wins: **16/16**
- T_obs: **+0.00183018154748278**
- Exact p-value: **1.52587890625e-05**
- Upper tail: **1 / 65,536**

C1.18 is treated as immutable and is not refit or reinterpreted after observing C1.19.

## Recovery boundary

The original Dell failed before any C1.19 performance run had been produced. The execution implementation used for C1.19 was therefore reconstructed **before observing C1.19 performance** from project chats, frozen protocol anchors, and recovered artifacts.

It is **not claimed to be byte-identical** to the lost historical Python source.

Before execution, the reconstructed implementation was checked against historical invariants, including:

- FlyCore64 base topology: **462 edges**
- base-topology SHA-256: `74a2ead538af0d049c66894bff705eb69102386c8a71013c3189815370dd5234`
- C1.17B1 structural bank reproduced: **300 candidates → 63 eligible → identical 10 selected pairs**
- C1.18 confirmation structural bank reproduced: **400 candidates → 91 eligible → identical 16 selected pairs / 32 topologies**
- C1.19P historical freeze SHA-256: `9ddf3004bdebcbcfc60f392285292238a8449f038965c69e02353c39e3951b54`
- C1.19D recovery freeze SHA-256: `551bc7fdbfd4ac3cf587bdddc6abe5e79f7963992484104ff14bba83babdd548`
- KMNIST raw-tree SHA-256: `a7d658293ca6d229eb1336a6446ac0c8c0ca0d0ea167c3fd97143e7caf73f53d`
- damage SHA-256: `84e8fbf7bf545b4f81a1075e25e7c02f6156236d9f5e96313f4fa5815c657b9d`
- calibration SHA-256: `5472743a6c8bc2598aa247a14c3d345d4d971ce982b5a545a51d72f6b04f2d82`

## Allowed interpretation

Under the tested **FlyCore64 + node-lesion** protocol, the frozen **RDE+FLE** predictor retained lower pair-level prediction error than the frozen **RDE-only** baseline after transport from FashionMNIST to KMNIST, with all 16 independent structural pairs favoring the augmented predictor.

This is evidence of **cross-dataset transport within the tested architecture and protocol**.

## What this does not establish

This result does **not** establish:

- universality of FLE;
- biological equivalence to a fly connectome;
- causality of FLE;
- transport to arbitrary architectures, datasets, or damage mechanisms;
- superior raw classification accuracy;
- Edge-AI efficiency or energy superiority.

The next scientific step should be a separately frozen stress test designed to challenge the transported effect rather than optimize around this PASS.
