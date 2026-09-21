"""AB-GEN Research Demo - Flask server.

This application is a diagnostic interface over recovered PCA-cache artifacts.
It is not an end-to-end RAW->prediction reproduction and it deliberately does
not expose unvalidated historical energy constants as live metrics.
"""

import base64
import io
import os
import pickle
import sys
import threading

import numpy as np
from PIL import Image
from flask import Flask, jsonify, render_template

from engine import ABGenEngine, CIFAR10_CLASSES
from runtime_integrity import runtime_preflight_errors

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ARTIFACT_DIR = os.path.join(BASE_DIR, "artifacts")

# Launchers/containers may override these paths explicitly. Direct launch uses
# the same repository-local artifacts/ contract documented everywhere else.
BUNDLE_PATH = os.environ.get(
    "ABGEN_BUNDLE_PATH", os.path.join(DEFAULT_ARTIFACT_DIR, "abgen_bundle.pkl")
)
SAMPLE_DATA_PATH = os.environ.get(
    "ABGEN_SAMPLE_DATA_PATH", os.path.join(DEFAULT_ARTIFACT_DIR, "sample_data.pkl")
)

REPORTED_V24_VERSION = "V24 Slow Burn"
REPORTED_V24_ACCURACY = 80.14
RECOVERED_ELITE_ACCURACY = 80.17
RECOVERED_M5_ACCURACY = 79.55
RECOVERED_M4_ACCURACY = 78.05

EVIDENCE_STATUS = "reported_historical_not_reproduced"
INPUT_MODE = "cached_pca_vectors"
SCORE_METRIC_STATUS = "normalized_decision_scores_uncalibrated"
ENERGY_METRIC_STATUS = "unavailable_pending_controlled_measurement"
INFERENCE_PATH_STATUS = "recovered_historical_path_not_clean_baseline"
BATCH_INVARIANCE_STATUS = "known_failure_in_targeted_audit"

app = Flask(__name__)
engine = None
sample_data = None

# Session statistics are diagnostic only. Batch selection is deterministic:
# after reset, calls traverse cached samples in stable stored order.
session_stats = {
    "total_images": 0,
    "total_correct": 0,
    "total_batches": 0,
    "total_latency_ms": 0.0,
    "class_correct": [0] * len(CIFAR10_CLASSES),
    "class_total": [0] * len(CIFAR10_CLASSES),
    "history_acc": [],
    "batch_cursor": 0,
}
session_stats_lock = threading.RLock()


def img_to_b64(arr_rgb_uint8: np.ndarray, scale: int = 4) -> str:
    """Convert a 32x32 RGB uint8 array to a base64-encoded PNG."""
    img = Image.fromarray(arr_rgb_uint8.astype(np.uint8), "RGB")
    img = img.resize((32 * scale, 32 * scale), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def load_resources():
    """Load trusted runtime artifacts after the caller has completed preflight."""
    global engine, sample_data
    print(f"[SERVER] Loading AB-GEN engine bundle: {BUNDLE_PATH}")
    engine = ABGenEngine(BUNDLE_PATH)
    print(f"[SERVER] Loading cached sample data: {SAMPLE_DATA_PATH}")
    with open(SAMPLE_DATA_PATH, "rb") as f:
        sample_data = pickle.load(f)
    print(f"[SERVER] {len(sample_data['y'])} cached test samples ready.")


def reset_session_stats():
    """Atomically restore counters, fixed class arrays and deterministic cursor."""
    with session_stats_lock:
        session_stats["total_images"] = 0
        session_stats["total_correct"] = 0
        session_stats["total_batches"] = 0
        session_stats["total_latency_ms"] = 0.0
        session_stats["class_correct"] = [0] * len(CIFAR10_CLASSES)
        session_stats["class_total"] = [0] * len(CIFAR10_CLASSES)
        session_stats["history_acc"].clear()
        session_stats["batch_cursor"] = 0


def next_batch_indices(total: int, batch_size: int) -> np.ndarray:
    """Return the next deterministic cached-sample indices and advance the cursor.

    The sequence is fully determined by stored sample order and session reset.
    This removes UI-level random sampling from reproducibility diagnostics.
    """
    if total <= 0:
        raise ValueError("sample cache is empty")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    n = min(int(batch_size), int(total))
    with session_stats_lock:
        start = int(session_stats["batch_cursor"]) % total
        idx = (np.arange(n, dtype=np.int64) + start) % total
        session_stats["batch_cursor"] = int((start + n) % total)
    return idx


def record_session_batch(y_true, preds, latency_ms: float, batch_acc: float):
    """Atomically record one diagnostic batch and return a consistent snapshot."""
    n = int(len(y_true))
    correct = int((preds == y_true).sum())

    with session_stats_lock:
        session_stats["total_images"] += n
        session_stats["total_correct"] += correct
        session_stats["total_batches"] += 1
        session_stats["total_latency_ms"] += float(latency_ms)
        session_stats["history_acc"].append(round(float(batch_acc), 1))

        for i in range(n):
            c = int(y_true[i])
            session_stats["class_total"][c] += 1
            if preds[i] == y_true[i]:
                session_stats["class_correct"][c] += 1

        session_acc = (
            session_stats["total_correct"] /
            max(session_stats["total_images"], 1)
        ) * 100.0

        class_acc = []
        for c in range(len(CIFAR10_CLASSES)):
            total = session_stats["class_total"][c]
            ok = session_stats["class_correct"][c]
            class_acc.append(round(ok / total * 100, 1) if total > 0 else None)

        batches = session_stats["total_batches"]
        return {
            "session_acc": session_acc,
            "session_images": session_stats["total_images"],
            "session_batches": batches,
            "avg_latency_ms": round(
                session_stats["total_latency_ms"] / max(batches, 1), 1
            ),
            "class_acc": class_acc,
            "history_acc": list(session_stats["history_acc"][-20:]),
        }


def _evidence_payload() -> dict:
    """Return explicit non-overlapping evidence states for public/API use."""
    return {
        "historical_reported": {
            "version": REPORTED_V24_VERSION,
            "accuracy_pct": REPORTED_V24_ACCURACY,
            "status": EVIDENCE_STATUS,
        },
        "recovered": {
            "elite_slow_burn_cache_accuracy_pct": RECOVERED_ELITE_ACCURACY,
            "m5_master_reconstructed_accuracy_pct": RECOVERED_M5_ACCURACY,
            "m4_cache_accuracy_pct": RECOVERED_M4_ACCURACY,
            "status": "recovered_or_reconstructed_not_clean_reproduction",
        },
    }


def _resources_ready() -> bool:
    return engine is not None and sample_data is not None


@app.route("/")
def index():
    total_samples = len(sample_data["y"]) if sample_data is not None else 0
    return render_template(
        "index.html",
        total_samples=total_samples,
        classes=CIFAR10_CLASSES,
    )


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Run the recovered inference path over the next deterministic cached batch."""
    if not _resources_ready():
        return jsonify({"error": "runtime resources are not loaded", "ready": False}), 503

    total_samples = len(sample_data["y"])
    if total_samples <= 0:
        return jsonify({"error": "sample cache is empty", "ready": False}), 503

    n = min(12, total_samples)
    idx = next_batch_indices(total_samples, n)

    x_batch = sample_data["x_pca"][idx]
    y_true = sample_data["y"][idx]

    preds, scores, latency_ms = engine.predict_batch(x_batch)

    correct = int((preds == y_true).sum())
    batch_acc = correct / n * 100.0
    session_snapshot = record_session_batch(
        y_true=y_true,
        preds=preds,
        latency_ms=latency_ms,
        batch_acc=batch_acc,
    )

    throughput = n / max(latency_ms / 1000.0, 1e-12)

    results = []
    for i, ix in enumerate(idx):
        img_b64 = img_to_b64(sample_data["images_rgb"][ix])
        top3 = []
        for j in np.argsort(scores[i])[::-1][:3]:
            score_pct = round(float(scores[i][j]) * 100, 1)
            top3.append({
                "class": CIFAR10_CLASSES[j],
                "score_pct": score_pct,
            })

        max_score_pct = round(float(scores[i].max()) * 100, 1)
        results.append({
            "index": int(ix),
            "true_label": CIFAR10_CLASSES[int(y_true[i])],
            "pred_label": CIFAR10_CLASSES[int(preds[i])],
            "score_pct": max_score_pct,
            "correct": bool(preds[i] == y_true[i]),
            "image_b64": img_b64,
            "top3": top3,
        })

    return jsonify({
        "batch_accuracy": round(batch_acc, 1),
        "correct": correct,
        "total": n,
        "latency_ms": round(latency_ms, 1),
        "throughput": round(throughput, 1),
        "input_mode": INPUT_MODE,
        "score_metric_status": SCORE_METRIC_STATUS,
        "energy_metric_status": ENERGY_METRIC_STATUS,
        "inference_path_status": INFERENCE_PATH_STATUS,
        "batch_invariance_status": BATCH_INVARIANCE_STATUS,
        "batch_indices": [int(x) for x in idx],
        "session_acc": round(session_snapshot["session_acc"], 1),
        "session_images": session_snapshot["session_images"],
        "session_batches": session_snapshot["session_batches"],
        "avg_latency_ms": session_snapshot["avg_latency_ms"],
        "class_acc": session_snapshot["class_acc"],
        "history_acc": session_snapshot["history_acc"],
        "results": results,
        "device": "CUDA" if __import__("torch").cuda.is_available() else "CPU",
    })


@app.route("/api/status")
def status():
    """Expose runtime state and evidence semantics without claim aliases."""
    samples = len(sample_data["y"]) if sample_data is not None else 0
    return jsonify({
        "model": "AB-GEN Research Demo",
        "dataset": "CIFAR-10",
        "evidence": _evidence_payload(),
        "input_mode": INPUT_MODE,
        "score_metric_status": SCORE_METRIC_STATUS,
        "energy_metric_status": ENERGY_METRIC_STATUS,
        "inference_path_status": INFERENCE_PATH_STATUS,
        "batch_invariance_status": BATCH_INVARIANCE_STATUS,
        "samples": samples,
        "device": "CUDA" if __import__("torch").cuda.is_available() else "CPU",
        "ready": _resources_ready(),
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    reset_session_stats()
    return jsonify({"ok": True})


def _direct_launch_preflight() -> int:
    errors = runtime_preflight_errors()
    if not errors:
        return 0
    print("[AB-GEN] Direct demo startup refused: runtime preflight failed.", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)
    return 3


if __name__ == "__main__":
    exit_code = _direct_launch_preflight()
    if exit_code:
        raise SystemExit(exit_code)
    load_resources()
    app.run(host="127.0.0.1", port=5000, debug=False)
