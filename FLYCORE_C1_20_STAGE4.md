# FlyCore C1.20P — Stage4 ZIP builder audit closure

## Status

**C1.20P Stage4: CLOSED PASS — READ-ONLY SOURCE AUDIT**

No training, performance execution, topology generation, project-code execution, or executable extraction occurred.

## Parent freeze

- C1.20P Stage3 freeze SHA-256: `54f9c3439be006a03643453afdc40ec18dce96c283763e989b4dc2f51e4f8bff`

## Verified Stage4 result

- Stage4 freeze SHA-256: `6fc6136bb9e937e5acbfb781740b401d6a77c8a94001d105814ec071e4215f6a`
- archive SHA-256: `a7d1f38eb0997e7062302f719243cbaaa8587e9f0bd6ed59f18f1345b85a973b`
- entries audited: **6**
- declarations extracted: **29**
- context rows: **337**
- training: **NONE**
- performance: **NONE**
- topology generation: **NONE**
- project-code execution: **NONE**
- executable extraction: **NONE**

The generated verify-only procedure returned PASS with the same Stage4 freeze SHA.

## Provenance finding

The audited archive package is not evidence of an exact historical C1.18 builder.

`c1_18p_derive_dev_builder.py` explicitly identifies itself as a **C1.18P DEVELOPMENT structural-bank deriver** that creates a **new** development bank builder by mechanically transforming the exact historical C1.17B1 source. It requires the historical source hash:

`732b7a6b3f8a7fa208daf0bcb4904a62f9ef338385adeb811fa9af677afee463`

for `c1_17b1_independent_bank.py`.

The deriver records status `DERIVED_BUILDER_CREATED_NOT_EXECUTED`, preserving the distinction between the historical B1 source and the newly derived development builder.

## Structural locks inherited from historical B1

The source-body audit shows the derivation preserves/locks:

- historical seed namespace `950100..950399` as the source pattern;
- `MIN_DELTA_RDE = 0.015`;
- RDE formula `(1-route_top3_share)/mean_distance`;
- route HHI not used for pair selection;
- structural pair-selection logic involving low/high RDE, delta-RDE, selected pairs, and seed identities;
- network training declared absent from the structural-bank source.

The development derivation changes only explicitly recognized constants/cardinalities and namespaces, including:

- `950100..950399` → `1810000..1810399`;
- 300 candidates → 400 candidates;
- 10 pairs → 12 pairs;
- 20 variants → 24 variants.

## Scientific specification

`c1_18p_spec.py` separately freezes:

### Development
- topology seeds: `1810000..1810399`
- target pairs: **12**
- target topologies: **24**

### Confirmation
- topology seeds: `1820000..1820399`
- target pairs: **16**
- target topologies: **32**
- training seeds: `1821001..1821005`
- damage seeds: `1822001..1822004`
- calibration seed: `1823001`

Therefore the development derivation script must not be mislabeled as the confirmation builder.

## Decision

The surviving package proves a chain of provenance back to the exact historical C1.17B1 source hash, but Stage4 does **not** locate that historical source body itself and does **not** locate a confirmation-specific builder transforming the development logic to the 182xxxx / 16-pair bank.

The next provenance gate must search every relevant loose file and archive entry for:

1. exact historical B1 SHA-256 `732b7a6b...`;
2. filename/content `c1_17b1_independent_bank.py`;
3. derived development builder `c1_18p_dev_bank.py` and its derivation manifest;
4. confirmation-specific builder/source for `1820000..1820399`, 16 pairs / 32 topologies;
5. any archive entry whose exact SHA matches the frozen historical B1/B2/B3 anchors.

Until that search is complete, C1.20 candidate generation remains unauthorized.
