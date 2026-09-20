# Security Policy

AB-GEN is currently a research/demo repository undergoing reproducibility and engineering hardening.

## Model and data artifacts

AB-GEN uses Python serialization (`joblib` / pickle-compatible artifacts) for model bundles. These formats must be treated as **trusted-code artifacts**, not as safe data-exchange formats.

**Never load a `.pkl`, joblib bundle or other serialized model artifact obtained from an untrusted or unverifiable source.** A malicious serialized object may execute code during deserialization.

Validated AB-GEN releases are intended to move toward an artifact-manifest process that records provenance, producing source/version and SHA-256 checksums before runtime deserialization. Until that process is complete, only use artifacts you produced yourself from trusted source or artifacts explicitly distributed as part of a verified project release.

See also:

- `REPRODUCIBILITY.md`
- `ARTIFACT_MANIFEST_TEMPLATE.md`
- `RELEASE_CHECKLIST.md`
- issue #21 for artifact-integrity hardening

## Secrets and private material

Do not commit:

- API keys, passwords, access tokens or private certificates;
- proprietary customer datasets;
- private training artifacts intended to remain confidential;
- credentials embedded in notebooks, configuration or logs;
- customer-identifying production data.

Use environment variables or an appropriate secret-management mechanism for deployment credentials.

## Dependency and deployment security

- Reproduce releases using documented dependency versions rather than arbitrary future package versions.
- Treat model artifacts and dependency locks as part of the release evidence package.
- Keep production services behind appropriate network controls when exposed outside localhost.
- Do not expose debug/development servers to untrusted networks.
- Review Docker/runtime permissions and artifact provenance before treating the public demo as a production deployment.

## Reporting a vulnerability

Please do not publish exploit details, credentials, private artifacts or sensitive customer information in a public issue.

If GitHub private vulnerability reporting is available for this repository, use that channel. Otherwise contact the repository owner through an agreed private channel before public disclosure. Non-sensitive engineering defects may be reported through normal GitHub issues.

## Current scope

The public repository is a research/demo codebase and is **not yet represented as a security-audited production product**. Security claims should follow the same evidence-first rule as performance and efficiency claims.
