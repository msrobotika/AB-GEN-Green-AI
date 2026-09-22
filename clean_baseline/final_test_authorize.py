from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Iterable, Mapping

from .candidate_verify import verify_frozen_candidate
from .contracts import LeakageError, assert_manifest_ready_for_final_test
from .gate_validate import validate_batch_invariance_gate, validate_leakage_gate
from .split_ledger import PROTOCOL_ID, sha256_file


def authorize_final_test(
    *,
    frozen_candidate_manifest: Path,
    leakage_gate_json: Path,
    batch_invariance_gate_json: Path,
    split_ledger_path: Path,
    first_authorized_command: str,
    output_path: Path,
) -> Path:
    if not first_authorized_command.strip():
        raise LeakageError("first_authorized_command must be non-empty")

    frozen_candidate_manifest = Path(frozen_candidate_manifest)
    candidate = dict(verify_frozen_candidate(frozen_candidate_manifest))
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise LeakageError("frozen candidate_id is missing")

    leakage_gate_json = Path(leakage_gate_json)
    batch_invariance_gate_json = Path(batch_invariance_gate_json)
    leakage_gate = validate_leakage_gate(
        leakage_gate_json,
        frozen_candidate_manifest=frozen_candidate_manifest,
    )
    batch_gate = validate_batch_invariance_gate(
        batch_invariance_gate_json,
        frozen_candidate_manifest=frozen_candidate_manifest,
    )

    tolerance = batch_gate.get("frozen_score_tolerance")
    if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or tolerance < 0:
        raise LeakageError("batch-invariance gate must contain non-negative frozen_score_tolerance")

    authorized = deepcopy(candidate)
    authorized["status"] = "AUTHORIZED_FINAL_TEST"

    leakage_section = authorized.get("leakage_audit")
    batch_section = authorized.get("batch_invariance")
    final_test = authorized.get("final_test")
    if not isinstance(leakage_section, dict) or not isinstance(batch_section, dict) or not isinstance(final_test, dict):
        raise LeakageError("candidate manifest gate sections are malformed")

    leakage_section["path"] = leakage_gate_json.resolve().as_posix()
    leakage_section["sha256"] = sha256_file(leakage_gate_json)
    leakage_section["pretest_status"] = "PASS"

    batch_section["path"] = batch_invariance_gate_json.resolve().as_posix()
    batch_section["sha256"] = sha256_file(batch_invariance_gate_json)
    batch_section["pretest_status"] = "PASS"
    batch_section["frozen_score_tolerance"] = tolerance

    final_test["sealed"] = True
    final_test["decisions_frozen"] = True
    final_test["access_count_before_seal"] = 0
    final_test["first_authorized_command"] = first_authorized_command

    assert_manifest_ready_for_final_test(authorized)

    splits = authorized.get("splits")
    if not isinstance(splits, Mapping):
        raise LeakageError("candidate splits section is malformed")
    expected_ledger_sha = splits.get("ledger_sha256")
    if not isinstance(expected_ledger_sha, str):
        raise LeakageError("candidate split ledger SHA-256 is missing")
    observed_ledger_sha = sha256_file(Path(split_ledger_path))
    if observed_ledger_sha.lower() != expected_ledger_sha.lower():
        raise LeakageError(
            f"split ledger hash mismatch during final-test authorization: observed={observed_ledger_sha}, expected={expected_ledger_sha}"
        )

    authorization_record = {
        "protocol_id": PROTOCOL_ID,
        "candidate_id": candidate_id,
        "frozen_candidate_manifest": frozen_candidate_manifest.resolve().as_posix(),
        "frozen_candidate_manifest_sha256": sha256_file(frozen_candidate_manifest),
        "leakage_gate": {
            "path": leakage_gate_json.resolve().as_posix(),
            "sha256": sha256_file(leakage_gate_json),
            "status": leakage_gate.get("status"),
            "source_audit_sha256": leakage_gate.get("structured_audit_sha256"),
        },
        "batch_invariance_gate": {
            "path": batch_invariance_gate_json.resolve().as_posix(),
            "sha256": sha256_file(batch_invariance_gate_json),
            "status": batch_gate.get("status"),
            "source_report_sha256": batch_gate.get("invariance_report_sha256"),
            "frozen_score_tolerance": tolerance,
            "max_score_drift": batch_gate.get("max_score_drift"),
        },
        "split_ledger_sha256": observed_ledger_sha,
        "first_authorized_command": first_authorized_command,
        "rule": "Authorization is valid only for this frozen candidate and source-revalidated evidence set. Any model/config/artifact change requires a new candidate freeze.",
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    record_path = output_path.with_name("final_test_authorization.json")
    record_bytes = (json.dumps(authorization_record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    record_path.write_bytes(record_bytes)

    authorized["final_test"]["authorization_record_path"] = record_path.name
    authorized["final_test"]["authorization_record_sha256"] = sha256_file(record_path)
    output_path.write_text(json.dumps(authorized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Authorize the first Clean Baseline v1 final-test command after all pretest gates pass"
    )
    parser.add_argument("--frozen-candidate", type=Path, required=True)
    parser.add_argument("--leakage-gate", type=Path, required=True)
    parser.add_argument("--batch-invariance-gate", type=Path, required=True)
    parser.add_argument("--split-ledger", type=Path, required=True)
    parser.add_argument("--first-authorized-command", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        path = authorize_final_test(
            frozen_candidate_manifest=args.frozen_candidate,
            leakage_gate_json=args.leakage_gate,
            batch_invariance_gate_json=args.batch_invariance_gate,
            split_ledger_path=args.split_ledger,
            first_authorized_command=args.first_authorized_command,
            output_path=args.out,
        )
    except (LeakageError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 2

    print(f"PASS: final-test authorization manifest written to {path}")
    print("AUTHORIZED: execute only the recorded first_authorized_command against the unchanged frozen candidate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
