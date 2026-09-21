# AB-GEN Publication Policy

AB-GEN uses an evidence-first communication policy: public claims may be as strong as the archived evidence, and no stronger.

## Source of truth

GitHub is the technical source of truth for AB-GEN. Public communication on WordPress, Canva assets, presentations, videos and social channels should reference a corresponding technical artifact whenever practical: commit, release, benchmark report, milestone entry, reproducibility note, issue or pull request.

The repository README and `MILESTONES.md` define current evidence status. The short GitHub “About” description is tracked separately in issue #11 until its wording is aligned.

## Evidence states

### Reported
A result exists in historical/internal project records but has not been reproduced from a frozen, auditable pipeline.

Acceptable wording:
- “Project records report 80.14% on CIFAR-10.”
- “Historical result; exact reproduction pending.”

Unacceptable wording:
- “AB-GEN achieves 80.14%” when exact reproduction is not established.

### Recovered
An original artifact or recovered execution path has been located and evaluated, but the complete producing pipeline is not yet proven.

Example:
- “The recovered Elite bundle evaluates to 80.17% from the PCA-cache path.”

Recovered does not imply that raw preprocessing, split identity, training protocol or historical prediction identity has been reproduced.

### Reconstructed
A missing pipeline stage has been rebuilt from evidence and executed successfully. The reconstruction must remain distinguishable from an original historical artifact.

### Reproduced
The accepted result is rerun from frozen source, inputs and artifacts under a documented environment with the relevant leakage and determinism gates passed.

Minimum evidence:
- exact source commit/tag;
- dataset version and immutable split identities;
- preprocessing fit scope;
- seeds and deterministic settings;
- dependency/environment lock;
- model and preprocessing artifact hashes;
- test output and full predictions where practical;
- leakage audit;
- per-class metrics where relevant.

### Validated / benchmarked
A reproduced result additionally passes the relevant comparison or domain-specific validation gates.

Efficiency claims require:
- exact hardware and OS;
- identical measurement boundary for model and baseline;
- warm-up procedure;
- batch size / throughput;
- repeated energy measurements and uncertainty;
- joules per inference/image;
- model-only versus end-to-end figures separated;
- baseline measured under the same protocol;
- comparable accuracy/evaluation conditions.

### Independently validated
A third party, separate environment, external dataset or other independent process confirms the core result. This is the preferred evidence level for strong external claims, press material or high-confidence scientific positioning.

## Current public-status rules

### CIFAR-10
- Historical V24 Slow Burn **80.14%**: `Reported`.
- Recovered Elite / Slow Burn **80.17%**: `Recovered` PCA-cache execution.
- M5 MASTER **79.55%**: reconstructed/executed route.
- M4 **78.05%**: recovered PCA-cache result.

None of these is currently a certified clean RAW→prediction baseline.

### Batch dependence
The recovered historical inference path has demonstrated batch-context dependence on a targeted low-margin subset. Public descriptions must say this when presenting live diagnostic results from that path. The subset must not be generalized to the entire test set without evidence.

### Energy
Historical Green AI figures are not validated measurements. Because the audit found a factor-of-1,000 discrepancy in at least one derived calculation, **no historical percentage-saving figure should be used as a current headline**.

Until a controlled benchmark is executed, acceptable wording is:
- “Energy benchmark pending controlled measurement.”

### Calibration / XAI
Normalized Ridge decision scores are not calibrated probabilities unless calibration evidence says otherwise. Geometric/PCA visualization is not automatically faithful attribution.

## Clean Baseline v1 publication gate

The next result promoted beyond recovery/reconstruction must come from a clean raw-data pipeline with:
- split frozen before fitting;
- train-only PCA and class-dependent transforms;
- leakage-safe N2 stacking;
- deterministic inference independent of batch position/composition;
- frozen source/environment/artifact hashes;
- final-test access after model-selection decisions are frozen;
- retained full predictions and audit outputs.

A lower clean score must be reported without attempting to preserve the historical headline.

## Connectome Edge R&D communication rule

Connectome-inspired work is a separate hypothesis-driven track. Until matched controls are executed, public language must use terms such as “research hypothesis”, “candidate topology” and “planned experiment”.

Do not describe AB-GEN as brain-like, neuromorphic, more intelligent, more efficient or superior on the basis of connectome inspiration alone.

## Publication workflow

For each meaningful milestone:
1. verify the technical result;
2. classify its evidence state;
3. record it in `MILESTONES.md`;
4. retain supporting source, environment, predictions and hashes;
5. complete the relevant leakage / benchmark / release gates;
6. update README only after the evidence state changes;
7. update WordPress and other public material with the same wording;
8. create a visual asset only when its numbers are already evidence-backed;
9. preserve superseded claims as history rather than silently rewriting evidence.

## Medical communication rule

Any AB-GEN medical work remains research/demo only unless appropriate clinical validation, calibration, external validation and regulatory requirements are met. It must not be presented as a clinically validated diagnostic system without that evidence.

## Standing rule

Do not trade long-term credibility for a short-term headline. If a statement cannot be traced to archived evidence, publish the uncertainty or experiment instead of presenting it as established fact.
