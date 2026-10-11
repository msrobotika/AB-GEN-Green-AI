# FlyCore C1.20P — Stage5 exact-source search closure

## Status

**C1.20P Stage5: CLOSED PASS — READ-ONLY EXACT-SOURCE SEARCH**

No training, performance execution, topology generation, project-code execution, or archive extraction occurred.

## Parent freeze

- C1.20P Stage4 freeze SHA-256: `6fc6136bb9e937e5acbfb781740b401d6a77c8a94001d105814ec071e4215f6a`

## Verified Stage5 result

- Stage5 freeze SHA-256: `2f71069a037ba10a495ed00ffcf9e302fb6d491c8cf530a77db84c82c3d79b70`
- loose files scanned: **27**
- ZIP archives inspected: **1**
- ZIP entries hashed: **12**
- loose exact hash hits: **0**
- ZIP exact hash hits: **0**
- loose text hits: **13**
- ZIP text hits: **11**
- training: **NONE**
- performance: **NONE**
- topology generation: **NONE**
- project-code execution: **NONE**
- archive extraction: **NONE**

The generated verify-only procedure returned PASS with the same Stage5 freeze SHA.

## Exact-source conclusion

No exact local or ZIP-entry hash match was found for the Stage5 historical anchors, including the exact C1.17B1 source SHA:

`732b7a6b3f8a7fa208daf0bcb4904a62f9ef338385adeb811fa9af677afee463`

Therefore Stage5 does **not** recover the exact historical B1 source body.

The surviving C1.18P Stage0 archive continues to preserve the B1 expected hash and the derivation chain, but not the exact source file itself.

## New high-value confirmation anchors

The recovered C1.19 recovery evidence records additional frozen C1.18 confirmation hashes that were not used as exact Stage5 search anchors:

- confirmation calibration SHA-256:
  `5472743a6c8bc2598aa247a14c3d345d4d971ce982b5a545a51d72f6b04f2d82`
- confirmation damage SHA-256:
  `84e8fbf7bf545b4f81a1075e25e7c02f6156236d9f5e96313f4fa5815c657b9d`
- confirmation selection SHA-256:
  `ef653f07d1d712c70c789b2f93be08dd552d4fb37698a47374db13a1f81a300a`

These are now priority provenance anchors because they may recover the original confirmation selection/damage/calibration artifacts even if the historical builder source is absent.

## Coverage caveat

Stage3 reported two ZIP archives, while Stage5 inspected one ZIP due its restricted search roots. Therefore exact-source absence is not yet exhaustive over the entire `C:\ABGEN` tree.

## Decision

Do not claim the historical builder source is absent globally yet.

Stage6 must perform an exhaustive SHA-only search across **all files and all ZIP entries under C:\ABGEN**, without extension/name filtering, for:

- C1.17B1/B2/B3 historical source anchors;
- C1.17B1 canonical selection / B2 freeze / B3 summary;
- C1.18 confirmation selection/calibration/damage anchors.

Only after that exhaustive search can the project close the historical-source recovery boundary and, if needed, move to an explicitly recovered/reconstructed C1.20 structural builder.
