# FlyCore C1.20P — Stage8 selection-logic evidence closure

## Status

**C1.20P Stage8: CLOSED PASS — READ-ONLY SOURCE-EVIDENCE EXTRACTION**

No training, performance execution, topology generation, project-code execution, or archive extraction occurred.

## Parent freeze

- Stage7 freeze SHA-256:
  `7ad3b78dd9206c9808bcaf8824a3ae87dd4d282e62c8cd8eb0268091b32d7efb`

## Stage8 freeze

- Stage8 freeze SHA-256:
  `1527ed75f93e660fd7112d79f20dab4f99501071c98a3e6731387427d4b77b85`

## Coverage

- evidence sources: **202**
- evidence rows: **1429**
- ZIP archives inspected: **2**
- training: **NONE**
- performance: **NONE**
- topology generation: **NONE**
- project-code execution: **NONE**
- archive extraction: **NONE**

## Source-supported structural facts

Stage8 preserves source evidence for:

- `MIN_DELTA_RDE = 0.015`
- RDE formula:
  `(1-route_top3_share)/mean_distance`
- `route_hhi` is **not** used to choose pairs
- structural selection logic references:
  - `node_connectivity_mean`
  - `high["rde"]`
  - `low["rde"]`
- historical B1 source name:
  `c1_17b1_independent_bank.py`
- historical B1 expected SHA-256:
  `732b7a6b3f8a7fa208daf0bcb4904a62f9ef338385adeb811fa9af677afee463`

The C1.18 development deriver mechanically preserved the historical B1 selection semantics while changing seed namespace/cardinality parameters.

## Remaining gap

Stage8 does **not yet prove the complete exact ordering and construction rule** that maps structural candidates into eligible LOW/HIGH pairs and then into the final selected-pair list.

In particular, the surviving evidence exposes the relevant field names and thresholds but not yet the complete historical expression/order governing:

1. grouping/filtering by structural compatibility;
2. LOW versus HIGH assignment;
3. eligible-pair ordering;
4. final pair selection/truncation.

These details must not be inferred from the 16 recovered selected outcomes alone.

## Next gate

Stage9 must audit the full source text of `c1_18p_derive_dev_builder.py`, especially its AST transformer and required-pattern assertions, to determine exactly what parts of the historical B1 logic were recognized and preserved.

C1.20 `1830000..1830399` topology generation remains unauthorized.
