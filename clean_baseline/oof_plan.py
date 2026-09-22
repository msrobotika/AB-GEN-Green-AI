from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .contracts import LeakageError
from .ledger_io import read_ledger_rows, verify_ledger_package
from .split_ledger import LedgerRow, PROTOCOL_ID, sha256_file
from .stage_audit import hash_sample_id_order


def _id_file_bytes(sample_ids: Sequence[str]) -> bytes:
    if not sample_ids:
        raise LeakageError("cannot serialize an empty OOF ID set")
    if len(sample_ids) != len(set(sample_ids)):
        raise LeakageError("OOF ID set contains duplicates")
    if list(sample_ids) != sorted(sample_ids):
        raise LeakageError("OOF ID files must be written in sample_id ascending order")
    return ("\n".join(sample_ids) + "\n").encode("ascii")


def _per_class_counts(rows: Sequence[LedgerRow]) -> dict[int, int]:
    counts = {label: 0 for label in range(10)}
    for row in rows:
        counts[row.label] += 1
    return counts


def build_oof_fold_sets(rows: Sequence[LedgerRow]) -> dict[int, tuple[tuple[str, ...], tuple[str, ...]]]:
    fit_pool = tuple(row for row in rows if row.split in {"train_core", "validation"})
    if len(fit_pool) != 45_000:
        raise LeakageError(f"expected 45,000-row OOF fit pool, got {len(fit_pool)}")

    plan: dict[int, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for fold in range(5):
        held_rows = tuple(row for row in fit_pool if row.oof_fold == fold)
        producer_rows = tuple(row for row in fit_pool if row.oof_fold != fold)
        held_ids = tuple(sorted(row.sample_id for row in held_rows))
        producer_ids = tuple(sorted(row.sample_id for row in producer_rows))

        if len(held_ids) != 9_000 or len(producer_ids) != 36_000:
            raise LeakageError(
                f"OOF fold {fold} count mismatch: producer={len(producer_ids)}, held_out={len(held_ids)}"
            )
        if set(held_ids) & set(producer_ids):
            raise LeakageError(f"OOF fold {fold} producer/held-out overlap detected")
        if set(held_ids) | set(producer_ids) != {row.sample_id for row in fit_pool}:
            raise LeakageError(f"OOF fold {fold} does not partition the complete fit pool")

        held_class_counts = _per_class_counts(held_rows)
        producer_class_counts = _per_class_counts(producer_rows)
        if held_class_counts != {label: 900 for label in range(10)}:
            raise LeakageError(f"OOF fold {fold} held-out class balance changed: {held_class_counts}")
        if producer_class_counts != {label: 3_600 for label in range(10)}:
            raise LeakageError(f"OOF fold {fold} producer class balance changed: {producer_class_counts}")

        plan[fold] = (producer_ids, held_ids)

    held_union: set[str] = set()
    for _producer, held in plan.values():
        overlap = held_union & set(held)
        if overlap:
            raise LeakageError("a fit-pool sample appears as held-out in more than one OOF fold")
        held_union.update(held)
    if len(held_union) != 45_000:
        raise LeakageError(f"OOF held-out union must cover 45,000 samples, got {len(held_union)}")

    return plan


def write_oof_plan(
    rows: Sequence[LedgerRow],
    *,
    ledger_sha256: str,
    output_dir: Path,
) -> Mapping[str, object]:
    if len(ledger_sha256) != 64:
        raise LeakageError("ledger_sha256 must be a 64-character SHA-256 value")
    try:
        int(ledger_sha256, 16)
    except ValueError as exc:
        raise LeakageError("ledger_sha256 is not hexadecimal") from exc

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fold_sets = build_oof_fold_sets(rows)

    folds: list[dict[str, object]] = []
    for fold in range(5):
        producer_ids, held_ids = fold_sets[fold]
        producer_name = f"oof_fold_{fold}_producer_ids.txt"
        held_name = f"oof_fold_{fold}_heldout_ids.txt"
        producer_bytes = _id_file_bytes(producer_ids)
        held_bytes = _id_file_bytes(held_ids)
        (output_dir / producer_name).write_bytes(producer_bytes)
        (output_dir / held_name).write_bytes(held_bytes)

        folds.append(
            {
                "fold": fold,
                "producer_count": len(producer_ids),
                "held_out_count": len(held_ids),
                "producer_ids_file": producer_name,
                "producer_ids_file_sha256": sha256(producer_bytes).hexdigest(),
                "producer_id_order_sha256": hash_sample_id_order(producer_ids),
                "held_out_ids_file": held_name,
                "held_out_ids_file_sha256": sha256(held_bytes).hexdigest(),
                "held_out_id_order_sha256": hash_sample_id_order(held_ids),
                "producer_per_class": {str(label): 3_600 for label in range(10)},
                "held_out_per_class": {str(label): 900 for label in range(10)},
            }
        )

    plan: dict[str, object] = {
        "protocol_id": PROTOCOL_ID,
        "ledger_sha256": ledger_sha256,
        "fold_count": 5,
        "fit_pool_count": 45_000,
        "fold_local_preprocessing_required": True,
        "rule": "For fold k, every fitted transform and N1 producer must fit only on producer_ids for fold k; held_out_ids for fold k produce the OOF meta-features.",
        "folds": folds,
    }
    payload = (json.dumps(plan, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (output_dir / "oof_plan.json").write_bytes(payload)
    return plan


def verify_oof_plan(plan_path: Path, ledger_path: Path) -> Mapping[str, object]:
    plan_path = Path(plan_path)
    ledger_path = Path(ledger_path)
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise LeakageError("OOF plan must be a JSON object")
    if payload.get("protocol_id") != PROTOCOL_ID:
        raise LeakageError("OOF plan protocol_id mismatch")
    if payload.get("ledger_sha256") != sha256_file(ledger_path):
        raise LeakageError("OOF plan is not bound to the supplied split ledger")
    if payload.get("fold_count") != 5 or payload.get("fit_pool_count") != 45_000:
        raise LeakageError("OOF plan frozen count contract mismatch")
    if payload.get("fold_local_preprocessing_required") is not True:
        raise LeakageError("OOF plan does not require fold-local preprocessing")

    rows = read_ledger_rows(ledger_path)
    expected_sets = build_oof_fold_sets(rows)
    folds = payload.get("folds")
    if not isinstance(folds, list) or len(folds) != 5:
        raise LeakageError("OOF plan must contain exactly five fold entries")

    root = plan_path.parent
    for entry in folds:
        if not isinstance(entry, Mapping):
            raise LeakageError("OOF plan fold entry must be an object")
        fold = entry.get("fold")
        if not isinstance(fold, int) or fold not in range(5):
            raise LeakageError(f"invalid OOF fold entry: {fold!r}")
        producer_ids, held_ids = expected_sets[fold]
        for role, expected_ids in (("producer", producer_ids), ("held_out", held_ids)):
            prefix = "producer" if role == "producer" else "held_out"
            file_key = "producer_ids_file" if role == "producer" else "held_out_ids_file"
            file_hash_key = f"{prefix}_ids_file_sha256"
            order_hash_key = f"{prefix}_id_order_sha256"
            filename = entry.get(file_key)
            if not isinstance(filename, str):
                raise LeakageError(f"OOF fold {fold} missing {file_key}")
            path = root / filename
            file_bytes = _id_file_bytes(expected_ids)
            if not path.is_file() or path.read_bytes() != file_bytes:
                raise LeakageError(f"OOF fold {fold} {role} ID file content mismatch")
            if entry.get(file_hash_key) != sha256(file_bytes).hexdigest():
                raise LeakageError(f"OOF fold {fold} {role} file hash mismatch")
            if entry.get(order_hash_key) != hash_sample_id_order(expected_ids):
                raise LeakageError(f"OOF fold {fold} {role} order hash mismatch")

    return payload


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or verify the frozen Clean Baseline v1 OOF plan")
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate")
    generate.add_argument("--ledger", type=Path, required=True)
    generate.add_argument("--ledger-manifest", type=Path, required=True)
    generate.add_argument("--out-dir", type=Path, required=True)

    verify = sub.add_parser("verify")
    verify.add_argument("--ledger", type=Path, required=True)
    verify.add_argument("--plan", type=Path, required=True)

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "generate":
        manifest = verify_ledger_package(args.ledger, args.ledger_manifest)
        rows = read_ledger_rows(args.ledger)
        plan = write_oof_plan(rows, ledger_sha256=str(manifest["ledger_sha256"]), output_dir=args.out_dir)
        print(f"PASS: wrote {plan['fold_count']}-fold OOF plan bound to ledger {plan['ledger_sha256']}")
        return 0

    verify_oof_plan(args.plan, args.ledger)
    print("PASS: OOF plan and all producer/held-out ID files match the frozen ledger.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
