from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping

from .contracts import LeakageError, assert_manifest_ready_for_final_test
from .split_ledger import sha256_file


def load_manifest(path: Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise LeakageError("candidate manifest must be a JSON object")
    return payload


def run_preflight(manifest_path: Path, *, split_ledger_path: Path | None = None) -> str:
    manifest = load_manifest(manifest_path)
    assert_manifest_ready_for_final_test(manifest)

    if split_ledger_path is not None:
        splits = manifest.get("splits")
        if not isinstance(splits, Mapping):
            raise LeakageError("manifest splits must be an object")
        expected = splits.get("ledger_sha256")
        if not isinstance(expected, str):
            raise LeakageError("manifest splits.ledger_sha256 is missing")
        observed = sha256_file(Path(split_ledger_path))
        if observed.lower() != expected.lower():
            raise LeakageError(
                f"split ledger hash mismatch: observed={observed}, expected={expected}"
            )

    return "PASS: Clean Baseline v1 candidate is sealed for final-test evaluation."


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed Clean Baseline v1 final-test authorization preflight"
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--split-ledger", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        message = run_preflight(args.manifest, split_ledger_path=args.split_ledger)
    except (LeakageError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 2

    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
