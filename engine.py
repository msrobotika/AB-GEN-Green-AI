"""
========================================================================
  AB-GEN 80% Accuracy - BLIND INFERENCE ENGINE
  Engine: Loads pre-trained model and performs geometric feature
          expansion + polynomial meta-learning inference.
  Dataset: CIFAR-10 (10 classes)
  Note: This module does NOT contain training logic.
========================================================================
"""

import time
import warnings
import numpy as np
import joblib
import torch
import torch.nn.functional as F
import sys
import os
import importlib.util

warnings.filterwarnings("ignore")

# â”€â”€ Register custom training classes so joblib can deserialize the bundle â”€â”€
# The .pkl was serialised with classes defined in the training script;
# we must expose them under the same module name ('training_module').
def _register_training_classes():
    """Find training script in parent dir and register its classes for pickle."""
    # Look two levels up: engine.py -> AB-GEN_GITHUB_DEMO -> AB-GEM + CNN
    demo_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(demo_dir)
    for fname in ["AB-GEN_80_Accuracy.py", "AB-GEM + CNN.py"]:
        fpath = os.path.join(root_dir, fname)
        if os.path.exists(fpath):
            spec = importlib.util.spec_from_file_location("training_module", fpath)
            mod  = importlib.util.module_from_spec(spec)
            sys.modules["training_module"] = mod
            spec.loader.exec_module(mod)
            return mod
    return None

_training_mod = _register_training_classes()
if _training_mod is None:
    print("[AB-GEN] WARNING: Training script not found. Bundle load may fail.")

# â”€â”€ CIFAR-10 Class names â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CIFAR10_CLASSES = [
    "airplane", "automobile", "bird", "cat", "deer",
    "dog", "frog", "horse", "ship", "truck"
]

COMPONENTES_PCA = 1200
VRAM_BATCH = 4096
TORCH_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# â”€â”€ Pure Math Functions (Mirrored from training, no fit logic) â”€â”€â”€â”€â”€â”€â”€
def _f32(x):
    return x.to(dtype=torch.float32) if torch.is_tensor(x) else np.asarray(x, dtype=np.float32)

def _normalize_l2(x):
    x = np.asarray(x, dtype=np.float32)
    return (x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-8)).astype(np.float32, copy=False)

def _multi_scale_fft(x_pca):
    def fft_block(x_np, blk):
        n_blocks = COMPONENTES_PCA // blk
        mags = []
        with torch.inference_mode():
            for s in range(0, x_np.shape[0], VRAM_BATCH):
                e = min(s + VRAM_BATCH, x_np.shape[0])
                batch = torch.as_tensor(x_np[s:e], dtype=torch.float32, device=TORCH_DEVICE)
                parts = [torch.abs(torch.fft.rfft(batch[:, b*blk:(b+1)*blk], dim=1)) for b in range(n_blocks)]
                mags.append(torch.cat(parts, dim=1).cpu().numpy())
        return np.vstack(mags).astype(np.float32)

    mi = fft_block(x_pca, 40)
    md = fft_block(x_pca, 200)
    mi /= (mi.max(axis=1, keepdims=True) + 1e-8)
    md /= (md.max(axis=1, keepdims=True) + 1e-8)

    ma_parts = []
    with torch.inference_mode():
        for s in range(0, x_pca.shape[0], VRAM_BATCH):
            e = min(s + VRAM_BATCH, x_pca.shape[0])
            seg = torch.as_tensor(x_pca[s:e], dtype=torch.float32, device=TORCH_DEVICE)
            ma_parts.append(torch.abs(torch.fft.rfft(seg, dim=1)).cpu().numpy())
    ma = np.vstack(ma_parts).astype(np.float32)
    ma /= (ma.max(axis=1, keepdims=True) + 1e-8)
    return np.hstack([x_pca, mi, md, ma]).astype(np.float32)[:, COMPONENTES_PCA:]

def _build_features(x_pca_w, cent_norm):
    xn = _normalize_l2(x_pca_w)
    sims = xn @ cent_norm.T
    qik = _f32((sims**2) / ((sims**2).sum(axis=1, keepdims=True) + 1e-8))
    hcr = _f32(np.hstack([sims, sims**2, sims**3]))
    dists = 1.0 - sims
    topo = _f32(np.hstack([
        dists.mean(axis=1, keepdims=True),
        dists.std(axis=1, keepdims=True),
        dists.min(axis=1, keepdims=True),
        dists.std(axis=1, keepdims=True) / (dists.mean(axis=1, keepdims=True) + 1e-8)
    ]))
    xd, cd = np.diff(xn, axis=1), np.diff(cent_norm, axis=1)
    gsb = _f32((xd @ cd.T) / (np.abs(xd @ cd.T).max(axis=1, keepdims=True) + 1e-8))
    return np.hstack([x_pca_w, _multi_scale_fft(x_pca_w), qik, hcr, topo, gsb]).astype(np.float32)

def _extract_logit_features(estimators, x):
    probs = []
    rng = np.random.default_rng(42)
    for est in estimators:
        p = est.predict_proba(x)
        p += est.predict_proba(x + rng.normal(0, 0.015, x.shape).astype(np.float32))
        p = p / 2.0
        probs.append(np.log(p + 1e-8).astype(np.float32))
    return np.hstack(probs).astype(np.float32)


# â”€â”€ AB-GEN Engine Class â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class ABGenEngine:
    """
    Blind inference engine for AB-GEN 80% Accuracy.
    Loads model bundles and the pre-computed PCA cache to perform
    geometric + polynomial inference on CIFAR-10 images.
    """
    def __init__(self, bundle_path: str):
        print(f"[AB-GEN] Loading model bundle from: {bundle_path}")
        bundle = joblib.load(bundle_path)

        self.n1        = bundle["n1"]
        self.pipeline_n2 = bundle["pipeline_n2"]
        self.cent_norm = bundle["cent_norm"]
        self.pesos_f   = bundle["pesos_f"]

        print(f"[AB-GEN] Device: {TORCH_DEVICE}")
        print("[AB-GEN] Engine ready âœ…")

    def _preprocess(self, x_pca: np.ndarray) -> np.ndarray:
        """Apply Fisher weighting + geometric feature expansion."""
        x_w = _f32(x_pca * self.pesos_f)
        return _build_features(x_w, self.cent_norm)

    def predict_batch(self, x_pca: np.ndarray):
        """
        Run full AB-GEN inference on a batch of PCA-projected vectors.
        Returns (predicted_class_indices, class_probabilities, latency_ms).
        """
        t0 = time.perf_counter()

        x_feat  = self._preprocess(x_pca)
        meta_raw = _extract_logit_features(self.n1.estimators_, x_feat)

        poly   = self.pipeline_n2["poly"]
        scaler = self.pipeline_n2["scaler"]
        ridge  = self.pipeline_n2["ridge"]

        meta_poly   = poly.transform(meta_raw)
        meta_scaled = scaler.transform(meta_poly)

        preds  = ridge.predict(meta_scaled)
        # Ridge doesn't output probabilities natively; use decision_function softmax
        df      = ridge.decision_function(meta_scaled)
        df_t    = torch.tensor(df, dtype=torch.float32)
        probs   = F.softmax(df_t, dim=1).numpy()

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return preds.astype(int), probs, latency_ms

    def predict_single(self, x_pca_row: np.ndarray):
        """Predict a single sample (1-D PCA vector)."""
        preds, probs, latency = self.predict_batch(x_pca_row[np.newaxis, :])
        return int(preds[0]), probs[0], latency

