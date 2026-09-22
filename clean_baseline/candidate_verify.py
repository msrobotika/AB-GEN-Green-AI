from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping

from .contracts import LeakageError
from .split_ledger import PROTOCOL_ID, sha256_file


def _load_object(path: Path, label: str) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise LeakageError(f"{label} must be a JSON object")
    return payload


def _resolve(root: Path, value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise LeakageError(f"{label} path is missing")
    path = Path(value)
    return path if path.is_absolute() else root / path


def _check_file(root: Path, entry: Mapping[str, object], label: str) -> Path:
    path = _resolve(root, entry.get("path"), label)
    expected = entry.get("sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise LeakageError(f"{label} SHA-256 is invalid")
    if not path.is_file():
        raise LeakageError(f"{label} file is missing: {path}")
    observed = sha256_file(path)
    if observed.lower() != expected.lower():
        raise LeakageError(f"{label} hash mismatch: observed={observed}, expected={expected}")
    return path


def verify_frozen_candidate(candidate_manifest_path: Path) -> Mapping[str, object]:
    candidate_manifest_path = Path(candidate_manifest_path)
    root = candidate_manifest_path.parent
    candidate = _load_object(candidate_manifest_path, "candidate manifest")

    if candidate.get("protocol_id") != PROTOCOL_ID:
        raise LeakageError("candidate manifest protocol_id mismatch")
    if candidate.get("status") != "FROZEN_PRETEST":
        raise LeakageError("candidate manifest status is not FROZEN_PRETEST")

    candidate_id = candidate.get("candidate_id")
    source_commit = candidate.get("source_commit")
    if not isinstance(candidate_id, str) or not candidate_id or candidate_id == "UNSET":
        raise LeakageError("candidate manifest candidate_id is not frozen")
    if not isinstance(source_commit, str) or len(source_commit) != 40:
        raise LeakageError("candidate manifest source_commit is not a full commit SHA")

    final_test = candidate.get("final_test")
    if not isinstance(final_test, Mapping):
        raise LeakageError("candidate final_test section is missing")
    if final_test.get("sealed") is not False:
        raise LeakageError("FROZEN_PRETEST candidate must keep final test sealed")
    if final_test.get("decisions_frozen") is not True:
        raise LeakageError("candidate decisions are not frozen")
    if final_test.get("access_count_before_seal") != 0:
        raise LeakageError("candidate records final-test access before seal")

    artifacts_section = candidate.get("artifacts")
    if not isinstance(artifacts_section, Mapping):
        raise LeakageError("candidate artifacts section is missing")
    pretest_path = _resolve(root, artifacts_section.get("pretest_manifest_path"), "pretest manifest")
    expected_pretest_sha = artifacts_section.get("pretest_manifest_sha256")
    if not isinstance(expected_pretest_sha, str) or len(expected_pretest_sha) != 64:
        raise LeakageError("candidate pretest manifest SHA-256 is invalid")
    if not pretest_path.is_file():
        raise LeakageError(f"pretest evidence manifest is missing: {pretest_path}")
    observed_pretest_sha = sha256_file(pretest_path)
    if observed_pretest_sha.lower() != expected_pretest_sha.lower():
        raise LeakageError(
            f"pretest evidence manifest hash mismatch: observed={observed_pretest_sha}, expected={expected_pretest_sha}"
        )

    pretest = _load_object(pretest_path, "pretest evidence manifest")
    if pretest.get("protocol_id") != PROTOCOL_ID:
        raise LeakageError("pretest evidence protocol_id mismatch")
    if pretest.get("candidate_id") != candidate_id:
        raise LeakageError("candidate/pretest candidate_id mismatch")
    if pretest.get("source_commit") != source_commit:
        raise LeakageError("candidate/pretest source_commit mismatch")
    if pretest.get("final_test_access_count_at_freeze") != 0:
        raise LeakageError("pretest evidence records final-test access before freeze")

    pretest_root = pretest_path.parent
    for key, label in (
        ("split_ledger", "split ledger"),
        ("oof_plan", "OOF plan"),
        ("frozen_config", "frozen config"),
        ("environment_lock", "environment lock"),
        ("feature_order", "feature order"),
    ):
        entry = pretest.get(key)
        if not isinstance(entry, Mapping):
            raise LeakageError(f"pretest evidence missing {key}")
        _check_file(pretest_root, entry, label)

    split_entry = pretest.get("split_ledger")
    if isinstance(split_entry, Mapping):
        manifest_path = _resolve(pretest_root, split_entry.get("manifest_path"), "split ledger manifest")
        expected = split_entry.get("manifest_sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            raise LeakageError("split ledger manifest SHA-256 is invalid")
        if not manifest_path.is_file() or sha256_file(manifest_path).lower() != expected.lower():
            raise LeakageError("split ledger manifest hash mismatch")

    artifact_entries = pretest.get("artifacts")
    if not isinstance(artifact_entries, list) or not artifact_entries:
        raise LeakageError("pretest evidence must retain at least one fitted/pretest artifact")
    for index, entry in enumerate(artifact_entries):
        if not isinstance(entry, Mapping):
            raise LeakageError(f"artifact entry {index} is not an object")
        path = _check_file(pretest_root, entry, f"artifact[{index}]")
        expected_size = entry.get("size_bytes")
        if not isinstance(expected_size, int) or path.stat().st_size != expected_size:
            raise LeakageError(f"artifact[{index}] size mismatch")

    commands = pretest.get("commands")
    if not isinstance(commands, list) or not commands or any(not isinstance(cmd, str) or not cmd for cmd in commands):
        raise LeakageError("pretest evidence exact command list is missing")

    return candidate


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a frozen Clean Baseline v1 pretest evidence package")
    parser.add_argument("candidate_manifest", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        candidate = verify_frozen_candidate(args.candidate_manifest)
    except (LeakageError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 2
    print(f"PASS: frozen candidate evidence is intact: {candidate['candidate_id']}")
    print("SEALED: integrity verification does not authorize final-test evaluation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
