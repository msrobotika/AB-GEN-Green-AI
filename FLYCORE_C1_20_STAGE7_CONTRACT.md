# FlyCore C1.20P — Stage7 reconstruction contract

## Status

**PREPARED — NO TOPOLOGY GENERATION AUTHORIZED**

Parent Stage6 freeze:

`0dafe2936e73bc8df38e46c176a6f0346f2b0005d56c37f6e938151ce78bcd75`

Stage6 closed byte-exact recovery for the nine pinned historical/confirmation anchors in the current C:\ABGEN evidence tree.

## Provenance status

The exact historical C1.18 structural-bank source is **not byte-identically available**.

Any builder used from this point must be labeled:

**RECOVERED / RECONSTRUCTED IMPLEMENTATION**

It must never be described as the exact historical source.

## Surviving recovered evidence

- recovery runner SHA-256:
  `5522b3cc5a49aec7bd53282f1a54b2bc97f0194f9221124fbe7f664290d41929`
- recovery evidence SHA-256:
  `28d7b81ebeada8a78a0024a318d0e8f74595e0fa5cb695e99cb5fc95ec0ec1bd`
- recovered selected-pairs SHA-256:
  `02a44ac1e21a14d1c64f2470f21f35cb8d70b7c32ff4acd0e4f9075d1c2df76b`
- base topology SHA-256:
  `74a2ead538af0d049c66894bff705eb69102386c8a71013c3189815370dd5234`
- historical C1.17B1 expected source SHA-256:
  `732b7a6b3f8a7fa208daf0bcb4904a62f9ef338385adeb811fa9af677afee463`
- historical C1.18 confirmation-selection expected SHA-256:
  `ef653f07d1d712c70c789b2f93be08dd552d4fb37698a47374db13a1f81a300a`

## Mandatory historical replay gate

Before any C1.20 183xxxx topology generation, a reconstructed structural builder must reproduce the frozen C1.18 confirmation structural bank:

- topology seed range: **1820000..1820399**
- candidate count: **400**
- eligible-pair count: **91**
- selected pairs: **16**
- selected topologies: **32**
- minimum delta-RDE: **0.015**
- exact 16-pair delta-RDE sequence: **required**
- exact recovered 32 topology seed identities: **required**
- exact recovered 32 topology SHA-256 values: **required**

## Structural semantic locks

- RDE formula: `(1-route_top3_share)/mean_distance`
- route HHI used for pair selection: **NO**
- performance used for topology eligibility/selection: **NO**
- FLE used for topology eligibility/selection: **NO**
- KMNIST used for topology eligibility/selection: **NO**
- network training used for topology eligibility/selection: **NO**

## C1.20 future namespace

Only after the historical replay gate passes:

- topology seeds: **1830000..1830399**
- exactly **400** candidate seeds
- target: **16 pairs / 32 topologies**
- if fewer than 16 valid pairs: **INVALID / INSUFFICIENT**
- no range extension
- no reseeding
- no performance-driven rescue

## Boundary

At Stage7 preparation:

- training: **NONE**
- performance: **NONE**
- topology generation: **NONE**
- C1.20 scientific execution authorization: **NO**
