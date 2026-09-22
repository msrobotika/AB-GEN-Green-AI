from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

from .candidate_verify import verify_frozen_candidate
from .contracts import LeakageError
from .gate_evidence import (
    BATCH_GATE_SCHEMA,
    LEAKAGE_GATE_SCHEMA,
    REQUIRED_INVARIANCE_CONTEXTS,
    REQUIRED_LEAKAGE_CHECKS,
    _load_object,
    _require_candidate_binding,
    _verify_evidence_entries,
)
from .split_ledger import sha256_file


def _verify_source_hash(path_value: object, sha_value: object, *, label: str) -> Path:
    if not isinstance(path_value, str) or not path_value:
        raise LeakageError(f"{label} source path is missing")
    if not isinstance(sha_value, str) or len(sha_value) != 64:
        raise LeakageError(f"{label} source SHA-256 is invalid")
    path = Path(path_value)
    if not path.is_file():
        raise LeakageError(f"{label} source file is missing: {path}")
    observed = sha256_file(path)
    if observed.lower() != sha_value.lower():
        raise LeakageError(f"{label} source hash mismatch: observed={observed}, expected={sha_value}")
    return path


def validate_leakage_gate(gate_path: Path, *, frozen_candidate_manifest: Path) -> Mapping[str, object]:
    frozen_candidate_manifest = Path(frozen_candidate_manifest)
    candidate = verify_frozen_candidate(frozen_candidate_manifest)
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise LeakageError("frozen candidate_id is missing")
    frozen_sha = sha256_file(frozen_candidate_manifest)

    gate = _load_object(Path(gate_path), "leakage gate")
    if gate.get("schema") != LEAKAGE_GATE_SCHEMA:
        raise LeakageError("leakage gate schema mismatch")
    _require_candidate_binding(
        gate,
        candidate_id=candidate_id,
        frozen_manifest_sha256=frozen_sha,
        label="leakage gate",
    )
    if gate.get("status") != "PASS":
        raise LeakageError("leakage gate status is not PASS")
    if gate.get("required_check_count") != len(REQUIRED_LEAKAGE_CHECKS):
        raise LeakageError("leakage gate required-check count mismatch")

    source_path = _verify_source_hash(
        gate.get("structured_audit_path"),
        gate.get("structured_audit_sha256"),
        label="structured leakage audit",
    )
    audit = _load_object(source_path, "structured leakage audit")
    _require_candidate_binding(
        audit,
        candidate_id=candidate_id,
        frozen_manifest_sha256=frozen_sha,
        label="structured leakage audit",
    )

    audit_checks = audit.get("checks")
    gate_checks = gate.get("checks")
    if not isinstance(audit_checks, Mapping) or not isinstance(gate_checks, Mapping):
        raise LeakageError("leakage audit/gate checks are missing")
    if REQUIRED_LEAKAGE_CHECKS - set(audit_checks) or REQUIRED_LEAKAGE_CHECKS - set(gate_checks):
        raise LeakageError("leakage audit/gate is missing required checks")

    for check_id in sorted(REQUIRED_LEAKAGE_CHECKS):
        source_entry = audit_checks.get(check_id)
        gate_entry = gate_checks.get(check_id)
        if not isinstance(source_entry, Mapping) or source_entry.get("status") != "PASS":
            raise LeakageError(f"structured leakage check {check_id} is not PASS")
        if not isinstance(gate_entry, Mapping) or gate_entry.get("status") != "PASS":
            raise LeakageError(f"leakage gate check {check_id} is not PASS")
        source_evidence = _verify_evidence_entries(
            source_entry.get("evidence"),
            root=source_path.parent,
            label=f"structured leakage check {check_id}",
        )
        gate_evidence = _verify_evidence_entries(
            gate_entry.get("evidence"),
            root=Path(gate_path).parent,
            label=f"leakage gate check {check_id}",
        )
        source_pairs = {(str(item["path"]), str(item["sha256"])) for item in source_evidence}
        gate_pairs = {(str(item["path"]), str(item["sha256"])) for item in gate_evidence}
        if source_pairs != gate_pairs:
            raise LeakageError(f"leakage gate/source evidence mismatch for check {check_id}")

    return gate


def validate_batch_invariance_gate(
    gate_path: Path,
    *,
    frozen_candidate_manifest: Path,
) -> Mapping[str, object]:
    frozen_candidate_manifest = Path(frozen_candidate_manifest)
    candidate = verify_frozen_candidate(frozen_candidate_manifest)
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise LeakageError("frozen candidate_id is missing")
    frozen_sha = sha256_file(frozen_candidate_manifest)

    gate = _load_object(Path(gate_path), "batch-invariance gate")
    if gate.get("schema") != BATCH_GATE_SCHEMA:
        raise LeakageError("batch-invariance gate schema mismatch")
    _require_candidate_binding(
        gate,
        candidate_id=candidate_id,
        frozen_manifest_sha256=frozen_sha,
        label="batch-invariance gate",
    )
    if gate.get("status") != "PASS":
        raise LeakageError("batch-invariance gate status is not PASS")

    report_path = _verify_source_hash(
        gate.get("invariance_report_path"),
        gate.get("invariance_report_sha256"),
        label="batch-invariance report",
    )
    report = _load_object(report_path, "batch-invariance report")
    _require_candidate_binding(
        report,
        candidate_id=candidate_id,
        frozen_manifest_sha256=frozen_sha,
        label="batch-invariance report",
    )

    for payload, label in ((report, "report"), (gate, "gate")):
        tolerance = payload.get("frozen_score_tolerance")
        max_drift = payload.get("max_score_drift")
        if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or tolerance < 0:
            raise LeakageError(f"batch-invariance {label} has invalid frozen_score_tolerance")
        if not isinstance(max_drift, (int, float)) or isinstance(max_drift, bool) or max_drift < 0:
            raise LeakageError(f"batch-invariance {label} has invalid max_score_drift")
        if max_drift > tolerance:
            raise LeakageError(f"batch-invariance {label} score drift exceeds frozen tolerance")
        for field in ("sample_count", "configuration_count", "repeat_pair_count"):
            value = payload.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise LeakageError(f"batch-invariance {label} {field} must be a positive integer")
        if payload.get("class_changes") != 0:
            raise LeakageError(f"batch-invariance {label} class_changes is not zero")
        if payload.get("identical_repeat_class_changes") != 0:
            raise LeakageError(f"batch-invariance {label} identical-repeat changes is not zero")
        if payload.get("hidden_rng_position_dependency_detected") is not False:
            raise LeakageError(f"batch-invariance {label} did not rule out hidden RNG/position dependency")
        contexts = payload.get("contexts_tested")
        if not isinstance(contexts, Sequence) or isinstance(contexts, (str, bytes)):
            raise LeakageError(f"batch-invariance {label} contexts_tested is invalid")
        if REQUIRED_INVARIANCE_CONTEXTS - frozenset(contexts):
            raise LeakageError(f"batch-invariance {label} is missing required contexts")

    if gate.get("frozen_score_tolerance") != report.get("frozen_score_tolerance"):
        raise LeakageError("batch-invariance gate/report frozen tolerance mismatch")
    if gate.get("max_score_drift") != report.get("max_score_drift"):
        raise LeakageError("batch-invariance gate/report max drift mismatch")
    for field in ("sample_count", "configuration_count", "repeat_pair_count"):
        if gate.get(field) != report.get(field):
            raise LeakageError(f"batch-invariance gate/report {field} mismatch")

    report_evidence = _verify_evidence_entries(
        report.get("evidence"),
        root=report_path.parent,
        label="batch-invariance report",
    )
    gate_evidence = _verify_evidence_entries(
        gate.get("evidence"),
        root=Path(gate_path).parent,
        label="batch-invariance gate",
    )
    report_pairs = {(str(item["path"]), str(item["sha256"])) for item in report_evidence}
    gate_pairs = {(str(item["path"]), str(item["sha256"])) for item in gate_evidence}
    if report_pairs != gate_pairs:
        raise LeakageError("batch-invariance gate/source evidence mismatch")

    return gate
