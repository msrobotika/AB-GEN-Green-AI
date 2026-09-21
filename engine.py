"""AB-GEN Research Demo - recovered inference engine.

Loads trusted pre-trained artifacts and performs geometric, spectral and
polynomial inference over PCA-projected CIFAR-10 samples. This module does
not contain training logic and must not be described as a clean RAW-image
reproduction.

Important: the recovered historical meta-feature path intentionally preserves
a noise-averaging step because changing it would alter the recovered behavior.
A targeted audit has shown that this mechanism can make predictions depend on
batch shape/position. That behavior is documented, not endorsed as a clean
inference design.
"""

import importlib.util
import os
import sys
import time

import joblib
import numpy as np
import torch
import torch.nn.functional as F


def _load_training_module(module_path: str):
    """Load a trusted compatibility/training module as ``training_module``."""
    spec = importlib.util.spec_from_file_location("training_module", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for: {module_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["training_module"] = mod
    spec.loader.exec_module(mod)
    return mod


def _register_training_classes():
    """Register classes required by legacy joblib bundles.

    A validated deployment should set ``ABGEN_TRAINING_MODULE_PATH`` to an
    explicitly supplied, trusted compatibility module. The parent-folder
    search is retained only for backwards compatibility with the historical
    local project layout and is never used by the container contract.
    """
    explicit_path = os.environ.get("ABGEN_TRAINING_MODULE_PATH")
    if explicit_path:
        explicit_path = os.path.abspath(explicit_path)
        if os.path.isfile(explicit_path):
            return _load_training_module(explicit_path)
        print(
            "[AB-GEN] WARNING: ABGEN_TRAINING_MODULE_PATH does not exist: "
            f"{explicit_path}"
        )
        return None

    demo_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(demo_dir)
    for fname in ["AB-GEN_80_Accuracy.py", "AB-GEM + CNN.py"]:
        fpath = os.path.join(root_dir, fname)
        if os.path.isfile(fpath):
            print(
                "[AB-GEN] WARNING: using historical parent-layout compatibility "
                f"module: {fpath}"
            )
            return _load_training_module(fpath)
    return None


_training_mod = _register_training_classes()
if _training_mod is None:
    print(
        "[AB-GEN] WARNING: serialization compatibility module not found. "
        "A legacy bundle that references training_module classes may fail to load."
    )


CIFAR10_CLASSES = [
    "airplane", "automobile", "bird", "cat", "deer",
    "dog", "frog", "horse", "ship", "truck",
]

COMPONENTES_PCA = 1200
VRAM_BATCH = 4096
TORCH_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
HISTORICAL_NOISE_SEED = 42
HISTORICAL_NOISE_STD = 0.015


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
                parts = [
                    torch.abs(torch.fft.rfft(batch[:, b * blk:(b + 1) * blk], dim=1))
                    for b in range(n_blocks)
                ]
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
    qik = _f32((sims ** 2) / ((sims ** 2).sum(axis=1, keepdims=True) + 1e-8))
    hcr = _f32(np.hstack([sims, sims ** 2, sims ** 3]))
    dists = 1.0 - sims
    topo = _f32(np.hstack([
        dists.mean(axis=1, keepdims=True),
        dists.std(axis=1, keepdims=True),
        dists.min(axis=1, keepdims=True),
        dists.std(axis=1, keepdims=True) / (dists.mean(axis=1, keepdims=True) + 1e-8),
    ]))
    xd, cd = np.diff(xn, axis=1), np.diff(cent_norm, axis=1)
    gsb = _f32((xd @ cd.T) / (np.abs(xd @ cd.T).max(axis=1, keepdims=True) + 1e-8))
    return np.hstack([x_pca_w, _multi_scale_fft(x_pca_w), qik, hcr, topo, gsb]).astype(np.float32)


def _extract_logit_features_historical(estimators, x):
    """Reproduce the recovered historical N1 noise-averaging behavior.

    The RNG is reset on every call. Noise is therefore deterministic for a
    given array shape/order, but it is assigned by batch position rather than
    by stable sample identity. The current audit has demonstrated that this can
    change predictions when the same sample is evaluated in different batch
    contexts.
    """
    probs = []
    rng = np.random.default_rng(HISTORICAL_NOISE_SEED)
    for est in estimators:
        p = est.predict_proba(x)
        noise = rng.normal(0, HISTORICAL_NOISE_STD, x.shape).astype(np.float32)
        p += est.predict_proba(x + noise)
        p = p / 2.0
        probs.append(np.log(p + 1e-8).astype(np.float32))
    return np.hstack(probs).astype(np.float32)


class ABGenEngine:
    """Inference engine for trusted, recovered AB-GEN runtime artifacts."""

    def __init__(self, bundle_path: str):
        print(f"[AB-GEN] Loading trusted model bundle from: {bundle_path}")
        bundle = joblib.load(bundle_path)

        self.n1 = bundle["n1"]
        self.pipeline_n2 = bundle["pipeline_n2"]
        self.cent_norm = bundle["cent_norm"]
        self.pesos_f = bundle["pesos_f"]

        print(f"[AB-GEN] Device: {TORCH_DEVICE}")
        print("[AB-GEN] Recovered historical inference path ready")

    def _preprocess(self, x_pca: np.ndarray) -> np.ndarray:
        """Apply recovered Fisher weighting plus geometric/spectral expansion."""
        x_w = _f32(x_pca * self.pesos_f)
        return _build_features(x_w, self.cent_norm)

    def predict_batch(self, x_pca: np.ndarray):
        """Return predictions, normalized decision scores and elapsed latency.

        This method preserves the recovered historical batch-dependent
        noise-averaging path. It is not the future clean-baseline inference API.
        """
        t0 = time.perf_counter()

        x_feat = self._preprocess(x_pca)
        meta_raw = _extract_logit_features_historical(self.n1.estimators_, x_feat)

        poly = self.pipeline_n2["poly"]
        scaler = self.pipeline_n2["scaler"]
        ridge = self.pipeline_n2["ridge"]

        meta_poly = poly.transform(meta_raw)
        meta_scaled = scaler.transform(meta_poly)

        preds = ridge.predict(meta_scaled)
        decision = ridge.decision_function(meta_scaled)
        decision_t = torch.as_tensor(decision, dtype=torch.float32)
        scores = F.softmax(decision_t, dim=1).numpy()

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return preds.astype(int), scores, latency_ms

    def predict_single(self, x_pca_row: np.ndarray):
        """Predict one PCA vector through the same recovered historical path."""
        preds, scores, latency = self.predict_batch(x_pca_row[np.newaxis, :])
        return int(preds[0]), scores[0], latency
