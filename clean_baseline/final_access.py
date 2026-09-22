from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping

from .contracts import LeakageError, assert_manifest_ready_for_final_test
from .preflight import run_preflight
from .split_ledger import PROTOCOL_ID, sha256_file


ACCESS_TOKEN_SCHEMA = "abgen-clean-baseline-v1/final-test-access-token-v1"


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


def issue_final_test_access_token(
    *,
    authorized_manifest_path: Path,
    split_ledger_path: Path,
    intended_command: str,
    output_path: Path,
) -> Path:
    if not intended_command.strip():
        raise LeakageError("intended_command must be non-empty")

    authorized_manifest_path = Path(authorized_manifest_path)
    split_ledger_path = Path(split_ledger_path)
    authorized = _load_object(authorized_manifest_path, "authorized candidate manifest")

    if authorized.get("protocol_id") != PROTOCOL_ID:
        raise LeakageError("authorized candidate protocol_id mismatch")
    if authorized.get("status") != "AUTHORIZED_FINAL_TEST":
        raise LeakageError("candidate is not in AUTHORIZED_FINAL_TEST state")
    assert_manifest_ready_for_final_test(authorized)
    run_preflight(authorized_manifest_path, split_ledger_path=split_ledger_path)

    candidate_id = authorized.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise LeakageError("authorized candidate_id is missing")
    final_test = authorized.get("final_test")
    if not isinstance(final_test, Mapping):
        raise LeakageError("authorized final_test section is missing")
    recorded_command = final_test.get("first_authorized_command")
    if recorded_command != intended_command:
        raise LeakageError(
            "intended final-test command does not exactly match first_authorized_command"
        )

    record_path = _resolve(
        authorized_manifest_path.parent,
        final_test.get("authorization_record_path"),
        "authorization record",
    )
    expected_record_sha = final_test.get("authorization_record_sha256")
    if not isinstance(expected_record_sha, str) or len(expected_record_sha) != 64:
        raise LeakageError("authorization record SHA-256 is invalid")
    if not record_path.is_file():
        raise LeakageError(f"authorization record is missing: {record_path}")
    observed_record_sha = sha256_file(record_path)
    if observed_record_sha.lower() != expected_record_sha.lower():
        raise LeakageError("authorization record hash mismatch")

    record = _load_object(record_path, "authorization record")
    if record.get("protocol_id") != PROTOCOL_ID:
        raise LeakageError("authorization record protocol_id mismatch")
    if record.get("candidate_id") != candidate_id:
        raise LeakageError("authorization record candidate_id mismatch")
    if record.get("first_authorized_command") != intended_command:
        raise LeakageError("authorization record command mismatch")

    ledger_sha = sha256_file(split_ledger_path)
    if record.get("split_ledger_sha256") != ledger_sha:
        raise LeakageError("authorization record split-ledger hash mismatch")

    token = {
        "schema": ACCESS_TOKEN_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "candidate_id": candidate_id,
        "authorized_manifest_path": authorized_manifest_path.resolve().as_posix(),
        "authorized_manifest_sha256": sha256_file(authorized_manifest_path),
        "authorization_record_path": record_path.resolve().as_posix(),
        "authorization_record_sha256": observed_record_sha,
        "split_ledger_path": split_ledger_path.resolve().as_posix(),
        "split_ledger_sha256": ledger_sha,
        "authorized_command": intended_command,
        "single_candidate_contract": True,
        "rule": "Token is valid only while the authorized manifest, authorization record, split ledger and exact command remain byte-identical.",
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(token, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def validate_final_test_access_token(
    token_path: Path,
    *,
    intended_command: str | None = None,
) -> Mapping[str, object]:
    token_path = Path(token_path)
    token = _load_object(token_path, "final-test access token")
    if token.get("schema") != ACCESS_TOKEN_SCHEMA:
        raise LeakageError("final-test access token schema mismatch")
    if token.get("protocol_id") != PROTOCOL_ID:
        raise LeakageError("final-test access token protocol_id mismatch")
    if token.get("single_candidate_contract") is not True:
        raise LeakageError("final-test access token contract flag is invalid")

    manifest_path = _resolve(token_path.parent, token.get("authorized_manifest_path"), "authorized manifest")
    record_path = _resolve(token_path.parent, token.get("authorization_record_path"), "authorization record")
    ledger_path = _resolve(token_path.parent, token.get("split_ledger_path"), "split ledger")
    for path, expected, label in (
        (manifest_path, token.get("authorized_manifest_sha256"), "authorized manifest"),
        (record_path, token.get("authorization_record_sha256"), "authorization record"),
        (ledger_path, token.get("split_ledger_sha256"), "split ledger"),
    ):
        if not path.is_file():
            raise LeakageError(f"{label} is missing: {path}")
        if not isinstance(expected, str) or len(expected) != 64:
            raise LeakageError(f"{label} token hash is invalid")
        if sha256_file(path).lower() != expected.lower():
            raise LeakageError(f"{label} changed after final-test access token issuance")

    command = token.get("authorized_command")
    if not isinstance(command, str) or not command:
        raise LeakageError("access token authorized command is missing")
    if intended_command is not None and command != intended_command:
        raise LeakageError("runtime command does not exactly match access-token command")

    authorized = _load_object(manifest_path, "authorized candidate manifest")
    if authorized.get("candidate_id") != token.get("candidate_id"):
        raise LeakageError("access token candidate_id no longer matches authorized manifest")
    assert_manifest_ready_for_final_test(authorized)
    run_preflight(manifest_path, split_ledger_path=ledger_path)

    return token


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Issue or verify a Clean Baseline v1 final-test access token")
    sub = parser.add_subparsers(dest="command", required=True)

    issue = sub.add_parser("issue")
    issue.add_argument("--authorized-manifest", type=Path, required=True)
    issue.add_argument("--split-ledger", type=Path, required=True)
    issue.add_argument("--intended-command", required=True)
    issue.add_argument("--out", type=Path, required=True)

    verify = sub.add_parser("verify")
    verify.add_argument("--token", type=Path, required=True)
    verify.add_argument("--intended-command")

    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "issue":
            path = issue_final_test_access_token(
                authorized_manifest_path=args.authorized_manifest,
                split_ledger_path=args.split_ledger,
                intended_command=args.intended_command,
                output_path=args.out,
            )
            print(f"PASS: final-test access token written to {path}")
        else:
            token = validate_final_test_access_token(
                args.token,
                intended_command=args.intended_command,
            )
            print(f"PASS: final-test access token is intact for candidate {token['candidate_id']}")
    except (LeakageError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
