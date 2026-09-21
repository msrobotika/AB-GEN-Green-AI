from app import CIFAR10_CLASSES, next_batch_indices, reset_session_stats, session_stats


def test_reset_session_stats_preserves_fixed_class_arrays_and_cursor():
    session_stats["total_images"] = 24
    session_stats["total_correct"] = 19
    session_stats["total_batches"] = 2
    session_stats["total_latency_ms"] = 123.4
    session_stats["class_correct"] = [1] * len(CIFAR10_CLASSES)
    session_stats["class_total"] = [2] * len(CIFAR10_CLASSES)
    session_stats["history_acc"] = [75.0, 83.3]
    session_stats["batch_cursor"] = 24

    reset_session_stats()

    assert session_stats["total_images"] == 0
    assert session_stats["total_correct"] == 0
    assert session_stats["total_batches"] == 0
    assert session_stats["total_latency_ms"] == 0.0
    assert session_stats["class_correct"] == [0] * len(CIFAR10_CLASSES)
    assert session_stats["class_total"] == [0] * len(CIFAR10_CLASSES)
    assert session_stats["history_acc"] == []
    assert session_stats["batch_cursor"] == 0


def test_cached_batch_selection_is_deterministic_and_wraps():
    reset_session_stats()

    first = next_batch_indices(total=10, batch_size=4).tolist()
    second = next_batch_indices(total=10, batch_size=4).tolist()
    third = next_batch_indices(total=10, batch_size=4).tolist()

    assert first == [0, 1, 2, 3]
    assert second == [4, 5, 6, 7]
    assert third == [8, 9, 0, 1]

    reset_session_stats()
    assert next_batch_indices(total=10, batch_size=4).tolist() == first
