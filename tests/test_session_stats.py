from concurrent.futures import ThreadPoolExecutor

import numpy as np

from app import (
    CIFAR10_CLASSES,
    record_session_batch,
    reset_session_stats,
    session_stats,
)


def test_concurrent_session_updates_are_consistent():
    reset_session_stats()

    y_true = np.arange(len(CIFAR10_CLASSES), dtype=np.int64)
    preds = y_true.copy()

    def record_one_batch(_):
        return record_session_batch(
            y_true=y_true,
            preds=preds,
            latency_ms=5.0,
            batch_acc=100.0,
        )

    batch_count = 32
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(record_one_batch, range(batch_count)))

    expected_images = batch_count * len(CIFAR10_CLASSES)
    assert session_stats["total_images"] == expected_images
    assert session_stats["total_correct"] == expected_images
    assert session_stats["total_batches"] == batch_count
    assert session_stats["total_latency_ms"] == batch_count * 5.0
    assert session_stats["class_total"] == [batch_count] * len(CIFAR10_CLASSES)
    assert session_stats["class_correct"] == [batch_count] * len(CIFAR10_CLASSES)
    assert len(session_stats["history_acc"]) == batch_count
    assert "energy_saved_j" not in session_stats


def test_session_snapshot_is_self_consistent():
    reset_session_stats()

    y_true = np.arange(len(CIFAR10_CLASSES), dtype=np.int64)
    preds = y_true.copy()

    snapshot = record_session_batch(
        y_true=y_true,
        preds=preds,
        latency_ms=7.5,
        batch_acc=100.0,
    )

    assert snapshot["session_acc"] == 100.0
    assert snapshot["session_images"] == len(CIFAR10_CLASSES)
    assert snapshot["session_batches"] == 1
    assert snapshot["avg_latency_ms"] == 7.5
    assert snapshot["class_acc"] == [100.0] * len(CIFAR10_CLASSES)
    assert snapshot["history_acc"] == [100.0]
    assert "reference_energy_saved_mj" not in snapshot
    assert "session_energy_saved_mj" not in snapshot
