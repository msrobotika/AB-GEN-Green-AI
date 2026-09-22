from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .contracts import LeakageError
from .final_access import validate_final_test_access_token
from .ledger_io import read_ledger_rows
from .split_ledger import PROTOCOL_ID, sha256_file


SCORE_COLUMNS = tuple(f"score_{index}" for index in range(10))
PREDICTION_COLUMNS = ("sample_id", "true_label", "predicted_label", *SCORE_COLUMNS)
ALLOWED_SCORE_SEMANTICS = frozenset({"decision_scores", "logits", "uncalibrated_scores"})


@dataclass(frozen=True)
class PredictionRow:
    sample_id: str
    true_label: int
    predicted_label: int
    scores: tuple[float, ...]


@dataclass(frozen=True)
class ClassMetric:
    class_id: int
    support: int
    precision: float
    recall: float
    f1: float


def _argmax(scores: Sequence[float]) -> int:
    if len(scores) != 10:
        raise LeakageError(f"expected 10 class scores, got {len(scores)}")
    return max(range(10), key=lambda index: scores[index])


def read_prediction_rows(path: Path) -> tuple[PredictionRow, ...]:
    path = Path(path)
    rows: list[PredictionRow] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(PREDICTION_COLUMNS):
            raise LeakageError(
                f"prediction CSV columns changed: {reader.fieldnames!r}; expected={list(PREDICTION_COLUMNS)!r}"
            )
        for line_number, item in enumerate(reader, start=2):
            try:
                sample_id = item["sample_id"]
                true_label = int(item["true_label"])
                predicted_label = int(item["predicted_label"])
                scores = tuple(float(item[column]) for column in SCORE_COLUMNS)
            except (KeyError, TypeError, ValueError) as exc:
                raise LeakageError(f"invalid prediction row at line {line_number}") from exc

            if sample_id in seen:
                raise LeakageError(f"duplicate prediction sample_id at line {line_number}: {sample_id}")
            seen.add(sample_id)
            if not 0 <= true_label <= 9 or not 0 <= predicted_label <= 9:
                raise LeakageError(f"invalid class label at line {line_number}")
            if any(not math.isfinite(value) for value in scores):
                raise LeakageError(f"non-finite class score at line {line_number}")
            if _argmax(scores) != predicted_label:
                raise LeakageError(
                    f"predicted_label does not equal argmax(scores) at line {line_number}: "
                    f"predicted={predicted_label}, argmax={_argmax(scores)}"
                )
            rows.append(PredictionRow(sample_id, true_label, predicted_label, scores))
    return tuple(rows)


def validate_final_predictions(
    rows: Sequence[PredictionRow],
    *,
    ledger_path: Path,
) -> tuple[PredictionRow, ...]:
    ledger = read_ledger_rows(Path(ledger_path))
    test_rows = {row.sample_id: row for row in ledger if row.split == "test"}
    if len(test_rows) != 10_000:
        raise LeakageError(f"frozen ledger must contain 10,000 test rows, got {len(test_rows)}")
    if len(rows) != 10_000:
        raise LeakageError(f"final prediction file must contain exactly 10,000 rows, got {len(rows)}")

    row_by_id = {row.sample_id: row for row in rows}
    if len(row_by_id) != 10_000:
        raise LeakageError("final prediction sample IDs are not unique")
    expected_ids = set(test_rows)
    observed_ids = set(row_by_id)
    missing = expected_ids - observed_ids
    extra = observed_ids - expected_ids
    if missing or extra:
        raise LeakageError(
            f"final prediction IDs do not exactly match frozen test split: missing={len(missing)}, extra={len(extra)}"
        )

    canonical: list[PredictionRow] = []
    for sample_id in sorted(expected_ids):
        prediction = row_by_id[sample_id]
        expected_label = test_rows[sample_id].label
        if prediction.true_label != expected_label:
            raise LeakageError(
                f"true-label mismatch for {sample_id}: predictions={prediction.true_label}, ledger={expected_label}"
            )
        canonical.append(prediction)
    return tuple(canonical)


def confusion_matrix(rows: Sequence[PredictionRow]) -> list[list[int]]:
    matrix = [[0 for _ in range(10)] for _ in range(10)]
    for row in rows:
        matrix[row.true_label][row.predicted_label] += 1
    return matrix


def compute_metrics(rows: Sequence[PredictionRow]) -> dict[str, object]:
    if len(rows) != 10_000:
        raise LeakageError("metrics require the complete 10,000-row final test")
    matrix = confusion_matrix(rows)
    correct = sum(matrix[index][index] for index in range(10))
    class_metrics: list[ClassMetric] = []

    for class_id in range(10):
        tp = matrix[class_id][class_id]
        support = sum(matrix[class_id])
        predicted_count = sum(matrix[truth][class_id] for truth in range(10))
        precision = tp / predicted_count if predicted_count else 0.0
        recall = tp / support if support else 0.0
        f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
        class_metrics.append(ClassMetric(class_id, support, precision, recall, f1))

    macro_f1 = sum(metric.f1 for metric in class_metrics) / 10.0
    return {
        "correct_count": correct,
        "denominator": 10_000,
        "accuracy": correct / 10_000.0,
        "macro_f1": macro_f1,
        "per_class": [asdict(metric) for metric in class_metrics],
    }


def _canonical_prediction_bytes(rows: Sequence[PredictionRow]) -> bytes:
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(PREDICTION_COLUMNS)
    for row in rows:
        writer.writerow(
            [
                row.sample_id,
                row.true_label,
                row.predicted_label,
                *(repr(value) for value in row.scores),
            ]
        )
    return buffer.getvalue().encode("utf-8")


def _confusion_bytes(matrix: Sequence[Sequence[int]]) -> bytes:
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["true\\pred", *range(10)])
    for class_id, row in enumerate(matrix):
        writer.writerow([class_id, *row])
    return buffer.getvalue().encode("utf-8")


def build_final_result_package(
    *,
    access_token_path: Path,
    prediction_csv_path: Path,
    ledger_path: Path,
    score_semantics: str,
    output_dir: Path,
) -> Mapping[str, object]:
    if score_semantics not in ALLOWED_SCORE_SEMANTICS:
        raise LeakageError(
            f"score_semantics must be one of {sorted(ALLOWED_SCORE_SEMANTICS)}; "
            "calibrated probability terminology is reserved for the later calibration gate"
        )

    access_token_path = Path(access_token_path)
    prediction_csv_path = Path(prediction_csv_path)
    ledger_path = Path(ledger_path)
    token = validate_final_test_access_token(access_token_path)
    if token.get("split_ledger_sha256") != sha256_file(ledger_path):
        raise LeakageError("result package ledger does not match the authorized access token")

    rows = validate_final_predictions(read_prediction_rows(prediction_csv_path), ledger_path=ledger_path)
    metrics = compute_metrics(rows)
    matrix = confusion_matrix(rows)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    canonical_predictions = _canonical_prediction_bytes(rows)
    predictions_path = output_dir / "final_predictions.csv"
    predictions_path.write_bytes(canonical_predictions)

    metrics_payload = {
        "protocol_id": PROTOCOL_ID,
        "candidate_id": token["candidate_id"],
        "score_semantics": score_semantics,
        "probability_calibration_claimed": False,
        **metrics,
    }
    metrics_bytes = (json.dumps(metrics_payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    metrics_path = output_dir / "final_metrics.json"
    metrics_path.write_bytes(metrics_bytes)

    confusion_payload = _confusion_bytes(matrix)
    confusion_path = output_dir / "confusion_matrix.csv"
    confusion_path.write_bytes(confusion_payload)

    manifest = {
        "protocol_id": PROTOCOL_ID,
        "candidate_id": token["candidate_id"],
        "status": "FINAL_TEST_EVIDENCE_RETAINED",
        "access_token_path": access_token_path.resolve().as_posix(),
        "access_token_sha256": sha256_file(access_token_path),
        "authorized_manifest_sha256": token["authorized_manifest_sha256"],
        "authorization_record_sha256": token["authorization_record_sha256"],
        "split_ledger_sha256": token["split_ledger_sha256"],
        "input_prediction_csv_path": prediction_csv_path.resolve().as_posix(),
        "input_prediction_csv_sha256": sha256_file(prediction_csv_path),
        "score_semantics": score_semantics,
        "prediction_rule": "argmax(score_0..score_9), lowest class index on exact tie",
        "files": {
            "final_predictions.csv": sha256(canonical_predictions).hexdigest(),
            "final_metrics.json": sha256(metrics_bytes).hexdigest(),
            "confusion_matrix.csv": sha256(confusion_payload).hexdigest(),
        },
        "correct_count": metrics["correct_count"],
        "denominator": 10_000,
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "limits": [
            "This package records one authorized final-test result; it does not by itself establish fresh-environment reproduction.",
            "Scores are not described as calibrated probabilities.",
            "Energy/resource observations are not a Green AI benchmark unless separately measured under the controlled protocol.",
        ],
    }
    manifest_path = output_dir / "final_result_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canonicalize and verify Clean Baseline v1 final-test evidence")
    parser.add_argument("--access-token", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--score-semantics", choices=sorted(ALLOWED_SCORE_SEMANTICS), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        manifest = build_final_result_package(
            access_token_path=args.access_token,
            prediction_csv_path=args.predictions,
            ledger_path=args.ledger,
            score_semantics=args.score_semantics,
            output_dir=args.out_dir,
        )
    except (LeakageError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 2

    print(
        "PASS: retained final-test evidence for "
        f"{manifest['correct_count']}/{manifest['denominator']} correct; "
        f"accuracy={manifest['accuracy']:.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
