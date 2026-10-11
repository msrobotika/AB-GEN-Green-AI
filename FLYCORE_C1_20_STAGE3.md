# FlyCore C1.20P — Stage3 deep provenance closure

## Status

**C1.20P Stage3: CLOSED PASS — READ-ONLY DEEP PROVENANCE**

No training, performance execution, topology generation, project-code execution, or persistent archive extraction occurred.

## Parent freeze

- C1.20P Stage2 freeze SHA-256: `672e96b10573e2b1b7dae50fc722f49b252b5339a0a67c257c72ce8059cf62d0`

## Verified Stage3 result

- Stage3 freeze SHA-256: `54f9c3439be006a03643453afdc40ec18dce96c283763e989b4dc2f51e4f8bff`
- loose source hits: **394**
- ZIP archives inspected: **2**
- ZIP source hits: **9**
- known hash hits: **2**
- training: **NONE**
- performance: **NONE**
- topology generation: **NONE**
- project-code execution: **NONE**
- archive extraction: **NONE**

The generated verify-only procedure returned PASS with the same freeze SHA.

## Key provenance finding

The recovered archive:

`00_Backup_Drive/RECOVERED_DRIVE_2026-10-01/c1_18p_stage0_v1.zip`

contains a dedicated C1.18P preflight/builder package. The highest-value entries are:

- `c1_18p_derive_dev_builder.py`
  - SHA-256: `d47fe09e3e23cdad4cf047ed4ccb2945cba3fd81e9fb32630ea0cfe00ac0db4f`
  - evidence includes `DEV_CANDIDATE_COUNT = 400`, `MIN_DELTA_RDE = 0.015`, and delta-RDE selection material.
- `c1_18p_spec.py`
  - SHA-256: `fcfd0a4809374c634891f5a3e0e1a085c63533b4e56f0a0679c6cfe8015695d3`
  - binds `topology_seed_start = 1820000` and `topology_seed_end = 1820399`.
- `c1_18p_verify_derived_builder.py`
  - SHA-256: `1bb0857c1ff4ebe3315dfde62a187ee86bee55a22fe83699214e413ee76e13c8`
  - requires `candidate_count == 400` and requires the builder text to retain `MIN_DELTA_RDE = 0.015`.

The archive also contains the rest of the C1.18P Stage0 preflight package, including preflight, source probe, damage sets, functional importance, selftest and verify-only files.

## Interpretation

This is the strongest provenance lead found so far for the C1.18 confirmation structural-bank construction path.

However, Stage3 only searched and hashed archive entries. It does not yet prove that `c1_18p_derive_dev_builder.py` implements all of:

1. candidate topology generation;
2. structural eligibility;
3. LOW/HIGH pairing;
4. delta-RDE threshold/order;
5. final 16-pair confirmation selection.

Nor does Stage3 establish whether the builder is exact historical source, an approved derived builder, or a later reconstruction. That distinction must be resolved from the full source bodies and their self-description/provenance metadata.

## Next gate

Stage4 must inspect the full source text of the three builder/spec/verifier entries directly from the frozen ZIP stream, bind their entry hashes, extract function/class declarations and source-body provenance statements, and map each required structural step to concrete source lines.

No project code execution and no C1.20 candidate generation are authorized at Stage4.
