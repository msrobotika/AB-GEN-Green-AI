from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Mapping

from .contracts import LeakageError
from .split_ledger import LEDGER_COLUMNS, PROTOCOL_ID, LedgerRow, assert_ledger_rows, sha256_file


def read_ledger_rows(path: Path) -> tuple[LedgerRow, ...]:
    path = Path(path)
    rows: list[LedgerRow] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(LEDGER_COLUMNS):
            raise LeakageError(
                f"split ledger columns changed: {reader.fieldnames!r}; expected={list(LEDGER_COLUMNS)!r}"
            )
        for line_number, item in enumerate(reader, start=2):
            try:
                sample_id = item["sample_id"]
                label = int(item["label"])
                source_partition = item["source_partition"]
                source_file = item["source_file"]
                source_index = int(item["source_index"])
                split = item["split"]
                fold_text = item["oof_fold"]
                oof_fold = None if fold_text == "" else int(fold_text)
            except (KeyError, TypeError, ValueError) as exc:
                raise LeakageError(f"invalid split ledger row at line {line_number}") from exc

            rows.append(
                LedgerRow(
                    sample_id=sample_id,
                    label=label,
                    source_partition=source_partition,
                    source_file=source_file,
                    source_index=source_index,
                    split=split,
                    oof_fold=oof_fold,
                )
            )

    assert_ledger_rows(rows)
    ordered_ids = [row.sample_id for row in rows]
    if ordered_ids != sorted(ordered_ids):
        raise LeakageError("split ledger row order is not frozen sample_id ascending order")
    return tuple(rows)


def _load_manifest(path: Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise LeakageError("split ledger manifest must be a JSON object")
    return payload


def verify_ledger_package(ledger_path: Path, manifest_path: Path) -> Mapping[str, object]:
    ledger_path = Path(ledger_path)
    manifest_path = Path(manifest_path)
    manifest = _load_manifest(manifest_path)

    if manifest.get("protocol_id") != PROTOCOL_ID:
        raise LeakageError("split ledger manifest protocol_id mismatch")
    if manifest.get("ledger_format") != "csv/utf-8/lf":
        raise LeakageError("split ledger manifest format mismatch")
    if manifest.get("row_order") != "sample_id ascending":
        raise LeakageError("split ledger manifest row-order contract mismatch")
    if manifest.get("ledger_file") != ledger_path.name:
        raise LeakageError(
            f"split ledger filename mismatch: manifest={manifest.get('ledger_file')!r}, actual={ledger_path.name!r}"
        )

    expected_sha = manifest.get("ledger_sha256")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise LeakageError("split ledger manifest contains invalid ledger_sha256")
    observed_sha = sha256_file(ledger_path)
    if observed_sha.lower() != expected_sha.lower():
        raise LeakageError(
            f"split ledger hash mismatch: observed={observed_sha}, expected={expected_sha}"
        )

    rows = read_ledger_rows(ledger_path)

    expected_counts = {
        "train_core": 40_000,
        "validation": 5_000,
        "calibration_reserved": 5_000,
        "test": 10_000,
        "oof_fold_0": 9_000,
        "oof_fold_1": 9_000,
        "oof_fold_2": 9_000,
        "oof_fold_3": 9_000,
        "oof_fold_4": 9_000,
    }
    if manifest.get("counts") != expected_counts:
        raise LeakageError("split ledger manifest count contract mismatch")

    source_hashes = manifest.get("source_batch_sha256")
    if not isinstance(source_hashes, Mapping) or len(source_hashes) != 6:
        raise LeakageError("split ledger manifest must retain six source batch hashes")
    for name, digest in source_hashes.items():
        if not isinstance(name, str) or not isinstance(digest, str) or len(digest) != 64:
            raise LeakageError("split ledger source hash entry is invalid")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise LeakageError(f"split ledger source hash for {name!r} is not hexadecimal") from exc

    if len(rows) != 60_000:
        raise LeakageError("verified ledger did not retain 60,000 rows")
    return manifest
