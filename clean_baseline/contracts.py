from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Mapping, Sequence


class LeakageError(RuntimeError):
    """Raised when a Clean Baseline v1 evidence/data boundary is violated."""


KNOWN_SPLITS = frozenset({"train_core", "validation", "calibration_reserved", "test"})

# A split-level guard is only one layer. OOF producer/held-out exclusion is
# enforced separately by assert_oof_exclusion().
FIT_PHASE_ALLOWED_SPLITS: Mapping[str, frozenset[str]] = {
    "development_preprocessing_fit": frozenset({"train_core"}),
    "development_n1_fit": frozenset({"train_core"}),
    "oof_producer_fit": frozenset({"train_core", "validation"}),
    "n2_oof_fit": frozenset({"train_core", "validation"}),
    "final_preprocessing_refit": frozenset({"train_core", "validation"}),
    "final_n1_refit": frozenset({"train_core", "validation"}),
    # Reserved for downstream issue #9. It must not be used to improve the
    # Clean Baseline v1 accuracy candidate.
    "downstream_calibration_fit": frozenset({"calibration_reserved"}),
}


@dataclass(frozen=True)
class RawSample:
    sample_id: str
    label: int
    source_partition: str  # "train" or "test"


@dataclass(frozen=True)
class SampleRecord:
    sample_id: str
    label: int
    split: str


def _validate_sample_id(sample_id: str) -> None:
    if not isinstance(sample_id, str) or len(sample_id) != 64:
        raise LeakageError(f"sample_id must be a 64-character SHA-256 hex string: {sample_id!r}")
    try:
        int(sample_id, 16)
    except ValueError as exc:
        raise LeakageError(f"sample_id is not valid hexadecimal: {sample_id!r}") from exc


def hash_sample_bytes(raw_image_bytes: bytes) -> str:
    """Return the stable Clean Baseline v1 sample identity."""
    if not isinstance(raw_image_bytes, (bytes, bytearray, memoryview)):
        raise TypeError("raw_image_bytes must be bytes-like")
    return sha256(bytes(raw_image_bytes)).hexdigest()


class SplitLedger:
    """Immutable lookup/validation layer for frozen sample identities."""

    def __init__(self, records: Iterable[SampleRecord]):
        records_tuple = tuple(records)
        if not records_tuple:
            raise LeakageError("split ledger is empty")

        by_id: dict[str, SampleRecord] = {}
        for record in records_tuple:
            _validate_sample_id(record.sample_id)
            if record.sample_id in by_id:
                raise LeakageError(f"duplicate sample_id in split ledger: {record.sample_id}")
            if record.split not in KNOWN_SPLITS:
                raise LeakageError(f"unknown split {record.split!r} for {record.sample_id}")
            if not isinstance(record.label, int) or not 0 <= record.label <= 9:
                raise LeakageError(f"invalid CIFAR-10 label {record.label!r} for {record.sample_id}")
            by_id[record.sample_id] = record

        self._records = records_tuple
        self._by_id = by_id

    @property
    def records(self) -> tuple[SampleRecord, ...]:
        return self._records

    def ids_for(self, *splits: str) -> frozenset[str]:
        requested = frozenset(splits)
        unknown = requested - KNOWN_SPLITS
        if unknown:
            raise LeakageError(f"unknown requested splits: {sorted(unknown)}")
        return frozenset(record.sample_id for record in self._records if record.split in requested)

    def record_for(self, sample_id: str) -> SampleRecord:
        try:
            return self._by_id[sample_id]
        except KeyError as exc:
            raise LeakageError(f"sample_id is not present in frozen split ledger: {sample_id}") from exc

    def assert_fit_scope(self, sample_ids: Iterable[str], phase: str) -> None:
        """Reject samples outside the phase's frozen fitting scope.

        Final-test samples are always forbidden from every fit phase, even if a
        future caller accidentally edits a policy mapping.
        """
        if phase not in FIT_PHASE_ALLOWED_SPLITS:
            raise LeakageError(f"unknown fit phase: {phase!r}")

        ids = tuple(sample_ids)
        if not ids:
            raise LeakageError(f"fit phase {phase!r} received no sample IDs")

        allowed = FIT_PHASE_ALLOWED_SPLITS[phase]
        observed_splits: set[str] = set()
        for sample_id in ids:
            record = self.record_for(sample_id)
            observed_splits.add(record.split)
            if record.split == "test":
                raise LeakageError(
                    f"FINAL TEST LEAKAGE: fit phase {phase!r} received test sample {sample_id}"
                )
            if record.split not in allowed:
                raise LeakageError(
                    f"fit-scope violation: phase={phase!r}, sample={sample_id}, "
                    f"split={record.split!r}, allowed={sorted(allowed)}"
                )

        if not observed_splits:
            raise LeakageError(f"fit phase {phase!r} resolved no frozen split identities")

    def assert_exact_split_counts(self) -> None:
        expected = {
            "train_core": 40_000,
            "validation": 5_000,
            "calibration_reserved": 5_000,
            "test": 10_000,
        }
        observed = {split: 0 for split in KNOWN_SPLITS}
        per_class = {split: {label: 0 for label in range(10)} for split in KNOWN_SPLITS}

        for record in self._records:
            observed[record.split] += 1
            per_class[record.split][record.label] += 1

        if observed != expected:
            raise LeakageError(f"unexpected Clean Baseline v1 split counts: {observed}; expected {expected}")

        expected_per_class = {
            "train_core": 4_000,
            "validation": 500,
            "calibration_reserved": 500,
            "test": 1_000,
        }
        for split, count in expected_per_class.items():
            bad = {label: n for label, n in per_class[split].items() if n != count}
            if bad:
                raise LeakageError(
                    f"split {split!r} is not class-balanced as frozen by protocol: {bad}; "
                    f"expected {count} per class"
                )


def assign_development_splits(samples: Sequence[RawSample]) -> tuple[SampleRecord, ...]:
    """Apply the frozen no-RNG CIFAR-10 split contract.

    Official train: per class, sample_id-sorted ranks 0..3999 train_core,
    4000..4499 validation, 4500..4999 calibration_reserved.
    Official test: remains test.
    """
    if len(samples) != 60_000:
        raise LeakageError(f"expected 60,000 CIFAR-10 samples, received {len(samples)}")

    seen: set[str] = set()
    train_by_class: dict[int, list[RawSample]] = {label: [] for label in range(10)}
    test_by_class: dict[int, list[RawSample]] = {label: [] for label in range(10)}

    for sample in samples:
        _validate_sample_id(sample.sample_id)
        if sample.sample_id in seen:
            raise LeakageError(f"duplicate RAW sample_id: {sample.sample_id}")
        seen.add(sample.sample_id)

        if not isinstance(sample.label, int) or not 0 <= sample.label <= 9:
            raise LeakageError(f"invalid CIFAR-10 label: {sample.label!r}")
        if sample.source_partition == "train":
            train_by_class[sample.label].append(sample)
        elif sample.source_partition == "test":
            test_by_class[sample.label].append(sample)
        else:
            raise LeakageError(f"unknown CIFAR-10 source partition: {sample.source_partition!r}")

    records: list[SampleRecord] = []
    for label in range(10):
        train = sorted(train_by_class[label], key=lambda sample: sample.sample_id)
        test = sorted(test_by_class[label], key=lambda sample: sample.sample_id)
        if len(train) != 5_000:
            raise LeakageError(f"class {label}: expected 5,000 official-train samples, got {len(train)}")
        if len(test) != 1_000:
            raise LeakageError(f"class {label}: expected 1,000 official-test samples, got {len(test)}")

        for rank, sample in enumerate(train):
            if rank < 4_000:
                split = "train_core"
            elif rank < 4_500:
                split = "validation"
            else:
                split = "calibration_reserved"
            records.append(SampleRecord(sample.sample_id, label, split))

        records.extend(SampleRecord(sample.sample_id, label, "test") for sample in test)

    ledger = SplitLedger(records)
    ledger.assert_exact_split_counts()
    return ledger.records


def assign_oof_folds(ledger: SplitLedger, folds: int = 5) -> dict[str, int]:
    """Return deterministic class-stratified fold IDs for train_core+validation."""
    if folds != 5:
        raise LeakageError("Clean Baseline v1 freezes OOF to exactly five folds")

    assignment: dict[str, int] = {}
    for label in range(10):
        fit_pool = sorted(
            (
                record
                for record in ledger.records
                if record.label == label and record.split in {"train_core", "validation"}
            ),
            key=lambda record: record.sample_id,
        )
        if len(fit_pool) != 4_500:
            raise LeakageError(
                f"class {label}: expected 4,500 fit-pool samples for OOF, got {len(fit_pool)}"
            )
        for rank, record in enumerate(fit_pool):
            assignment[record.sample_id] = rank % folds

    if len(assignment) != 45_000:
        raise LeakageError(f"expected 45,000 OOF assignments, got {len(assignment)}")
    return assignment


def assert_oof_exclusion(
    held_out_ids: Iterable[str],
    producer_training_ids: Iterable[str],
    *,
    context: str = "OOF producer",
) -> None:
    """Prove a held-out row was not used by the pipeline that produced it."""
    held_out = frozenset(held_out_ids)
    producer = frozenset(producer_training_ids)
    if not held_out:
        raise LeakageError(f"{context}: held-out set is empty")
    if not producer:
        raise LeakageError(f"{context}: producer training set is empty")
    overlap = held_out & producer
    if overlap:
        preview = sorted(overlap)[:5]
        raise LeakageError(
            f"OOF LEAKAGE in {context}: {len(overlap)} held-out sample(s) were present in "
            f"producer training data; first={preview}"
        )


def _require_sha256(value: object, path: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise LeakageError(f"manifest field {path} must contain a 64-character SHA-256 hex value")
    try:
        int(value, 16)
    except ValueError as exc:
        raise LeakageError(f"manifest field {path} is not valid SHA-256 hex") from exc


def _nested_get(mapping: Mapping[str, object], *path: str) -> object:
    current: object = mapping
    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            raise LeakageError(f"manifest missing required field: {'.'.join(path)}")
        current = current[part]
    return current


def assert_manifest_ready_for_final_test(manifest: Mapping[str, object]) -> None:
    """Fail closed unless a candidate is sealed before final-test access."""
    if _nested_get(manifest, "protocol_id") != "abgen-clean-baseline-v1":
        raise LeakageError("manifest protocol_id is not abgen-clean-baseline-v1")

    candidate_id = _nested_get(manifest, "candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip() or candidate_id == "UNSET":
        raise LeakageError("manifest candidate_id is not frozen")

    source_commit = _nested_get(manifest, "source_commit")
    if not isinstance(source_commit, str) or len(source_commit) < 7 or source_commit == "UNSET":
        raise LeakageError("manifest source_commit is not frozen")

    for path in (
        ("dataset", "raw_source_sha256"),
        ("splits", "ledger_sha256"),
        ("config", "frozen_config_sha256"),
        ("environment", "lock_sha256"),
        ("features", "feature_order_sha256"),
        ("artifacts", "pretest_manifest_sha256"),
    ):
        value = _nested_get(manifest, *path)
        _require_sha256(value, ".".join(path))

    commands = _nested_get(manifest, "commands")
    if not isinstance(commands, Sequence) or isinstance(commands, (str, bytes)) or not commands:
        raise LeakageError("manifest commands must retain at least one exact command")

    final_test = _nested_get(manifest, "final_test")
    if not isinstance(final_test, Mapping):
        raise LeakageError("manifest final_test must be an object")
    if final_test.get("sealed") is not True:
        raise LeakageError("final test is not sealed")
    if final_test.get("decisions_frozen") is not True:
        raise LeakageError("model decisions are not frozen")
    if final_test.get("access_count_before_seal") != 0:
        raise LeakageError("final test was accessed before the candidate seal")

    leakage = _nested_get(manifest, "leakage_audit")
    if not isinstance(leakage, Mapping) or leakage.get("pretest_status") != "PASS":
        raise LeakageError("pre-test leakage audit is not PASS")

    invariance = _nested_get(manifest, "batch_invariance")
    if not isinstance(invariance, Mapping) or invariance.get("pretest_status") != "PASS":
        raise LeakageError("pre-test batch-invariance gate is not PASS")

    calibration = _nested_get(manifest, "calibration_reserved")
    if not isinstance(calibration, Mapping):
        raise LeakageError("manifest calibration_reserved must be an object")
    if calibration.get("used_to_tune_clean_baseline_accuracy") is not False:
        raise LeakageError("calibration_reserved was used to tune Clean Baseline v1 accuracy")
