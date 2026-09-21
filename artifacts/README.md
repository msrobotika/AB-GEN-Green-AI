# Runtime artifacts

This directory is a **local mount point only**. Runtime model/data files are intentionally excluded from Git.

A validated Docker run expects these trusted files:

- `abgen_bundle.pkl` — serialized recovered inference bundle;
- `sample_data.pkl` — cached demo sample/PCA data;
- `training_module.py` — serialization-compatibility module with the exact trusted class definitions required by the bundle;
- `runtime-manifest.json` — trusted manifest containing the accepted filename, size and SHA-256 for the three runtime artifacts.

Default environment variables:

- `ABGEN_BUNDLE_PATH=/artifacts/abgen_bundle.pkl`
- `ABGEN_SAMPLE_DATA_PATH=/artifacts/sample_data.pkl`
- `ABGEN_TRAINING_MODULE_PATH=/artifacts/training_module.py`
- `ABGEN_ARTIFACT_MANIFEST_PATH=/artifacts/runtime-manifest.json`
- `ABGEN_REQUIRE_MANIFEST=1`

## Create a candidate manifest

From a trusted artifact set:

```bash
python tools/artifact_manifest.py create \
  --artifact model_bundle=artifacts/abgen_bundle.pkl \
  --artifact sample_data=artifacts/sample_data.pkl \
  --artifact training_module=artifacts/training_module.py \
  --output artifacts/runtime-manifest.json
```

On Windows `cmd.exe`, place the command on one line or use the appropriate line-continuation syntax.

## Security boundary

Python pickle/joblib artifacts can execute code while loading. The container now verifies the artifact bytes against the supplied manifest **before** `joblib.load()` is reached.

That check provides integrity, not automatic trust. A malicious artifact plus a malicious manifest still passes a hash comparison. Therefore:

1. the manifest itself must come from a trusted evidence/release package;
2. the accepted manifest should be bound to an immutable commit/release;
3. third-party or unverifiable serialized artifacts must never be loaded;
4. a hash mismatch causes container startup to fail closed.

`ABGEN_REQUIRE_MANIFEST=0` exists only for explicit local forensic/debug work. It must not be used for a validated release.

See `SECURITY.md`, `REPRODUCIBILITY.md`, `ARTIFACT_MANIFEST_TEMPLATE.md` and issue #21.

## Current status

The public repository does not distribute a validated V24 Slow Burn runtime artifact set. Until an accepted trusted manifest and artifact package exist, a public clone is not a standalone reproducible model release.
