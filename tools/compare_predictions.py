#!/usr/bin/env python3
"""Compare two AB-GEN prediction CSV exports by stable sample ID.

Required columns:
    sample_id,predicted_label

Optional columns:
    true_label
    score_*      (for example score_airplane, score_automobile, ...)

The comparison is independent of row order. Predicted labels are compared
exactly. Score columns present in both files are compared numerically with an
absolute tolerance. A JSON report can be retained as reproduction evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple


REQUIRED_COLUMNS = {"sample_id", "predicted_label"}


class PredictionFormatError(ValueError):
    """Raised when a prediction export is malformed."""


def _read_predictions(path: Path) -> Tuple[Dict[str, dict], List[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise PredictionFormatError(f"{path}: missing CSV header")

        fieldnames = [name.strip() for name in reader.fieldnames if name is not None]
        missing = REQUIRED_COLUMNS.difference(fieldnames)
        if missing:
            raise PredictionFormatError(
                f"{path}: missing required columns: {', '.join(sorted(missing))}"
            )

        rows: Dict[str, dict] = {}
        for line_number, raw_row in enumerate(reader, start=2):
            row = {str(key).strip(): (value if value is not None else "") for key, value in raw_row.items()}
            sample_id = row["sample_id"].strip()
            if not sample_id:
                raise PredictionFormatError(f"{path}:{line_number}: empty sample_id")
            if sample_id in rows:
                raise PredictionFormatError(
                    f"{path}:{line_number}: duplicate sample_id {sample_id!r}"
                )
            if not row["predicted_label"].strip():
                raise PredictionFormatError(
                    f"{path}:{line_number}: empty predicted_label for {sample_id!r}"
                )
            rows[sample_id] = row

    if not rows:
        raise PredictionFormatError(f"{path}: contains no prediction rows")

    return rows, fieldnames


def _score_columns(fieldnames: Iterable[str]) -> List[str]:
    return sorted(name for name in fieldnames if name.startswith("score_"))


def _parse_finite_float(value: str, *, path: Path, sample_id: str, column: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise PredictionFormatError(
            f"{path}: non-numeric {column!r} for sample_id {sample_id!r}: {value!r}"
        ) from exc
    if not math.isfinite(parsed):
        raise PredictionFormatError(
            f"{path}: non-finite {column!r} for sample_id {sample_id!r}: {value!r}"
        )
    return parsed


def compare_prediction_files(
    reference_path: Path,
    candidate_path: Path,
    *,
    atol: float = 1e-9,
    max_mismatches: int = 50,
) -> Mapping[str, object]:
    if atol < 0:
        raise ValueError("atol must be >= 0")
    if max_mismatches < 1:
        raise ValueError("max_mismatches must be >= 1")

    reference, ref_fields = _read_predictions(reference_path)
    candidate, cand_fields = _read_predictions(candidate_path)

    ref_ids = set(reference)
    cand_ids = set(candidate)
    missing_in_candidate = sorted(ref_ids - cand_ids)
    extra_in_candidate = sorted(cand_ids - ref_ids)
    common_ids = sorted(ref_ids & cand_ids)

    label_mismatches: List[str] = []
    true_label_mismatches: List[str] = []

    true_label_comparable = "true_label" in ref_fields and "true_label" in cand_fields

    ref_scores = set(_score_columns(ref_fields))
    cand_scores = set(_score_columns(cand_fields))
    common_score_columns = sorted(ref_scores & cand_scores)
    score_only_reference = sorted(ref_scores - cand_scores)
    score_only_candidate = sorted(cand_scores - ref_scores)

    score_stats = {
        column: {
            "mismatch_count": 0,
            "max_abs_delta": 0.0,
            "mean_abs_delta": 0.0,
        }
        for column in common_score_columns
    }
    score_delta_sums = {column: 0.0 for column in common_score_columns}
    score_mismatch_ids: Dict[str, List[str]] = {column: [] for column in common_score_columns}

    for sample_id in common_ids:
        ref_row = reference[sample_id]
        cand_row = candidate[sample_id]

        if ref_row["predicted_label"].strip() != cand_row["predicted_label"].strip():
            if len(label_mismatches) < max_mismatches:
                label_mismatches.append(sample_id)

        if true_label_comparable:
            if ref_row["true_label"].strip() != cand_row["true_label"].strip():
                if len(true_label_mismatches) < max_mismatches:
                    true_label_mismatches.append(sample_id)

        for column in common_score_columns:
            ref_value = _parse_finite_float(
                ref_row[column], path=reference_path, sample_id=sample_id, column=column
            )
            cand_value = _parse_finite_float(
                cand_row[column], path=candidate_path, sample_id=sample_id, column=column
            )
            delta = abs(ref_value - cand_value)
            score_delta_sums[column] += delta
            score_stats[column]["max_abs_delta"] = max(
                score_stats[column]["max_abs_delta"], delta
            )
            if delta > atol:
                score_stats[column]["mismatch_count"] += 1
                if len(score_mismatch_ids[column]) < max_mismatches:
                    score_mismatch_ids[column].append(sample_id)

    for column in common_score_columns:
        if common_ids:
            score_stats[column]["mean_abs_delta"] = score_delta_sums[column] / len(common_ids)
        score_stats[column]["mismatch_sample_ids"] = score_mismatch_ids[column]

    total_reference = len(reference)
    total_candidate = len(candidate)
    compared = len(common_ids)
    label_mismatch_count = sum(
        1
        for sample_id in common_ids
        if reference[sample_id]["predicted_label"].strip()
        != candidate[sample_id]["predicted_label"].strip()
    )
    true_label_mismatch_count = 0
    if true_label_comparable:
        true_label_mismatch_count = sum(
            1
            for sample_id in common_ids
            if reference[sample_id]["true_label"].strip()
            != candidate[sample_id]["true_label"].strip()
        )

    score_mismatch_total = sum(
        int(stats["mismatch_count"]) for stats in score_stats.values()
    )

    sample_sets_match = not missing_in_candidate and not extra_in_candidate
    labels_match = sample_sets_match and label_mismatch_count == 0
    true_labels_match = (not true_label_comparable) or true_label_mismatch_count == 0
    comparable_scores_match = score_mismatch_total == 0
    overall_match = labels_match and true_labels_match and comparable_scores_match

    return {
        "reference_file": reference_path.name,
        "candidate_file": candidate_path.name,
        "absolute_tolerance": atol,
        "reference_rows": total_reference,
        "candidate_rows": total_candidate,
        "compared_rows": compared,
        "sample_sets_match": sample_sets_match,
        "missing_in_candidate_count": len(missing_in_candidate),
        "missing_in_candidate_sample_ids": missing_in_candidate[:max_mismatches],
        "extra_in_candidate_count": len(extra_in_candidate),
        "extra_in_candidate_sample_ids": extra_in_candidate[:max_mismatches],
        "predicted_label_mismatch_count": label_mismatch_count,
        "predicted_label_mismatch_sample_ids": label_mismatches,
        "predicted_label_agreement_rate": (
            (compared - label_mismatch_count) / compared if compared else 0.0
        ),
        "true_label_comparable": true_label_comparable,
        "true_label_mismatch_count": true_label_mismatch_count,
        "true_label_mismatch_sample_ids": true_label_mismatches,
        "common_score_columns": common_score_columns,
        "score_columns_only_in_reference": score_only_reference,
        "score_columns_only_in_candidate": score_only_candidate,
        "score_stats": score_stats,
        "scores_comparable": bool(common_score_columns),
        "comparable_scores_match": comparable_scores_match,
        "overall_match": overall_match,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="Historical/reference prediction CSV")
    parser.add_argument("candidate", type=Path, help="Candidate/reproduced prediction CSV")
    parser.add_argument(
        "--atol",
        type=float,
        default=1e-9,
        help="Absolute tolerance for common score_* columns (default: 1e-9)",
    )
    parser.add_argument(
        "--max-mismatches",
        type=int,
        default=50,
        help="Maximum sample IDs retained per mismatch category (default: 50)",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path for a machine-readable comparison report",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        report = compare_prediction_files(
            args.reference,
            args.candidate,
            atol=args.atol,
            max_mismatches=args.max_mismatches,
        )
    except (PredictionFormatError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.json_output:
        args.json_output.write_text(rendered + "\n", encoding="utf-8")

    return 0 if report["overall_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
