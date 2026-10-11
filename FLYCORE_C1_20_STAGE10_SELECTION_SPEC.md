# FlyCore C1.20P — Stage10 reconstructed structural-selection specification

## Status

**PREPARED FROM HISTORICAL MASTER EVIDENCE — NO C1.20 TOPOLOGY GENERATION**

Parent Stage9 freeze:

`8392f40d25e3745da8fef26403916f05e765f2053bad19331b7d6c570688e165`

## Provenance chain

The exact historical `c1_17b1_independent_bank.py` source is not byte-identically available.

However, the surviving project evidence establishes:

1. the C1.18 deriver was mechanically generated from the exact historical C1.17B1 source SHA-256
   `732b7a6b3f8a7fa208daf0bcb4904a62f9ef338385adeb811fa9af677afee463`;
2. the deriver preserved B1 structural-selection semantics while changing only authorized seed/cardinality constants;
3. the canonical MASTER preserves the full predecessor C1.16 pair-selection preregistration;
4. the project history records C1.17B1 as reusing that same structural eligibility/pairing logic with new seeds.

Therefore the following selection rule is frozen as a **RECOVERED/RECONSTRUCTED specification**, not as byte-identical historical source code.

## Candidate bank

For a bank with fixed seed range:

- generate exactly one structural candidate per topology seed;
- structural generation only;
- no dataset, forward pass, training, FLE, damaged performance, or accuracy may enter selection.

Historical confirmation replay:

- seeds: `1820000..1820399`
- candidate count: **400**

Future C1.20 bank, only after replay PASS:

- seeds: `1830000..1830399`
- candidate count: **400**

## Pair eligibility

For every unordered pair of distinct candidates, assign:

- **LOW** = lower RDE candidate;
- **HIGH** = higher RDE candidate.

A pair is eligible only if all conditions hold:

1. `global_vertex_cut` matches exactly;
2. `global_edge_cut` matches exactly;
3. `node_connectivity_mean` matches exactly;
4. `abs(changed_fraction_HIGH - changed_fraction_LOW) <= 0.020000`;
5. `RDE_HIGH - RDE_LOW >= 0.015000`.

RDE is frozen as:

`RDE = (1 - route_top3_share) / mean_distance`

`route_hhi` is not used for pair selection.

## Deterministic ordering

For every eligible pair compute:

- `abs_delta_changed_fraction = abs(changed_fraction_HIGH - changed_fraction_LOW)`
- `delta_RDE = RDE_HIGH - RDE_LOW`

Sort all eligible pairs by:

1. `abs_delta_changed_fraction` ascending;
2. `delta_RDE` descending;
3. `LOW_seed` ascending;
4. `HIGH_seed` ascending.

## Greedy selection

Traverse that sorted list and accept a pair only if:

- neither topology has already been selected;
- the exact stratum
  `(global_vertex_cut, global_edge_cut, node_connectivity_mean)`
  has fewer than **2** previously accepted pairs.

Continue greedily until the target pair count is reached.

No topology may appear in more than one selected pair.

## Historical target cardinalities

C1.17B1:

- 300 candidates
- 63 eligible pairs
- target 10 pairs / 20 topologies

C1.18 confirmation replay:

- 400 candidates
- 91 eligible pairs
- target 16 pairs / 32 topologies

## Replay gate

Before any C1.20 `183xxxx` generation, the reconstructed builder must reproduce the frozen C1.18 confirmation bank exactly:

- candidate count = 400
- eligible pair count = 91
- selected pair count = 16
- selected topology count = 32
- exact 16 delta-RDE values
- exact 32 low/high seed identities
- exact 32 topology SHA-256 values

Any mismatch means **RECONSTRUCTION FAIL / NOT AUTHORIZED**.

No threshold relaxation, range extension, reseeding, hand-picking, or performance-based rescue is permitted.

## Boundary

At Stage10 specification freeze:

- training: **NONE**
- performance: **NONE**
- C1.20 topology generation: **NONE**
- historical replay execution: **NOT YET**
