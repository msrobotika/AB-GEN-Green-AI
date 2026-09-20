from app import CIFAR10_CLASSES, reset_session_stats, session_stats


def test_reset_session_stats_preserves_fixed_class_arrays():
    session_stats["total_images"] = 24
    session_stats["total_correct"] = 19
    session_stats["total_batches"] = 2
    session_stats["total_latency_ms"] = 123.4
    session_stats["class_correct"] = [1] * len(CIFAR10_CLASSES)
    session_stats["class_total"] = [2] * len(CIFAR10_CLASSES)
    session_stats["history_acc"] = [75.0, 83.3]
    session_stats["energy_saved_j"] = 0.123

    reset_session_stats()

    assert session_stats["total_images"] == 0
    assert session_stats["total_correct"] == 0
    assert session_stats["total_batches"] == 0
    assert session_stats["total_latency_ms"] == 0.0
    assert session_stats["class_correct"] == [0] * len(CIFAR10_CLASSES)
    assert session_stats["class_total"] == [0] * len(CIFAR10_CLASSES)
    assert session_stats["history_acc"] == []
    assert session_stats["energy_saved_j"] == 0.0
