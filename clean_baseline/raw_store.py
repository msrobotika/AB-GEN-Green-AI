from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .contracts import LeakageError, SampleRecord, SplitLedger, hash_sample_bytes
from .ledger_io import read_ledger_rows, verify_ledger_package
from .split_ledger import (
    CIFAR_BATCH_SPECS,
    CIFAR_IMAGE_BYTES,
    LedgerRow,
    inventory_cifar_python_dir,
    sha256_file,
)
from .stage_audit import StageReceipt, authorize_transform, make_stage_receipt


@dataclass(frozen=True)
class RawBatch:
    sample_ids: tuple[str, ...]
    labels: np.ndarray
    values: np.ndarray


@dataclass(frozen=True)
class NormalizedBatch:
    sample_ids: tuple[str, ...]
    labels: np.ndarray
    values: np.ndarray
    receipt: StageReceipt


def cifar_raw_feature_names() -> tuple[str, ...]:
    names: list[str] = []
    for channel in ("R", "G", "B"):
        for index in range(32 * 32):
            names.append(f"raw_{channel}_{index:04d}")
    return tuple(names)


def _payload_value(payload: Mapping[object, object], *keys: object) -> object:
    for key in keys:
        if key in payload:
            return payload[key]
    raise LeakageError(f"CIFAR batch missing keys {keys!r}")


def _load_verified_batch(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Deserialize one CIFAR batch after its immediately preceding hash check."""
    with Path(path).open("rb") as handle:
        payload = pickle.load(handle, encoding="bytes")  # noqa: S301 - hash-bound CIFAR source only

    if not isinstance(payload, Mapping):
        raise LeakageError(f"unexpected CIFAR batch payload type in {Path(path).name}: {type(payload)!r}")

    data = np.asarray(_payload_value(payload, b"data", "data"))
    labels = np.asarray(_payload_value(payload, b"labels", "labels"))

    if data.shape != (10_000, CIFAR_IMAGE_BYTES):
        raise LeakageError(f"{Path(path).name}: expected data shape (10000, 3072), got {data.shape}")
    if data.dtype != np.uint8:
        raise LeakageError(f"{Path(path).name}: expected uint8 data, got {data.dtype}")
    if labels.shape != (10_000,):
        raise LeakageError(f"{Path(path).name}: expected labels shape (10000,), got {labels.shape}")
    if not np.issubdtype(labels.dtype, np.integer):
        raise LeakageError(f"{Path(path).name}: labels must be integer-valued, got {labels.dtype}")
    if np.any(labels < 0) or np.any(labels > 9):
        raise LeakageError(f"{Path(path).name}: labels contain values outside [0, 9]")

    return data, labels.astype(np.int64, copy=False)


def _require_sha256_map(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise LeakageError("split ledger manifest source_batch_sha256 must be an object")

    expected_names = {name for name, _ in CIFAR_BATCH_SPECS}
    if set(value) != expected_names:
        missing = sorted(expected_names - set(value))
        extra = sorted(set(value) - expected_names)
        raise LeakageError(f"source hash map mismatch; missing={missing}, extra={extra}")

    result: dict[str, str] = {}
    for name in sorted(expected_names):
        digest = value[name]
        if not isinstance(digest, str) or len(digest) != 64:
            raise LeakageError(f"invalid source SHA-256 for {name}: {digest!r}")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise LeakageError(f"invalid source SHA-256 hex for {name}: {digest!r}") from exc
        result[name] = digest.lower()
    return result


def _validate_row_source_contract(rows: Sequence[LedgerRow]) -> None:
    partition_by_file = dict(CIFAR_BATCH_SPECS)
    for row in rows:
        expected_partition = partition_by_file.get(row.source_file)
        if expected_partition is None:
            raise LeakageError(f"ledger references unexpected CIFAR source file: {row.source_file!r}")
        if row.source_partition != expected_partition:
            raise LeakageError(
                f"ledger source partition mismatch for {row.sample_id}: "
                f"file={row.source_file!r} implies {expected_partition!r}, "
                f"ledger records {row.source_partition!r}"
            )
        if not 0 <= row.source_index < 10_000:
            raise LeakageError(
                f"ledger source index outside CIFAR batch bounds for {row.sample_id}: {row.source_index}"
            )


class VerifiedCifarRawStore:
    """Hash-bound, ledger-bound lazy reader for the frozen CIFAR-10 RAW source.

    Opening the store performs no pickle deserialization. All six source-file
    hashes must match the already-frozen split-ledger manifest first. Individual
    CIFAR batch files are deserialized lazily only when an authorized transform
    requests samples from that file. Each file is re-hashed immediately before
    its first pickle load to close the hash-check/deserialization TOCTOU window.
    """

    def __init__(
        self,
        *,
        root: Path,
        rows: Sequence[LedgerRow],
        expected_source_hashes: Mapping[str, str],
    ) -> None:
        self.root = Path(root)
        self.rows = tuple(rows)
        self.expected_source_hashes = dict(expected_source_hashes)
        _validate_row_source_contract(self.rows)

        self._row_by_id = {row.sample_id: row for row in self.rows}
        if len(self._row_by_id) != len(self.rows):
            raise LeakageError("RAW store ledger contains duplicate sample IDs")

        self.ledger = SplitLedger(
            SampleRecord(row.sample_id, row.label, row.split) for row in self.rows
        )
        self._batch_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    @classmethod
    def open(
        cls,
        *,
        cifar_python_dir: Path,
        ledger_path: Path,
        ledger_manifest_path: Path,
    ) -> "VerifiedCifarRawStore":
        manifest = verify_ledger_package(Path(ledger_path), Path(ledger_manifest_path))
        rows = read_ledger_rows(Path(ledger_path))
        expected = _require_sha256_map(manifest.get("source_batch_sha256"))

        observed = inventory_cifar_python_dir(Path(cifar_python_dir))
        for filename, expected_digest in expected.items():
            observed_digest = observed.get(filename)
            if observed_digest is None:
                raise LeakageError(f"RAW source inventory missing {filename}")
            if observed_digest.lower() != expected_digest:
                raise LeakageError(
                    f"RAW source hash mismatch for {filename}: "
                    f"observed={observed_digest}, expected={expected_digest}"
                )

        return cls(root=Path(cifar_python_dir), rows=rows, expected_source_hashes=expected)

    def _batch(self, filename: str) -> tuple[np.ndarray, np.ndarray]:
        if filename not in self.expected_source_hashes:
            raise LeakageError(f"attempted RAW access through unbound source file: {filename!r}")
        if filename not in self._batch_cache:
            path = self.root / filename
            observed = sha256_file(path)
            expected = self.expected_source_hashes[filename]
            if observed.lower() != expected.lower():
                raise LeakageError(
                    f"RAW source changed before deserialization for {filename}: "
                    f"observed={observed}, expected={expected}"
                )
            self._batch_cache[filename] = _load_verified_batch(path)
        return self._batch_cache[filename]

    def read(
        self,
        sample_ids: Sequence[str],
        *,
        purpose: str,
        final_test_authorized: bool = False,
    ) -> RawBatch:
        ids = authorize_transform(
            self.ledger,
            sample_ids,
            purpose=purpose,
            final_test_authorized=final_test_authorized,
        )

        values = np.empty((len(ids), CIFAR_IMAGE_BYTES), dtype=np.uint8)
        labels = np.empty((len(ids),), dtype=np.int64)

        for output_index, sample_id in enumerate(ids):
            try:
                row = self._row_by_id[sample_id]
            except KeyError as exc:
                raise LeakageError(f"RAW store has no provenance row for sample {sample_id}") from exc

            data, batch_labels = self._batch(row.source_file)
            raw_row = np.asarray(data[row.source_index], dtype=np.uint8)
            observed_id = hash_sample_bytes(raw_row.tobytes(order="C"))
            if observed_id != row.sample_id:
                raise LeakageError(
                    f"RAW sample identity mismatch for {row.sample_id}: observed={observed_id}"
                )

            observed_label = int(batch_labels[row.source_index])
            if observed_label != row.label:
                raise LeakageError(
                    f"RAW label mismatch for {row.sample_id}: observed={observed_label}, expected={row.label}"
                )

            values[output_index] = raw_row
            labels[output_index] = observed_label

        return RawBatch(sample_ids=ids, labels=labels, values=values)


def normalize_unit_float32(raw: RawBatch, *, purpose: str) -> NormalizedBatch:
    if raw.values.ndim != 2 or raw.values.shape[1] != CIFAR_IMAGE_BYTES:
        raise LeakageError(
            f"RAW normalization expects shape (N, {CIFAR_IMAGE_BYTES}), got {raw.values.shape}"
        )
    if raw.values.dtype != np.uint8:
        raise LeakageError(f"RAW normalization expects uint8 input, got {raw.values.dtype}")
    if raw.labels.shape != (len(raw.sample_ids),):
        raise LeakageError("RAW normalization label/sample count mismatch")

    normalized = raw.values.astype(np.float32) / np.float32(255.0)
    if not np.isfinite(normalized).all():
        raise LeakageError("RAW normalization produced non-finite values")
    if np.any(normalized < 0.0) or np.any(normalized > 1.0):
        raise LeakageError("RAW normalization produced values outside [0, 1]")

    feature_names = cifar_raw_feature_names()
    receipt = make_stage_receipt(
        stage="raw_unit_scale",
        operation="transform",
        purpose=purpose,
        input_values=raw.values,
        output_values=normalized,
        sample_ids=raw.sample_ids,
        input_feature_names=feature_names,
        output_feature_names=feature_names,
    )

    return NormalizedBatch(
        sample_ids=raw.sample_ids,
        labels=raw.labels.copy(),
        values=normalized,
        receipt=receipt,
    )
