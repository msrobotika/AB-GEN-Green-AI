from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .contracts import LeakageError, SplitLedger, assert_oof_exclusion


def _hash_ordered_strings(values: Sequence[str]) -> str:
    digest = sha256()
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def hash_sample_id_order(sample_ids: Iterable[str]) -> str:
    ids = tuple(sample_ids)
    if not ids:
        raise LeakageError("cannot hash an empty sample-ID sequence")
    if len(ids) != len(set(ids)):
        raise LeakageError("sample-ID sequence contains duplicates")
    return _hash_ordered_strings(ids)


def hash_feature_order(feature_names: Iterable[str]) -> str:
    names = tuple(feature_names)
    if not names:
        raise LeakageError("feature order cannot be empty")
    if len(names) != len(set(names)):
        raise LeakageError("feature order contains duplicate names")
    return _hash_ordered_strings(names)


def _shape_of(values: object) -> tuple[int, ...]:
    shape = getattr(values, "shape", None)
    if shape is None:
        raise LeakageError("stage value does not expose a shape")
    try:
        normalized = tuple(int(dim) for dim in shape)
    except (TypeError, ValueError) as exc:
        raise LeakageError(f"invalid stage shape: {shape!r}") from exc
    if not normalized or any(dim < 0 for dim in normalized):
        raise LeakageError(f"invalid stage shape: {normalized!r}")
    return normalized


def _dtype_of(values: object) -> str:
    dtype = getattr(values, "dtype", None)
    if dtype is None:
        raise LeakageError("stage value does not expose a dtype")
    return str(dtype)


@dataclass(frozen=True)
class TensorSignature:
    sample_count: int
    shape: tuple[int, ...]
    dtype: str
    sample_id_order_sha256: str
    feature_order_sha256: str | None


@dataclass(frozen=True)
class FitAuthorization:
    stage: str
    phase: str
    sample_count: int
    sample_id_order_sha256: str
    split_counts: Mapping[str, int]


@dataclass(frozen=True)
class OOFProducerAuthorization:
    stage: str
    fold_id: int
    producer_sample_count: int
    held_out_sample_count: int
    producer_ids_sha256: str
    held_out_ids_sha256: str


@dataclass(frozen=True)
class StageReceipt:
    protocol_id: str
    stage: str
    operation: str
    purpose: str
    input_signature: TensorSignature
    output_signature: TensorSignature
    fit_authorization_sha256: str | None = None
    artifact_sha256: str | None = None


def tensor_signature(
    values: object,
    sample_ids: Iterable[str],
    *,
    feature_names: Iterable[str] | None = None,
) -> TensorSignature:
    ids = tuple(sample_ids)
    shape = _shape_of(values)
    if shape[0] != len(ids):
        raise LeakageError(
            f"stage row/sample mismatch: tensor first dimension={shape[0]}, sample IDs={len(ids)}"
        )
    feature_hash = None if feature_names is None else hash_feature_order(tuple(feature_names))
    return TensorSignature(
        sample_count=len(ids),
        shape=shape,
        dtype=_dtype_of(values),
        sample_id_order_sha256=hash_sample_id_order(ids),
        feature_order_sha256=feature_hash,
    )


def authorize_fit(
    ledger: SplitLedger,
    sample_ids: Iterable[str],
    *,
    stage: str,
    phase: str,
) -> FitAuthorization:
    ids = tuple(sample_ids)
    if not stage.strip():
        raise LeakageError("fit authorization requires a non-empty stage name")
    if len(ids) != len(set(ids)):
        raise LeakageError(f"fit stage {stage!r} received duplicate sample IDs")
    ledger.assert_fit_scope(ids, phase)

    split_counts: dict[str, int] = {}
    for sample_id in ids:
        split = ledger.record_for(sample_id).split
        split_counts[split] = split_counts.get(split, 0) + 1

    return FitAuthorization(
        stage=stage,
        phase=phase,
        sample_count=len(ids),
        sample_id_order_sha256=hash_sample_id_order(ids),
        split_counts=dict(sorted(split_counts.items())),
    )


def authorize_oof_producer(
    ledger: SplitLedger,
    producer_training_ids: Iterable[str],
    held_out_ids: Iterable[str],
    *,
    stage: str,
    fold_id: int,
) -> OOFProducerAuthorization:
    producer = tuple(producer_training_ids)
    held_out = tuple(held_out_ids)
    if fold_id not in range(5):
        raise LeakageError(f"OOF fold_id must be in [0, 4], got {fold_id}")
    authorize_fit(ledger, producer, stage=stage, phase="oof_producer_fit")
    assert_oof_exclusion(held_out, producer, context=f"{stage}/fold-{fold_id}")

    for sample_id in held_out:
        record = ledger.record_for(sample_id)
        if record.split not in {"train_core", "validation"}:
            raise LeakageError(
                f"OOF held-out sample {sample_id} is in split {record.split!r}; "
                "only train_core/validation may produce N2 OOF rows"
            )

    return OOFProducerAuthorization(
        stage=stage,
        fold_id=fold_id,
        producer_sample_count=len(producer),
        held_out_sample_count=len(held_out),
        producer_ids_sha256=hash_sample_id_order(producer),
        held_out_ids_sha256=hash_sample_id_order(held_out),
    )


def authorize_transform(
    ledger: SplitLedger,
    sample_ids: Iterable[str],
    *,
    purpose: str,
    final_test_authorized: bool = False,
) -> tuple[str, ...]:
    ids = tuple(sample_ids)
    if not ids:
        raise LeakageError(f"transform purpose {purpose!r} received no sample IDs")
    if len(ids) != len(set(ids)):
        raise LeakageError(f"transform purpose {purpose!r} received duplicate sample IDs")
    if not purpose.strip():
        raise LeakageError("transform purpose must be non-empty")

    for sample_id in ids:
        record = ledger.record_for(sample_id)
        if record.split == "test" and not final_test_authorized:
            raise LeakageError(
                f"FINAL TEST SEALED: transform purpose {purpose!r} attempted to access test sample "
                f"{sample_id} without preflight authorization"
            )
    return ids


def _authorization_hash(authorization: FitAuthorization | OOFProducerAuthorization | None) -> str | None:
    if authorization is None:
        return None
    payload = json.dumps(asdict(authorization), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(payload).hexdigest()


def make_stage_receipt(
    *,
    stage: str,
    operation: str,
    purpose: str,
    input_values: object,
    output_values: object,
    sample_ids: Iterable[str],
    input_feature_names: Iterable[str] | None = None,
    output_feature_names: Iterable[str] | None = None,
    fit_authorization: FitAuthorization | OOFProducerAuthorization | None = None,
    artifact_sha256: str | None = None,
) -> StageReceipt:
    if operation not in {"fit_transform", "transform", "predict", "predict_scores"}:
        raise LeakageError(f"unsupported stage operation: {operation!r}")
    if not stage.strip() or not purpose.strip():
        raise LeakageError("stage and purpose must be non-empty")

    ids = tuple(sample_ids)
    input_sig = tensor_signature(input_values, ids, feature_names=input_feature_names)
    output_sig = tensor_signature(output_values, ids, feature_names=output_feature_names)
    if input_sig.sample_id_order_sha256 != output_sig.sample_id_order_sha256:
        raise LeakageError("stage input/output sample identity order changed unexpectedly")

    if artifact_sha256 is not None:
        if len(artifact_sha256) != 64:
            raise LeakageError("artifact_sha256 must be a 64-character SHA-256 hex string")
        try:
            int(artifact_sha256, 16)
        except ValueError as exc:
            raise LeakageError("artifact_sha256 is not hexadecimal") from exc

    return StageReceipt(
        protocol_id="abgen-clean-baseline-v1",
        stage=stage,
        operation=operation,
        purpose=purpose,
        input_signature=input_sig,
        output_signature=output_sig,
        fit_authorization_sha256=_authorization_hash(fit_authorization),
        artifact_sha256=artifact_sha256,
    )


def write_stage_receipts(receipts: Sequence[StageReceipt], path: Path) -> str:
    if not receipts:
        raise LeakageError("cannot write an empty stage receipt log")
    lines = [json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":")) for receipt in receipts]
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    Path(path).write_bytes(payload)
    return sha256(payload).hexdigest()
