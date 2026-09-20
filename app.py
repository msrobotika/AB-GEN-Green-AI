"""
AB-GEN Research Demo - Flask server.

The demo exposes live session/inference metrics separately from reported
experimental results and historical energy reference values.
"""

import os
import io
import random
import pickle
import base64
import threading
import numpy as np
from PIL import Image
from flask import Flask, render_template, jsonify
from engine import ABGenEngine, CIFAR10_CLASSES

# Runtime artifacts can be supplied explicitly (for example by a read-only
# Docker volume) while preserving the historical local-file defaults.
BUNDLE_PATH = os.environ.get("ABGEN_BUNDLE_PATH", "abgen_bundle.pkl")
SAMPLE_DATA_PATH = os.environ.get("ABGEN_SAMPLE_DATA_PATH", "sample_data.pkl")
REFERENCE_ACCURACY_THRESHOLD = 80.0
REPORTED_V24_ACCURACY = 80.14
REPORTED_V24_VERSION = "V24 Slow Burn"

# Historical/project Green AI reference values.
# These are NOT live power measurements and remain pending controlled re-benchmarking.
J_PER_INFERENCE = 0.00031
CNN_J_INFERENCE = 0.0042
CO2_PER_KWH = 0.233
INFERENCE_PRICE = 0.00012

EVIDENCE_STATUS = "reported_pending_reproduction"
ENERGY_METRIC_STATUS = "historical_reference_not_live_measurement"
SCORE_METRIC_STATUS = "normalized_decision_scores_uncalibrated"
INPUT_MODE = "cached_pca_vectors"

app = Flask(__name__)
engine = None
sample_data = None

# Session stats (in-memory)
session_stats = {
    "total_images": 0,
    "total_correct": 0,
    "total_batches": 0,
    "total_latency_ms": 0.0,
    "class_correct": [0] * 10,
    "class_total": [0] * 10,
    "history_acc": [],
    "energy_saved_j": 0.0,
}
session_stats_lock = threading.RLock()


def img_to_b64(arr_rgb_uint8: np.ndarray, scale: int = 4) -> str:
    """Convert (32, 32, 3) uint8 ndarray to a base64-encoded PNG."""
    img = Image.fromarray(arr_rgb_uint8.astype(np.uint8), "RGB")
    img = img.resize((32 * scale, 32 * scale), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def load_resources():
    global engine, sample_data
    print(f"[SERVER] Loading AB-GEN engine bundle: {BUNDLE_PATH}")
    engine = ABGenEngine(BUNDLE_PATH)
    print(f"[SERVER] Loading cached sample data: {SAMPLE_DATA_PATH}")
    with open(SAMPLE_DATA_PATH, "rb") as f:
        sample_data = pickle.load(f)
    print(f"[SERVER] {len(sample_data['y'])} cached test samples ready.")


def reset_session_stats():
    """Atomically restore session counters and fixed per-class array sizes."""
    with session_stats_lock:
        session_stats["total_images"] = 0
        session_stats["total_correct"] = 0
        session_stats["total_batches"] = 0
        session_stats["total_latency_ms"] = 0.0
        session_stats["class_correct"] = [0] * len(CIFAR10_CLASSES)
        session_stats["class_total"] = [0] * len(CIFAR10_CLASSES)
        session_stats["history_acc"].clear()
        session_stats["energy_saved_j"] = 0.0


def record_session_batch(y_true, preds, latency_ms: float, batch_acc: float, saved_j: float):
    """Atomically record one batch and return a consistent session snapshot."""
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

        # Retained for UI compatibility; this is reference-derived, not measured energy.
        session_stats["energy_saved_j"] += float(saved_j)

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
            "reference_energy_saved_mj": round(session_stats["energy_saved_j"] * 1000, 3),
            # Legacy compatibility alias. See energy_metric_status in API payload.
            "session_energy_saved_mj": round(session_stats["energy_saved_j"] * 1000, 3),
            "avg_latency_ms": round(session_stats["total_latency_ms"] / max(batches, 1), 1),
            "class_acc": class_acc,
            "history_acc": list(session_stats["history_acc"][-20:]),
        }


@app.route("/")
def index():
    return render_template(
        "index.html",
        total_samples=len(sample_data["y"]),
        accuracy_target=REFERENCE_ACCURACY_THRESHOLD,
        classes=CIFAR10_CLASSES,
    )


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Run inference over a random batch of cached CIFAR-10 PCA samples."""
    n = min(12, len(sample_data["y"]))
    idx = random.sample(range(len(sample_data["y"])), n)

    x_batch = sample_data["x_pca"][idx]
    y_true = sample_data["y"][idx]

    preds, scores, latency_ms = engine.predict_batch(x_batch)

    correct = int((preds == y_true).sum())
    batch_acc = correct / n * 100.0

    # Historical/reference constants only; not live power measurement.
    reference_energy_j = J_PER_INFERENCE * n
    reference_saved_j = (CNN_J_INFERENCE - J_PER_INFERENCE) * n
    reference_co2_saved_ug = (reference_saved_j / 3_600_000) * CO2_PER_KWH * 1e9

    session_snapshot = record_session_batch(
        y_true=y_true,
        preds=preds,
        latency_ms=latency_ms,
        batch_acc=batch_acc,
        saved_j=reference_saved_j,
    )

    throughput = n / (latency_ms / 1000.0)

    results = []
    for i, ix in enumerate(idx):
        img_b64 = img_to_b64(sample_data["images_rgb"][ix])
        top3 = []
        for j in np.argsort(scores[i])[::-1][:3]:
            score_pct = round(float(scores[i][j]) * 100, 1)
            top3.append({
                "class": CIFAR10_CLASSES[j],
                "score_pct": score_pct,
                # Legacy compatibility alias; not a calibrated probability.
                "prob": score_pct,
            })

        max_score_pct = round(float(scores[i].max()) * 100, 1)
        results.append({
            "index": int(ix),
            "true_label": CIFAR10_CLASSES[int(y_true[i])],
            "pred_label": CIFAR10_CLASSES[int(preds[i])],
            "score_pct": max_score_pct,
            # Legacy compatibility alias; see score_metric_status.
            "confidence": max_score_pct,
            "correct": bool(preds[i] == y_true[i]),
            "image_b64": img_b64,
            "top3": top3,
        })

    reference_saving_pct = round((reference_saved_j / (CNN_J_INFERENCE * n)) * 100, 1)

    return jsonify({
        "batch_accuracy": round(batch_acc, 1),
        "correct": correct,
        "total": n,
        "latency_ms": round(latency_ms, 1),
        "throughput": round(throughput, 1),
        "input_mode": INPUT_MODE,
        "score_metric_status": SCORE_METRIC_STATUS,
        "energy_metric_status": ENERGY_METRIC_STATUS,
        "reference_energy_uj": round(reference_energy_j * 1e6, 1),
        "reference_energy_saved_uj": round(reference_saved_j * 1e6, 1),
        "reference_co2_saved_ug": round(reference_co2_saved_ug, 4),
        "reference_saving_pct": reference_saving_pct,
        # Legacy compatibility fields. All are reference-derived, not measured live.
        "energy_uj": round(reference_energy_j * 1e6, 1),
        "energy_saved_uj": round(reference_saved_j * 1e6, 1),
        "co2_saved_ug": round(reference_co2_saved_ug, 4),
        "saving_pct": reference_saving_pct,
        "session_acc": round(session_snapshot["session_acc"], 1),
        "session_images": session_snapshot["session_images"],
        "session_batches": session_snapshot["session_batches"],
        "reference_energy_saved_mj": session_snapshot["reference_energy_saved_mj"],
        "session_energy_saved_mj": session_snapshot["session_energy_saved_mj"],
        "avg_latency_ms": session_snapshot["avg_latency_ms"],
        "class_acc": session_snapshot["class_acc"],
        "history_acc": session_snapshot["history_acc"],
        "results": results,
        "device": "CUDA" if __import__("torch").cuda.is_available() else "CPU",
    })


@app.route("/api/status")
def status():
    """Expose runtime status and explicit evidence semantics."""
    return jsonify({
        "model": "AB-GEN Research Demo",
        "dataset": "CIFAR-10",
        "reported_version": REPORTED_V24_VERSION,
        "reported_accuracy": REPORTED_V24_ACCURACY,
        # Legacy compatibility field; interpretation is explicit in accuracy_status.
        "accuracy": REPORTED_V24_ACCURACY,
        "accuracy_status": EVIDENCE_STATUS,
        "input_mode": INPUT_MODE,
        "score_metric_status": SCORE_METRIC_STATUS,
        "energy_metric_status": ENERGY_METRIC_STATUS,
        "samples": len(sample_data["y"]),
        "device": "CUDA" if __import__("torch").cuda.is_available() else "CPU",
        "ready": True,
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    reset_session_stats()
    return jsonify({"ok": True})


if __name__ == "__main__":
    load_resources()
    app.run(host="0.0.0.0", port=5000, debug=False)
