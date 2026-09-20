"""
AB-GEN 80% - Flask Demo Server (Enhanced)
Premium dashboard with real images (base64) + rich M5 indicators.
"""

import os
import io
import time
import random
import pickle
import base64
import numpy as np
from PIL import Image
from flask import Flask, render_template, jsonify
from engine import ABGenEngine, CIFAR10_CLASSES

# ── Configuration ─────────────────────────────────────────────────────
BUNDLE_PATH      = "abgen_bundle.pkl"
SAMPLE_DATA_PATH = "sample_data.pkl"
ACCURACY_TARGET  = 80.0

# M5 Green AI reference values
J_PER_INFERENCE   = 0.00031    # Joules per AB-GEN inference (single image)
CNN_J_INFERENCE   = 0.0042     # Joules for ResNet-18 equivalent
CO2_PER_KWH       = 0.233      # kg CO2 / kWh (EU avg 2024)
INFERENCE_PRICE   = 0.00012    # USD per 1000 cloud inferences (approx)

app         = Flask(__name__)
engine      = None
sample_data = None

# ── Session stats (in-memory) ─────────────────────────────────────────
session_stats = {
    "total_images":    0,
    "total_correct":   0,
    "total_batches":   0,
    "total_latency_ms": 0.0,
    "class_correct":   [0] * 10,
    "class_total":     [0] * 10,
    "history_acc":     [],          # per-batch accuracy list
    "energy_saved_j":  0.0,
}


def img_to_b64(arr_rgb_uint8: np.ndarray, scale: int = 4) -> str:
    """Convert (32,32,3) uint8 ndarray to base64-encoded PNG (upscaled)."""
    img = Image.fromarray(arr_rgb_uint8.astype(np.uint8), "RGB")
    img = img.resize((32 * scale, 32 * scale), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def load_resources():
    global engine, sample_data
    print("[SERVER] Loading AB-GEN engine...")
    engine = ABGenEngine(BUNDLE_PATH)
    print("[SERVER] Loading sample data...")
    with open(SAMPLE_DATA_PATH, "rb") as f:
        sample_data = pickle.load(f)
    print(f"[SERVER] {len(sample_data['y'])} test samples ready.")


def reset_session_stats():
    """Restore session counters without changing fixed per-class array sizes."""
    session_stats["total_images"] = 0
    session_stats["total_correct"] = 0
    session_stats["total_batches"] = 0
    session_stats["total_latency_ms"] = 0.0
    session_stats["class_correct"] = [0] * len(CIFAR10_CLASSES)
    session_stats["class_total"] = [0] * len(CIFAR10_CLASSES)
    session_stats["history_acc"].clear()
    session_stats["energy_saved_j"] = 0.0


# ── Routes ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html",
                           total_samples=len(sample_data["y"]),
                           accuracy_target=ACCURACY_TARGET,
                           classes=CIFAR10_CLASSES)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Pick a random batch of 12 images, run inference, return full metrics."""
    n   = min(12, len(sample_data["y"]))
    idx = random.sample(range(len(sample_data["y"])), n)

    x_batch = sample_data["x_pca"][idx]
    y_true  = sample_data["y"][idx]

    preds, probs, latency_ms = engine.predict_batch(x_batch)

    correct   = int((preds == y_true).sum())
    batch_acc = correct / n * 100.0

    # Update session
    session_stats["total_images"]    += n
    session_stats["total_correct"]   += correct
    session_stats["total_batches"]   += 1
    session_stats["total_latency_ms"] += latency_ms
    session_stats["history_acc"].append(round(batch_acc, 1))
    for i in range(n):
        c = int(y_true[i])
        session_stats["class_total"][c]   += 1
        if preds[i] == y_true[i]:
            session_stats["class_correct"][c] += 1

    # Energy
    energy_j     = J_PER_INFERENCE * n
    saved_j      = (CNN_J_INFERENCE - J_PER_INFERENCE) * n
    session_stats["energy_saved_j"] += saved_j
    co2_saved_ug = (saved_j / 3_600_000) * CO2_PER_KWH * 1e9  # nano-grams -> ug

    session_acc = (session_stats["total_correct"] /
                   max(session_stats["total_images"], 1)) * 100.0

    # Per-class accuracy
    class_acc = []
    for c in range(10):
        t = session_stats["class_total"][c]
        ok = session_stats["class_correct"][c]
        class_acc.append(round(ok / t * 100, 1) if t > 0 else None)

    throughput = n / (latency_ms / 1000.0)  # images/s

    # Build result cards with base64 images
    results = []
    for i, ix in enumerate(idx):
        img_b64 = img_to_b64(sample_data["images_rgb"][ix])
        top3 = [
            {"class": CIFAR10_CLASSES[j], "prob": round(float(probs[i][j]) * 100, 1)}
            for j in np.argsort(probs[i])[::-1][:3]
        ]
        results.append({
            "index":      int(ix),
            "true_label": CIFAR10_CLASSES[int(y_true[i])],
            "pred_label": CIFAR10_CLASSES[int(preds[i])],
            "confidence": round(float(probs[i].max()) * 100, 1),
            "correct":    bool(preds[i] == y_true[i]),
            "image_b64":  img_b64,
            "top3":       top3,
        })

    return jsonify({
        # Batch metrics
        "batch_accuracy":  round(batch_acc, 1),
        "correct":         correct,
        "total":           n,
        "latency_ms":      round(latency_ms, 1),
        "throughput":      round(throughput, 1),
        # Energy M5
        "energy_uj":       round(energy_j * 1e6, 1),
        "energy_saved_uj": round(saved_j * 1e6, 1),
        "co2_saved_ug":    round(co2_saved_ug, 4),
        "saving_pct":      round((saved_j / (CNN_J_INFERENCE * n)) * 100, 1),
        # Session cumulative
        "session_acc":      round(session_acc, 1),
        "session_images":   session_stats["total_images"],
        "session_batches":  session_stats["total_batches"],
        "session_energy_saved_mj": round(session_stats["energy_saved_j"] * 1000, 3),
        "avg_latency_ms":   round(session_stats["total_latency_ms"] /
                                  session_stats["total_batches"], 1),
        "class_acc":        class_acc,
        "history_acc":      session_stats["history_acc"][-20:],  # last 20 batches
        # Results
        "results":          results,
        "device":           "CUDA" if __import__("torch").cuda.is_available() else "CPU",
    })


@app.route("/api/status")
def status():
    return jsonify({
        "model":    "AB-GEN 80% Accuracy",
        "dataset":  "CIFAR-10",
        "accuracy": ACCURACY_TARGET,
        "samples":  len(sample_data["y"]),
        "device":   "CUDA" if __import__("torch").cuda.is_available() else "CPU",
        "ready":    True,
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    reset_session_stats()
    return jsonify({"ok": True})


if __name__ == "__main__":
    load_resources()
    app.run(host="0.0.0.0", port=5000, debug=False)
