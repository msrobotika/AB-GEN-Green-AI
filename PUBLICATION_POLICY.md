# AB-GEN Publication Policy

AB-GEN uses an evidence-first communication policy. Public claims should be as strong as the underlying evidence, and no stronger.

## Source of truth

GitHub is the technical source of truth for AB-GEN. Public communication on WordPress, Canva assets, presentations, videos, and social channels should reference a corresponding technical artifact whenever possible: commit, release, benchmark report, milestone entry, reproducibility note, or issue/PR.

## Claim levels

### 1. Reported
A result exists in project records but has not yet been independently reproduced from a clean environment.

Required wording examples:
- "Project records report 80.14% on CIFAR-10."
- "Result pending full reproduction."

### 2. Reproduced
The result has been rerun from frozen source and artifacts with a documented environment, dataset split, seeds, hashes, and test protocol.

Required evidence:
- exact source commit/tag;
- dataset and split;
- preprocessing definition;
- seed(s);
- dependency lock or environment export;
- model/preprocessing artifact hashes;
- test output and per-class metrics where relevant.

### 3. Benchmarked
The result has been reproduced and compared against baselines under the same measurement boundary and hardware.

For efficiency claims this also requires:
- exact hardware and OS;
- warm-up procedure;
- batch size and throughput;
- repeated power/energy measurements;
- joules per inference;
- model-only vs end-to-end figures separated;
- baseline measured under the same protocol.

### 4. Independently validated
A third party, separate environment, external dataset, or other independent process confirms the core result.

This is the preferred level for strong external claims, press outreach, investor material, and high-confidence scientific communication.

## Publication workflow

For each meaningful milestone:
1. Verify the technical result.
2. Record it in `MILESTONES.md`.
3. Create or update the supporting benchmark/reproducibility documentation.
4. Tag or release the reproducible version when appropriate.
5. Update the repository README with the new validated state.
6. Create a concise public explanation for WordPress.
7. Create a matching visual asset in Canva when the result benefits from a chart, diagram, or infographic.
8. Reuse the same validated numbers and wording across all channels.

## Communication priorities

AB-GEN should be positioned around:
- efficient vision architectures;
- geometric and spectral feature engineering;
- reproducibility;
- edge and resource-constrained inference;
- measured Green AI performance;
- interpretable decision paths where actually supported by the model and validation method.

## Current headline result under validation

Project documentation records **80.14% CIFAR-10 accuracy for AB-GEN V24 Slow Burn**, with a recorded runtime of approximately 420 minutes. This remains a reported result until the original training source and artifacts are fully reproduced and audited.

## Medical communication rule

AB-GEN Medical remains a research/demo system unless and until appropriate clinical validation, calibration, external validation, and regulatory requirements are met. Public materials must not present it as a clinically validated diagnostic system without that evidence.

## Standing rule

Do not trade long-term credibility for a short-term headline. If a claim cannot be traced to evidence, publish the experiment or uncertainty instead of presenting the claim as established fact.
