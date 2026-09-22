from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .candidate_verify import verify_frozen_candidate
from .contracts import LeakageError
from .split_ledger import PROTOCOL_ID, sha256_file


LEAKAGE_GATE_SCHEMA = "abgen-clean-baseline-v1/leakage-gate-v1"
BATCH_GATE_SCHEMA = "abgen-clean-baseline-v1/batch-invariance-gate-v1"

REQUIRED_LEAKAGE_CHECKS = frozenset(
    {
        "D1",
        "D2",
        "D3",
        "D4",
        "P1",
        "P2",
        "F1",
        "F2",
        "N1-1",
        "N1-2",
        "N1-3",
        "N2-1",
        "N2-2",
        "N2-3",
        "A1",
        "A2",
        "C1",
        "C2",
        "E1",
        "E2",
        "E3",
    }
)

REQUIRED_INVARIANCE_CONTEXTS = frozenset(
    {
        "repeated_identical_calls",
        "individual_inference",
        "multiple_batch_sizes",
        "multiple_batch_positions",
        "different_companion_samples",
    }
)


def _load_object(path: Path, label: str) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise LeakageError(f"{label} must be a JSON object")
    return payload


def _require_candidate_binding(
    payload: Mapping[str, object],
    *,
    candidate_id: str,
    frozen_manifest_sha256: str,
    label: str,
) -> None:
    if payload.get("protocol_id") != PROTOCOL_ID:
        raise LeakageError(f"{label} protocol_id mismatch")
    if payload.get("candidate_id") != candidate_id:
        raise LeakageError(f"{label} candidate_id mismatch")
    if payload.get("frozen_candidate_manifest_sha256") != frozen_manifest_sha256:
        raise LeakageError(f"{label} is not bound to the supplied frozen candidate manifest")


def _resolve_evidence_path(root: Path, value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise LeakageError(f"{label} evidence path is missing")
    path = Path(value)
    return path if path.is_absolute() else root / path


def _verify_evidence_entries(entries: object, *, root: Path, label: str) -> tuple[dict[str, object], ...]:
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)) or not entries:
        raise LeakageError(f"{label} must retain at least one evidence file")

    verified: list[dict[str, object]] = []
    for index, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, Mapping):
            raise LeakageError(f"{label} evidence[{index}] must be an object")
        path = _resolve_evidence_path(root, raw_entry.get("path"), f"{label}[{index}]")
        expected = raw_entry.get("sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            raise LeakageError(f"{label} evidence[{index}] has invalid SHA-256")
        try:
            int(expected, 16)
        except ValueError as exc:
            raise LeakageError(f"{label} evidence[{index}] SHA-256 is not hexadecimal") from exc
        if not path.is_file():
            raise LeakageError(f"{label} evidence[{index}] file is missing: {path}")
        observed = sha256_file(path)
        if observed.lower() != expected.lower():
            raise LeakageError(
                f"{label} evidence[{index}] hash mismatch: observed={observed}, expected={expected}"
            )
        verified.append(
            {
                "path": path.resolve().as_posix(),
                "sha256": observed,
                "size_bytes": path.stat().st_size,
            }
        )
    return tuple(verified)


def build_leakage_gate(
    *,
    frozen_candidate_manifest: Path,
    structured_audit_json: Path,
    output_path: Path,
) -> Path:
    frozen_candidate_manifest = Path(frozen_candidate_manifest)
    candidate = verify_frozen_candidate(frozen_candidate_manifest)
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise LeakageError("frozen candidate_id is missing")
    frozen_sha = sha256_file(frozen_candidate_manifest)

    structured_audit_json = Path(structured_audit_json)
    audit = _load_object(structured_audit_json, "structured leakage audit")
    _require_candidate_binding(
        audit,
        candidate_id=candidate_id,
        frozen_manifest_sha256=frozen_sha,
        label="structured leakage audit",
    )

    checks = audit.get("checks")
    if not isinstance(checks, Mapping):
        raise LeakageError("structured leakage audit checks must be an object")
    missing = REQUIRED_LEAKAGE_CHECKS - set(checks)
    if missing:
        raise LeakageError(f"structured leakage audit missing required checks: {sorted(missing)}")

    normalized_checks: dict[str, object] = {}
    for check_id in sorted(REQUIRED_LEAKAGE_CHECKS):
        entry = checks.get(check_id)
        if not isinstance(entry, Mapping):
            raise LeakageError(f"leakage check {check_id} must be an object")
        status = entry.get("status")
        if status != "PASS":
            raise LeakageError(f"leakage check {check_id} is not PASS: {status!r}")
        evidence = _verify_evidence_entries(
            entry.get("evidence"),
            root=structured_audit_json.parent,
            label=f"leakage check {check_id}",
        )
        normalized_checks[check_id] = {
            "status": "PASS",
            "evidence": list(evidence),
            "note": entry.get("note", ""),
        }

    gate = {
        "schema": LEAKAGE_GATE_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "candidate_id": candidate_id,
        "frozen_candidate_manifest_sha256": frozen_sha,
        "status": "PASS",
        "required_check_count": len(REQUIRED_LEAKAGE_CHECKS),
        "checks": normalized_checks,
        "structured_audit_path": structured_audit_json.resolve().as_posix(),
        "structured_audit_sha256": sha256_file(structured_audit_json),
        "rule": "PASS is derived only when every required Clean Baseline v1 leakage check is PASS and each check retains hash-verified evidence.",
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def build_batch_invariance_gate(
    *,
    frozen_candidate_manifest: Path,
    invariance_report_json: Path,
    output_path: Path,
) -> Path:
    frozen_candidate_manifest = Path(frozen_candidate_manifest)
    candidate = verify_frozen_candidate(frozen_candidate_manifest)
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise LeakageError("frozen candidate_id is missing")
    frozen_sha = sha256_file(frozen_candidate_manifest)

    invariance_report_json = Path(invariance_report_json)
    report = _load_object(invariance_report_json, "batch-invariance report")
    _require_candidate_binding(
        report,
        candidate_id=candidate_id,
        frozen_manifest_sha256=frozen_sha,
        label="batch-invariance report",
    )

    tolerance = report.get("frozen_score_tolerance")
    max_drift = report.get("max_score_drift")
    if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or tolerance < 0:
        raise LeakageError("batch-invariance report frozen_score_tolerance must be non-negative")
    if not isinstance(max_drift, (int, float)) or isinstance(max_drift, bool) or max_drift < 0:
        raise LeakageError("batch-invariance report max_score_drift must be non-negative")
    if max_drift > tolerance:
        raise LeakageError(
            f"batch-invariance score drift exceeds frozen tolerance: max={max_drift}, tolerance={tolerance}"
        )

    for field in ("sample_count", "configuration_count", "repeat_pair_count"):
        value = report.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise LeakageError(f"batch-invariance report {field} must be a positive integer")

    if report.get("class_changes") != 0:
        raise LeakageError(f"batch-invariance class_changes must be 0, got {report.get('class_changes')!r}")
    if report.get("identical_repeat_class_changes") != 0:
        raise LeakageError(
            "batch-invariance identical_repeat_class_changes must be 0"
        )
    if report.get("hidden_rng_position_dependency_detected") is not False:
        raise LeakageError("batch-invariance report detected or did not rule out hidden RNG/position dependency")

    contexts = report.get("contexts_tested")
    if not isinstance(contexts, Sequence) or isinstance(contexts, (str, bytes)):
        raise LeakageError("batch-invariance report contexts_tested must be a list")
    context_set = frozenset(contexts)
    missing_contexts = REQUIRED_INVARIANCE_CONTEXTS - context_set
    if missing_contexts:
        raise LeakageError(f"batch-invariance report missing required contexts: {sorted(missing_contexts)}")

    evidence = _verify_evidence_entries(
        report.get("evidence"),
        root=invariance_report_json.parent,
        label="batch-invariance report",
    )

    gate = {
        "schema": BATCH_GATE_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "candidate_id": candidate_id,
        "frozen_candidate_manifest_sha256": frozen_sha,
        "status": "PASS",
        "frozen_score_tolerance": tolerance,
        "max_score_drift": max_drift,
        "sample_count": report["sample_count"],
        "configuration_count": report["configuration_count"],
        "repeat_pair_count": report["repeat_pair_count"],
        "class_changes": 0,
        "identical_repeat_class_changes": 0,
        "hidden_rng_position_dependency_detected": False,
        "contexts_tested": sorted(context_set),
        "evidence": list(evidence),
        "invariance_report_path": invariance_report_json.resolve().as_posix(),
        "invariance_report_sha256": sha256_file(invariance_report_json),
        "rule": "PASS is derived only with zero class changes across required accidental batch contexts and max score drift within the frozen tolerance.",
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def validate_gate_for_candidate(
    gate_path: Path,
    *,
    frozen_candidate_manifest: Path,
    expected_schema: str,
) -> Mapping[str, object]:
    frozen_candidate_manifest = Path(frozen_candidate_manifest)
    candidate = verify_frozen_candidate(frozen_candidate_manifest)
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise LeakageError("frozen candidate_id is missing")

    gate = _load_object(Path(gate_path), "gate evidence")
    if gate.get("schema") != expected_schema:
        raise LeakageError(f"gate schema mismatch: expected={expected_schema!r}, got={gate.get('schema')!r}")
    _require_candidate_binding(
        gate,
        candidate_id=candidate_id,
        frozen_manifest_sha256=sha256_file(frozen_candidate_manifest),
        label="gate evidence",
    )
    if gate.get("status") != "PASS":
        raise LeakageError("gate evidence status is not PASS")

    if expected_schema == LEAKAGE_GATE_SCHEMA:
        checks = gate.get("checks")
        if not isinstance(checks, Mapping):
            raise LeakageError("leakage gate checks are missing")
        if REQUIRED_LEAKAGE_CHECKS - set(checks):
            raise LeakageError("leakage gate no longer contains every required check")
        for check_id in REQUIRED_LEAKAGE_CHECKS:
            entry = checks.get(check_id)
            if not isinstance(entry, Mapping) or entry.get("status") != "PASS":
                raise LeakageError(f"leakage gate check {check_id} is not PASS")
    elif expected_schema == BATCH_GATE_SCHEMA:
        tolerance = gate.get("frozen_score_tolerance")
        max_drift = gate.get("max_score_drift")
        if not isinstance(tolerance, (int, float)) or not isinstance(max_drift, (int, float)):
            raise LeakageError("batch gate tolerance/drift is invalid")
        if max_drift > tolerance or gate.get("class_changes") != 0:
            raise LeakageError("batch gate no longer satisfies invariance contract")
        contexts = gate.get("contexts_tested")
        if not isinstance(contexts, Sequence) or isinstance(contexts, (str, bytes)):
            raise LeakageError("batch gate contexts are invalid")
        if REQUIRED_INVARIANCE_CONTEXTS - frozenset(contexts):
            raise LeakageError("batch gate is missing required invariance contexts")
    else:
        raise LeakageError(f"unsupported gate schema: {expected_schema!r}")

    return gate


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Derive hash-bound Clean Baseline v1 machine gate evidence")
    sub = parser.add_subparsers(dest="command", required=True)

    leakage = sub.add_parser("leakage")
    leakage.add_argument("--frozen-candidate", type=Path, required=True)
    leakage.add_argument("--audit", type=Path, required=True)
    leakage.add_argument("--out", type=Path, required=True)

    batch = sub.add_parser("batch-invariance")
    batch.add_argument("--frozen-candidate", type=Path, required=True)
    batch.add_argument("--report", type=Path, required=True)
    batch.add_argument("--out", type=Path, required=True)

    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "leakage":
            path = build_leakage_gate(
                frozen_candidate_manifest=args.frozen_candidate,
                structured_audit_json=args.audit,
                output_path=args.out,
            )
        else:
            path = build_batch_invariance_gate(
                frozen_candidate_manifest=args.frozen_candidate,
                invariance_report_json=args.report,
                output_path=args.out,
            )
    except (LeakageError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 2

    print(f"PASS: machine gate evidence written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
