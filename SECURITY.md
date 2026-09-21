# Security Policy

AB-GEN is a research/demo repository undergoing reproducibility and engineering hardening. It is not represented as a security-audited production product.

## Serialized model/data artifacts

AB-GEN uses Python serialization (`joblib` / pickle-compatible artifacts) for recovered runtime bundles. These formats are **trusted-code artifacts**, not safe interchange formats.

**Never load a `.pkl`, joblib bundle or compatibility module obtained from an untrusted or unverifiable source.** Malicious serialized objects or imported Python modules can execute arbitrary code.

## Runtime integrity preflight

The Docker diagnostic runtime now requires a `runtime-manifest.json` by default and verifies filename, size and SHA-256 for:

- `abgen_bundle.pkl`;
- `sample_data.pkl`;
- `training_module.py`.

Verification happens in `docker_entrypoint.py` before `serve.py` starts and therefore before the bundle reaches `joblib.load()`.

This improves **integrity checking**, but it does not create trust by itself. A malicious artifact and malicious matching manifest still pass a hash comparison. A validated release must therefore bind the accepted manifest to a trusted immutable release/commit/evidence package.

`ABGEN_REQUIRE_MANIFEST=0` is for explicit local forensic/debug work only and must not be used as a validated deployment mode.

See also:
- `artifacts/README.md`;
- `REPRODUCIBILITY.md`;
- `ARTIFACT_MANIFEST_TEMPLATE.md`;
- `RELEASE_CHECKLIST.md`;
- issue #21.

## Compatibility-module boundary

Legacy bundles may require Python class definitions from `training_module.py`. In validated container execution this path is explicit through `ABGEN_TRAINING_MODULE_PATH` and covered by the runtime manifest.

The source engine retains a parent-folder compatibility search only for historical local-layout recovery. When that fallback is used it emits a warning. It must not be treated as a validated deployment path.

## Secrets and private material

Do not commit:
- API keys, passwords, access tokens or private certificates;
- proprietary customer datasets;
- private training artifacts intended to remain confidential;
- credentials embedded in notebooks, configuration or logs;
- customer-identifying production data;
- local absolute paths that expose private workstation structure when not required as evidence.

Use environment variables or an appropriate secret-management mechanism for deployment credentials.

## Dependency and deployment security

- Reproducible releases require frozen/tested dependency versions rather than arbitrary future package versions.
- Treat environment locks and artifact manifests as release evidence.
- Keep services behind appropriate network controls when exposed outside localhost.
- Never expose Flask development/debug mode to untrusted networks.
- Run containers as an unprivileged user.
- Keep runtime artifacts mounted read-only.
- GPU/container-toolkit configuration must be explicit and independently documented when used.
- `pip check` and source compilation are part of repository CI, but do not replace dependency-vulnerability review.

## Reporting a vulnerability

Do not publish exploit details, credentials, private artifacts or sensitive customer information in a public issue.

If GitHub private vulnerability reporting is enabled for the repository, use it. Otherwise contact the repository owner through an agreed private channel before public disclosure. Non-sensitive engineering defects may use normal GitHub issues.

## Standing rule

Security claims follow the same evidence-first policy as model-performance and efficiency claims. A security control may be described as implemented only for the boundary it actually covers; unresolved trust assumptions must remain visible.
