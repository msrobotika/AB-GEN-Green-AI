from pathlib import Path

import pytest

from tools.compare_predictions import PredictionFormatError, compare_prediction_files


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_exact_match_is_independent_of_row_order(tmp_path):
    reference = _write(
        tmp_path / "reference.csv",
        "sample_id,true_label,predicted_label,score_a,score_b\n"
        "a,0,0,0.9,0.1\n"
        "b,1,1,0.2,0.8\n",
    )
    candidate = _write(
        tmp_path / "candidate.csv",
        "sample_id,true_label,predicted_label,score_a,score_b\n"
        "b,1,1,0.2,0.8\n"
        "a,0,0,0.9,0.1\n",
    )

    report = compare_prediction_files(reference, candidate)

    assert report["sample_sets_match"] is True
    assert report["predicted_label_mismatch_count"] == 0
    assert report["predicted_label_agreement_rate"] == 1.0
    assert report["overall_match"] is True


def test_label_mismatch_is_reported(tmp_path):
    reference = _write(
        tmp_path / "reference.csv",
        "sample_id,predicted_label\n"
        "a,0\n"
        "b,1\n",
    )
    candidate = _write(
        tmp_path / "candidate.csv",
        "sample_id,predicted_label\n"
        "a,0\n"
        "b,2\n",
    )

    report = compare_prediction_files(reference, candidate)

    assert report["predicted_label_mismatch_count"] == 1
    assert report["predicted_label_mismatch_sample_ids"] == ["b"]
    assert report["overall_match"] is False


def test_score_tolerance_is_enforced(tmp_path):
    reference = _write(
        tmp_path / "reference.csv",
        "sample_id,predicted_label,score_a\n"
        "a,0,0.500000\n",
    )
    candidate = _write(
        tmp_path / "candidate.csv",
        "sample_id,predicted_label,score_a\n"
        "a,0,0.500500\n",
    )

    strict = compare_prediction_files(reference, candidate, atol=1e-4)
    relaxed = compare_prediction_files(reference, candidate, atol=1e-3)

    assert strict["score_stats"]["score_a"]["mismatch_count"] == 1
    assert strict["overall_match"] is False
    assert relaxed["score_stats"]["score_a"]["mismatch_count"] == 0
    assert relaxed["overall_match"] is True


def test_sample_set_difference_blocks_match(tmp_path):
    reference = _write(
        tmp_path / "reference.csv",
        "sample_id,predicted_label\n"
        "a,0\n"
        "b,1\n",
    )
    candidate = _write(
        tmp_path / "candidate.csv",
        "sample_id,predicted_label\n"
        "a,0\n"
        "c,1\n",
    )

    report = compare_prediction_files(reference, candidate)

    assert report["missing_in_candidate_count"] == 1
    assert report["extra_in_candidate_count"] == 1
    assert report["overall_match"] is False


def test_duplicate_sample_id_is_rejected(tmp_path):
    reference = _write(
        tmp_path / "reference.csv",
        "sample_id,predicted_label\n"
        "a,0\n"
        "a,1\n",
    )
    candidate = _write(
        tmp_path / "candidate.csv",
        "sample_id,predicted_label\n"
        "a,0\n",
    )

    with pytest.raises(PredictionFormatError, match="duplicate sample_id"):
        compare_prediction_files(reference, candidate)


def test_non_numeric_score_is_rejected(tmp_path):
    reference = _write(
        tmp_path / "reference.csv",
        "sample_id,predicted_label,score_a\n"
        "a,0,not-a-number\n",
    )
    candidate = _write(
        tmp_path / "candidate.csv",
        "sample_id,predicted_label,score_a\n"
        "a,0,0.5\n",
    )

    with pytest.raises(PredictionFormatError, match="non-numeric"):
        compare_prediction_files(reference, candidate)
