from __future__ import annotations

import argparse
import csv
import json
import pickle
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np

from .contracts import LeakageError, RawSample, SplitLedger, assign_development_splits, assign_oof_folds, hash_sample_bytes


PROTOCOL_ID = "abgen-clean-baseline-v1"
CIFAR_IMAGE_BYTES = 32 * 32 * 3
CIFAR_BATCH_SPECS: tuple[tuple[str, str], ...] = (
    ("data_batch_1", "train"),
    ("data_batch_2", "train"),
    ("data_batch_3", "train"),
    ("data_batch_4", "train"),
    ("data_batch_5", "train"),
    ("test_batch", "test"),
)


@dataclass(frozen=True)
class SourceSample:
    sample_id: str
    label: int
    source_partition: str
    source_file: str
    source_index: int


@dataclass(frozen=True)
class LedgerRow:
    sample_id: str
    label: int
    source_partition: str
    source_file: str
    source_index: int
    split: str
    oof_fold: int | None


LEDGER_COLUMNS = (
    "sample_id",
    "label",
    "source_partition",
    "source_file",
    "source_index",
    "split",
    "oof_fold",
)


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def inventory_cifar_python_dir(root: Path) -> dict[str, str]:
    """Hash the six expected CIFAR-10 Python batch files without unpickling them."""
    root = Path(root)
    hashes: dict[str, str] = {}
    for filename, _partition in CIFAR_BATCH_SPECS:
        path = root / filename
        if not path.is_file():
            raise LeakageError(f"missing CIFAR-10 batch file: {path}")
        hashes[filename] = sha256_file(path)
    return hashes


def _validate_expected_hashes(observed: Mapping[str, str], expected: Mapping[str, object]) -> None:
    expected_names = {name for name, _ in CIFAR_BATCH_SPECS}
    if set(expected) != expected_names:
        missing = sorted(expected_names - set(expected))
        extra = sorted(set(expected) - expected_names)
        raise LeakageError(f"expected-source hash map mismatch; missing={missing}, extra={extra}")

    for filename in sorted(expected_names):
        value = expected[filename]
        if not isinstance(value, str) or len(value) != 64:
            raise LeakageError(f"invalid SHA-256 value for {filename}: {value!r}")
        try:
            int(value, 16)
        except ValueError as exc:
            raise LeakageError(f"invalid SHA-256 hex for {filename}: {value!r}") from exc
        if observed[filename].lower() != value.lower():
            raise LeakageError(
                f"CIFAR-10 source hash mismatch for {filename}: "
                f"observed={observed[filename]}, expected={value}"
            )


def _payload_value(payload: Mapping[object, object], *keys: object) -> object:
    for key in keys:
        if key in payload:
            return payload[key]
    raise LeakageError(f"CIFAR batch missing keys {keys!r}")


def _load_trusted_batch(path: Path, partition: str) -> tuple[SourceSample, ...]:
    """Load one hash-verified CIFAR-10 Python batch.

    CIFAR-10 Python batches are pickle files. Callers must validate the complete
    batch-file SHA-256 map before this function is reached. Never point this at
    untrusted arbitrary pickle input.
    """
    with path.open("rb") as handle:
        payload = pickle.load(handle, encoding="bytes")  # noqa: S301 - hash-verified trusted source only

    if not isinstance(payload, Mapping):
        raise LeakageError(f"unexpected CIFAR batch payload type in {path.name}: {type(payload)!r}")

    data_obj = _payload_value(payload, b"data", "data")
    labels_obj = _payload_value(payload, b"labels", "labels")
    data = np.asarray(data_obj)
    labels = np.asarray(labels_obj)

    if data.shape != (10_000, CIFAR_IMAGE_BYTES):
        raise LeakageError(f"{path.name}: expected data shape (10000, 3072), got {data.shape}")
    if data.dtype != np.uint8:
        raise LeakageError(f"{path.name}: expected uint8 data, got {data.dtype}")
    if labels.shape != (10_000,):
        raise LeakageError(f"{path.name}: expected 10,000 labels, got shape {labels.shape}")

    samples: list[SourceSample] = []
    for index in range(10_000):
        raw_bytes = data[index].tobytes(order="C")
        if len(raw_bytes) != CIFAR_IMAGE_BYTES:
            raise LeakageError(f"{path.name}[{index}]: unexpected raw byte length {len(raw_bytes)}")
        label = int(labels[index])
        if not 0 <= label <= 9:
            raise LeakageError(f"{path.name}[{index}]: invalid CIFAR-10 label {label}")
        samples.append(
            SourceSample(
                sample_id=hash_sample_bytes(raw_bytes),
                label=label,
                source_partition=partition,
                source_file=path.name,
                source_index=index,
            )
        )
    return tuple(samples)


def load_verified_cifar_python_batches(
    root: Path,
    expected_source_hashes: Mapping[str, object],
) -> tuple[tuple[SourceSample, ...], dict[str, str]]:
    """Load exactly 60,000 CIFAR-10 rows after full source-file hash verification."""
    root = Path(root)
    observed_hashes = inventory_cifar_python_dir(root)
    _validate_expected_hashes(observed_hashes, expected_source_hashes)

    samples: list[SourceSample] = []
    for filename, partition in CIFAR_BATCH_SPECS:
        samples.extend(_load_trusted_batch(root / filename, partition))

    if len(samples) != 60_000:
        raise LeakageError(f"expected 60,000 CIFAR-10 samples, loaded {len(samples)}")
    if len({sample.sample_id for sample in samples}) != 60_000:
        raise LeakageError("exact duplicate RAW image bytes detected while building split ledger")

    return tuple(samples), observed_hashes


def build_ledger_rows(samples: Sequence[SourceSample]) -> tuple[LedgerRow, ...]:
    raw_samples = tuple(
        RawSample(sample.sample_id, sample.label, sample.source_partition) for sample in samples
    )
    records = assign_development_splits(raw_samples)
    ledger = SplitLedger(records)
    ledger.assert_exact_split_counts()
    oof = assign_oof_folds(ledger)

    source_by_id = {sample.sample_id: sample for sample in samples}
    if len(source_by_id) != len(samples):
        raise LeakageError("duplicate sample IDs prevent unambiguous source provenance")

    rows: list[LedgerRow] = []
    for record in records:
        source = source_by_id[record.sample_id]
        rows.append(
            LedgerRow(
                sample_id=record.sample_id,
                label=record.label,
                source_partition=source.source_partition,
                source_file=source.source_file,
                source_index=source.source_index,
                split=record.split,
                oof_fold=oof.get(record.sample_id),
            )
        )

    rows.sort(key=lambda row: row.sample_id)
    assert_ledger_rows(rows)
    return tuple(rows)


def assert_ledger_rows(rows: Sequence[LedgerRow]) -> None:
    if len(rows) != 60_000:
        raise LeakageError(f"ledger must contain exactly 60,000 rows, got {len(rows)}")
    if len({row.sample_id for row in rows}) != 60_000:
        raise LeakageError("ledger sample IDs are not unique")

    counts = {"train_core": 0, "validation": 0, "calibration_reserved": 0, "test": 0}
    fold_counts = {fold: 0 for fold in range(5)}
    for row in rows:
        if row.split not in counts:
            raise LeakageError(f"unknown ledger split: {row.split!r}")
        counts[row.split] += 1
        if row.split == "test":
            if row.source_partition != "test" or row.oof_fold is not None:
                raise LeakageError("official test row must remain test and have no OOF fold")
        else:
            if row.source_partition != "train":
                raise LeakageError("official train row was not retained inside development partitions")
            if row.split in {"train_core", "validation"}:
                if row.oof_fold not in fold_counts:
                    raise LeakageError("fit-pool row must have an OOF fold in [0, 4]")
                fold_counts[int(row.oof_fold)] += 1
            elif row.oof_fold is not None:
                raise LeakageError("calibration_reserved must not receive an OOF fold")

    expected_counts = {
        "train_core": 40_000,
        "validation": 5_000,
        "calibration_reserved": 5_000,
        "test": 10_000,
    }
    if counts != expected_counts:
        raise LeakageError(f"ledger split counts changed: {counts}; expected={expected_counts}")
    if fold_counts != {fold: 9_000 for fold in range(5)}:
        raise LeakageError(f"OOF fold counts changed: {fold_counts}; expected 9,000 per fold")


def ledger_csv_bytes(rows: Sequence[LedgerRow]) -> bytes:
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=LEDGER_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        item = asdict(row)
        item["oof_fold"] = "" if row.oof_fold is None else row.oof_fold
        writer.writerow(item)
    return buffer.getvalue().encode("utf-8")


def write_ledger_package(
    rows: Sequence[LedgerRow],
    source_hashes: Mapping[str, str],
    output_dir: Path,
) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_bytes = ledger_csv_bytes(rows)
    ledger_path = output_dir / "split_ledger.csv"
    ledger_path.write_bytes(csv_bytes)
    ledger_sha = sha256(csv_bytes).hexdigest()

    manifest: dict[str, object] = {
        "protocol_id": PROTOCOL_ID,
        "ledger_format": "csv/utf-8/lf",
        "sample_id_rule": "sha256(exact 3072 uint8 bytes as stored in verified CIFAR-10 Python batch row)",
        "row_order": "sample_id ascending",
        "ledger_file": ledger_path.name,
        "ledger_sha256": ledger_sha,
        "source_batch_sha256": {name: source_hashes[name] for name, _ in CIFAR_BATCH_SPECS},
        "counts": {
            "train_core": 40_000,
            "validation": 5_000,
            "calibration_reserved": 5_000,
            "test": 10_000,
            "oof_fold_0": 9_000,
            "oof_fold_1": 9_000,
            "oof_fold_2": 9_000,
            "oof_fold_3": 9_000,
            "oof_fold_4": 9_000,
        },
        "security_boundary": "Python batches are unpickled only after all six file hashes match the user-supplied frozen hash map.",
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest_path = output_dir / "split_ledger.manifest.json"
    manifest_path.write_bytes(manifest_bytes)
    return manifest


def _load_hash_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise LeakageError("expected-source hash JSON must be an object keyed by batch filename")
    return payload


def _write_inventory(root: Path, output: Path) -> None:
    hashes = inventory_cifar_python_dir(root)
    Path(output).write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the frozen AB-GEN Clean Baseline v1 split ledger")
    parser.add_argument("--cifar-python-dir", type=Path, required=True)
    parser.add_argument("--inventory-only", type=Path, metavar="OUT_JSON")
    parser.add_argument("--expected-source-hashes", type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.inventory_only is not None:
        if args.expected_source_hashes is not None or args.out_dir is not None:
            parser.error("--inventory-only cannot be combined with ledger-build arguments")
        _write_inventory(args.cifar_python_dir, args.inventory_only)
        print(f"PASS: wrote hash-only inventory to {args.inventory_only}")
        return 0

    if args.expected_source_hashes is None or args.out_dir is None:
        parser.error("ledger build requires --expected-source-hashes and --out-dir")

    expected = _load_hash_json(args.expected_source_hashes)
    samples, observed = load_verified_cifar_python_batches(args.cifar_python_dir, expected)
    rows = build_ledger_rows(samples)
    manifest = write_ledger_package(rows, observed, args.out_dir)
    print(f"PASS: wrote 60,000-row split ledger; sha256={manifest['ledger_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
