# FlyCore C1.20P — Stage10 selection-spec closure

## Status

**C1.20P Stage10: CLOSED PASS — RECONSTRUCTED SELECTION SPEC FROZEN**

Parent Stage9 freeze:

`8392f40d25e3745da8fef26403916f05e765f2053bad19331b7d6c570688e165`

Stage10 freeze:

`0853fc59b137b98b78d489bd95996c7040ae4509c2c5c46525d6119b43b7574f`

## Frozen reconstructed selection rule

- RDE: `(1-route_top3_share)/mean_distance`
- minimum delta-RDE: **0.015**
- exact pair stratum:
  - `global_vertex_cut`
  - `global_edge_cut`
  - `node_connectivity_mean`
- maximum absolute changed-fraction difference: **0.020000**
- LOW/HIGH assignment: by RDE only
- eligible-pair ordering:
  1. abs delta changed fraction ascending
  2. delta-RDE descending
  3. LOW seed ascending
  4. HIGH seed ascending
- greedy topology uniqueness: **required**
- maximum accepted pairs per exact stratum: **2**

## Historical replay target

- seeds: `1820000..1820399`
- candidates: **400**
- eligible pairs: **91**
- selected pairs: **16**
- selected topologies: **32**

## Boundaries

- training: **NONE**
- performance: **NONE**
- topology generation: **NONE**

## Next gate

Before executing the historical replay, Stage11A must bind the surviving implementation dependencies used to reconstruct topology edges and compute the structural metrics.

The recovered C1.18 runner calls the historical structural metrics API through `a5b.metrics_for(...)` and `a5b.summary_row(...)`. Stage11A must identify the exact local module/source for this API, hash it, and freeze the relevant source windows together with the recovered topology primitives.

Only then may Stage11B generate `182xxxx` candidates.
