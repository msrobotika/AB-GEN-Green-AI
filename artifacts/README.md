# Runtime artifacts

This directory is a **local mount point only**. Runtime model/data files are intentionally excluded from Git.

A validated Docker run currently expects these trusted files:

- `abgen_bundle.pkl` — serialized AB-GEN inference bundle;
- `sample_data.pkl` — cached demo sample/PCA data;
- `training_module.py` — serialization-compatibility module containing the exact trusted class definitions required by the validated bundle.

The exact filenames may be replaced by environment variables:

- `ABGEN_BUNDLE_PATH`
- `ABGEN_SAMPLE_DATA_PATH`
- `ABGEN_TRAINING_MODULE_PATH`

## Security boundary

Python pickle/joblib artifacts can execute code while loading. Never place third-party or unverified artifacts here. A validated release must record SHA-256 hashes and provenance before these files are accepted for runtime use.

See `SECURITY.md`, `REPRODUCIBILITY.md` and `ARTIFACT_MANIFEST_TEMPLATE.md`.

## Current status

The public repository does not yet distribute the validated V24 Slow Burn runtime artifact set. Until that evidence package exists, the Docker container is expected to fail its runtime preflight with a clear error rather than silently guessing or downloading artifacts.
