from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
from sklearn.decomposition import PCA

from .contracts import LeakageError, SplitLedger
from .raw_store import NormalizedBatch, cifar_raw_feature_names
from .stage_audit import (
    FitAuthorization,
    OOFProducerAuthorization,
    StageReceipt,
    authorize_fit,
    authorize_oof_producer,
    authorize_transform,
    hash_feature_order,
    make_stage_receipt,
)


PROTOCOL_ID = "abgen-clean-baseline-v1"
PCA_ARTIFACT_SCHEMA = "abgen-pca-artifact-v1"
PCA_ARTIFACT_MAGIC = b"ABGEN-PCA-V1\n"
PCA_INPUT_FEATURE_COUNT = 32 * 32 * 3
_ALLOWED_FIT_PHASES = frozenset({"development_preprocessing_fit", "oof_producer_fit", "final_preprocessing_refit"})
_ALLOWED_DTYPES = frozenset({"float32", "float64"})
_ALLOWED_SOLVERS = frozenset({"full", "randomized"})
_ARRAY_ORDER = (
    "mean",
    "components",
    "explained_variance",
    "explained_variance_ratio",
    "singular_values",
)


@dataclass(frozen=True)
class PCAConfig:
    n_components: int
    svd_solver: str = "full"
    fit_dtype: str = "float64"
    whiten: bool = False
    random_state: int | None = None
    iterated_power: int = 4
    n_oversamples: int = 10
    power_iteration_normalizer: str = "QR"

    def validate(self) -> None:
        if not isinstance(self.n_components, int) or isinstance(self.n_components, bool) or self.n_components <= 0:
            raise LeakageError("PCA n_components must be a positive integer")
        if self.svd_solver not in _ALLOWED_SOLVERS:
            raise LeakageError(
                f"PCA svd_solver must be explicit and one of {sorted(_ALLOWED_SOLVERS)}; "
                f"got {self.svd_solver!r}"
            )
        if self.fit_dtype not in _ALLOWED_DTYPES:
            raise LeakageError(f"PCA fit_dtype must be one of {sorted(_ALLOWED_DTYPES)}")
        if self.whiten:
            raise LeakageError("PCA whitening is not implemented in Clean Baseline v1 audited PCA")
        if not isinstance(self.iterated_power, int) or isinstance(self.iterated_power, bool) or self.iterated_power < 1:
            raise LeakageError("PCA iterated_power must be an integer >= 1")
        if not isinstance(self.n_oversamples, int) or isinstance(self.n_oversamples, bool) or self.n_oversamples < 1:
            raise LeakageError("PCA n_oversamples must be an integer >= 1")
        if self.power_iteration_normalizer not in {"QR", "LU", "none"}:
            raise LeakageError("PCA power_iteration_normalizer must be one of QR, LU or none")

        if self.svd_solver == "full":
            if self.random_state is not None:
                raise LeakageError("full PCA is deterministic and requires random_state=None")
        else:
            if not isinstance(self.random_state, int) or isinstance(self.random_state, bool):
                raise LeakageError("randomized PCA requires an explicit integer random_state")


@dataclass(frozen=True)
class PCATransformedBatch:
    sample_ids: tuple[str, ...]
    labels: np.ndarray
    values: np.ndarray
    feature_names: tuple[str, ...]
    receipt: StageReceipt


@dataclass(frozen=True)
class PCAArtifact:
    config: PCAConfig
    n_samples_fit: int
    n_features_in: int
    input_feature_order_sha256: str
    output_feature_order_sha256: str
    fit_authorization: FitAuthorization | OOFProducerAuthorization
    mean: np.ndarray
    components: np.ndarray
    explained_variance: np.ndarray
    explained_variance_ratio: np.ndarray
    singular_values: np.ndarray

    @property
    def feature_names(self) -> tuple[str, ...]:
        return pca_feature_names(self.config.n_components)

    @property
    def artifact_sha256(self) -> str:
        return sha256(self.to_bytes()).hexdigest()

    def _validated_arrays(self) -> dict[str, np.ndarray]:
        self.config.validate()
        if not isinstance(self.n_samples_fit, int) or self.n_samples_fit <= 0:
            raise LeakageError("PCA artifact n_samples_fit must be positive")
        if self.n_features_in != PCA_INPUT_FEATURE_COUNT:
            raise LeakageError(
                f"PCA artifact requires {PCA_INPUT_FEATURE_COUNT} input features, got {self.n_features_in}"
            )
        _require_sha256(self.input_feature_order_sha256, "input_feature_order_sha256")
        _require_sha256(self.output_feature_order_sha256, "output_feature_order_sha256")

        expected_input_hash = hash_feature_order(cifar_raw_feature_names())
        expected_output_hash = hash_feature_order(self.feature_names)
        if self.input_feature_order_sha256 != expected_input_hash:
            raise LeakageError("PCA artifact input feature-order hash is not the frozen CIFAR RAW order")
        if self.output_feature_order_sha256 != expected_output_hash:
            raise LeakageError("PCA artifact output feature-order hash does not match n_components")

        expected_shapes = {
            "mean": (self.n_features_in,),
            "components": (self.config.n_components, self.n_features_in),
            "explained_variance": (self.config.n_components,),
            "explained_variance_ratio": (self.config.n_components,),
            "singular_values": (self.config.n_components,),
        }
        arrays = {
            "mean": self.mean,
            "components": self.components,
            "explained_variance": self.explained_variance,
            "explained_variance_ratio": self.explained_variance_ratio,
            "singular_values": self.singular_values,
        }
        result: dict[str, np.ndarray] = {}
        for name in _ARRAY_ORDER:
            value = np.asarray(arrays[name])
            if value.shape != expected_shapes[name]:
                raise LeakageError(
                    f"PCA artifact array {name!r} shape mismatch: {value.shape}; expected={expected_shapes[name]}"
                )
            if str(value.dtype) != self.config.fit_dtype:
                raise LeakageError(
                    f"PCA artifact array {name!r} dtype mismatch: {value.dtype}; expected={self.config.fit_dtype}"
                )
            if not np.isfinite(value).all():
                raise LeakageError(f"PCA artifact array {name!r} contains non-finite values")
            result[name] = _canonical_float_array(value, self.config.fit_dtype)

        if np.any(result["explained_variance"] < 0.0):
            raise LeakageError("PCA explained variance contains negative values")
        if np.any(result["explained_variance_ratio"] < 0.0):
            raise LeakageError("PCA explained variance ratio contains negative values")
        return result

    def to_bytes(self) -> bytes:
        arrays = self._validated_arrays()
        header = {
            "protocol_id": PROTOCOL_ID,
            "schema": PCA_ARTIFACT_SCHEMA,
            "config": asdict(self.config),
            "n_samples_fit": self.n_samples_fit,
            "n_features_in": self.n_features_in,
            "input_feature_order_sha256": self.input_feature_order_sha256,
            "output_feature_order_sha256": self.output_feature_order_sha256,
            "fit_authorization_type": type(self.fit_authorization).__name__,
            "fit_authorization": asdict(self.fit_authorization),
            "arrays": [
                {
                    "name": name,
                    "dtype": arrays[name].dtype.str,
                    "shape": list(arrays[name].shape),
                    "nbytes": int(arrays[name].nbytes),
                }
                for name in _ARRAY_ORDER
            ],
        }
        header_bytes = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")
        payload = bytearray(PCA_ARTIFACT_MAGIC)
        payload.extend(len(header_bytes).to_bytes(8, "big"))
        payload.extend(header_bytes)
        for name in _ARRAY_ORDER:
            payload.extend(arrays[name].tobytes(order="C"))
        return bytes(payload)

    @classmethod
    def from_bytes(cls, payload: bytes) -> "PCAArtifact":
        if not isinstance(payload, (bytes, bytearray, memoryview)):
            raise TypeError("PCA artifact payload must be bytes-like")
        raw = bytes(payload)
        prefix_len = len(PCA_ARTIFACT_MAGIC)
        if not raw.startswith(PCA_ARTIFACT_MAGIC):
            raise LeakageError("PCA artifact magic/schema prefix mismatch")
        if len(raw) < prefix_len + 8:
            raise LeakageError("PCA artifact is truncated before header length")

        header_len = int.from_bytes(raw[prefix_len : prefix_len + 8], "big")
        header_start = prefix_len + 8
        header_end = header_start + header_len
        if header_len <= 0 or header_end > len(raw):
            raise LeakageError("PCA artifact header length is invalid")
        try:
            header = json.loads(raw[header_start:header_end].decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LeakageError("PCA artifact header is not valid canonical JSON") from exc
        if not isinstance(header, Mapping):
            raise LeakageError("PCA artifact header must be a JSON object")
        if header.get("protocol_id") != PROTOCOL_ID or header.get("schema") != PCA_ARTIFACT_SCHEMA:
            raise LeakageError("PCA artifact protocol/schema mismatch")

        config_obj = header.get("config")
        if not isinstance(config_obj, Mapping):
            raise LeakageError("PCA artifact config is missing")
        try:
            config = PCAConfig(**dict(config_obj))
        except TypeError as exc:
            raise LeakageError("PCA artifact config fields are invalid") from exc
        config.validate()

        authorization = _authorization_from_header(header)
        array_specs = header.get("arrays")
        if not isinstance(array_specs, Sequence) or isinstance(array_specs, (str, bytes)):
            raise LeakageError("PCA artifact arrays metadata is invalid")
        if len(array_specs) != len(_ARRAY_ORDER):
            raise LeakageError("PCA artifact arrays metadata count mismatch")

        offset = header_end
        arrays: dict[str, np.ndarray] = {}
        for expected_name, spec_obj in zip(_ARRAY_ORDER, array_specs):
            if not isinstance(spec_obj, Mapping) or spec_obj.get("name") != expected_name:
                raise LeakageError("PCA artifact array order/name mismatch")
            dtype_text = spec_obj.get("dtype")
            shape_obj = spec_obj.get("shape")
            nbytes_obj = spec_obj.get("nbytes")
            if not isinstance(dtype_text, str):
                raise LeakageError(f"PCA array {expected_name!r} dtype metadata is invalid")
            if not isinstance(shape_obj, Sequence) or isinstance(shape_obj, (str, bytes)):
                raise LeakageError(f"PCA array {expected_name!r} shape metadata is invalid")
            try:
                shape = tuple(int(dim) for dim in shape_obj)
                dtype = np.dtype(dtype_text)
                nbytes = int(nbytes_obj)
            except (TypeError, ValueError) as exc:
                raise LeakageError(f"PCA array {expected_name!r} metadata is invalid") from exc
            expected_nbytes = int(np.prod(shape, dtype=np.int64)) * dtype.itemsize
            if nbytes != expected_nbytes or nbytes < 0:
                raise LeakageError(f"PCA array {expected_name!r} byte count mismatch")
            end = offset + nbytes
            if end > len(raw):
                raise LeakageError(f"PCA artifact is truncated inside array {expected_name!r}")
            value = np.frombuffer(raw[offset:end], dtype=dtype).reshape(shape).copy()
            value = value.astype(config.fit_dtype, copy=False)
            value.setflags(write=False)
            arrays[expected_name] = value
            offset = end

        if offset != len(raw):
            raise LeakageError("PCA artifact contains trailing bytes")

        try:
            n_samples_fit = int(header["n_samples_fit"])
            n_features_in = int(header["n_features_in"])
            input_feature_hash = str(header["input_feature_order_sha256"])
            output_feature_hash = str(header["output_feature_order_sha256"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LeakageError("PCA artifact required metadata is invalid") from exc

        artifact = cls(
            config=config,
            n_samples_fit=n_samples_fit,
            n_features_in=n_features_in,
            input_feature_order_sha256=input_feature_hash,
            output_feature_order_sha256=output_feature_hash,
            fit_authorization=authorization,
            mean=arrays["mean"],
            components=arrays["components"],
            explained_variance=arrays["explained_variance"],
            explained_variance_ratio=arrays["explained_variance_ratio"],
            singular_values=arrays["singular_values"],
        )
        artifact._validated_arrays()
        return artifact


def _require_sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise LeakageError(f"{name} must be a 64-character SHA-256 value")
    try:
        int(value, 16)
    except ValueError as exc:
        raise LeakageError(f"{name} is not valid hexadecimal") from exc
    return value.lower()


def _canonical_float_array(value: np.ndarray, dtype_name: str) -> np.ndarray:
    dtype = np.dtype("<f4" if dtype_name == "float32" else "<f8")
    result = np.ascontiguousarray(np.asarray(value, dtype=dtype))
    return result


def _authorization_from_header(header: Mapping[str, object]) -> FitAuthorization | OOFProducerAuthorization:
    kind = header.get("fit_authorization_type")
    payload = header.get("fit_authorization")
    if not isinstance(payload, Mapping):
        raise LeakageError("PCA artifact fit authorization is missing")
    try:
        if kind == "FitAuthorization":
            return FitAuthorization(**dict(payload))
        if kind == "OOFProducerAuthorization":
            return OOFProducerAuthorization(**dict(payload))
    except TypeError as exc:
        raise LeakageError("PCA artifact fit authorization fields are invalid") from exc
    raise LeakageError(f"PCA artifact fit authorization type is invalid: {kind!r}")


def pca_feature_names(n_components: int) -> tuple[str, ...]:
    if not isinstance(n_components, int) or isinstance(n_components, bool) or n_components <= 0:
        raise LeakageError("PCA feature count must be a positive integer")
    return tuple(f"pca_{index:04d}" for index in range(n_components))


def _validate_normalized_batch(batch: NormalizedBatch) -> None:
    if not isinstance(batch.sample_ids, tuple) or not batch.sample_ids:
        raise LeakageError("PCA stage requires a non-empty ordered sample-ID tuple")
    if len(batch.sample_ids) != len(set(batch.sample_ids)):
        raise LeakageError("PCA stage received duplicate sample IDs")
    if batch.values.ndim != 2 or batch.values.shape != (len(batch.sample_ids), PCA_INPUT_FEATURE_COUNT):
        raise LeakageError(
            f"PCA stage expects values shape (N, {PCA_INPUT_FEATURE_COUNT}), got {batch.values.shape}"
        )
    if str(batch.values.dtype) not in _ALLOWED_DTYPES:
        raise LeakageError(f"PCA stage requires float32/float64 normalized input, got {batch.values.dtype}")
    if batch.labels.shape != (len(batch.sample_ids),):
        raise LeakageError("PCA stage label/sample count mismatch")
    if not np.isfinite(batch.values).all():
        raise LeakageError("PCA stage input contains non-finite values")


def _sklearn_pca(config: PCAConfig) -> PCA:
    kwargs: dict[str, object] = {
        "n_components": config.n_components,
        "svd_solver": config.svd_solver,
        "whiten": False,
    }
    if config.svd_solver == "randomized":
        kwargs.update(
            {
                "random_state": config.random_state,
                "iterated_power": config.iterated_power,
                "n_oversamples": config.n_oversamples,
                "power_iteration_normalizer": config.power_iteration_normalizer,
            }
        )
    return PCA(**kwargs)


def fit_pca(
    batch: NormalizedBatch,
    *,
    ledger: SplitLedger,
    config: PCAConfig,
    phase: str,
    oof_held_out_ids: Sequence[str] | None = None,
    fold_id: int | None = None,
) -> PCAArtifact:
    config.validate()
    _validate_normalized_batch(batch)
    if phase not in _ALLOWED_FIT_PHASES:
        raise LeakageError(f"PCA fit phase is not permitted: {phase!r}")
    if config.n_components > min(batch.values.shape):
        raise LeakageError(
            f"PCA n_components={config.n_components} exceeds min(input shape)={min(batch.values.shape)}"
        )

    if phase == "oof_producer_fit":
        if oof_held_out_ids is None or fold_id is None:
            raise LeakageError("OOF PCA fit requires held-out IDs and fold_id")
        authorization: FitAuthorization | OOFProducerAuthorization = authorize_oof_producer(
            ledger,
            batch.sample_ids,
            oof_held_out_ids,
            stage="pca",
            fold_id=fold_id,
        )
    else:
        if oof_held_out_ids is not None or fold_id is not None:
            raise LeakageError("non-OOF PCA fit must not receive OOF held-out IDs or fold_id")
        authorization = authorize_fit(ledger, batch.sample_ids, stage="pca", phase=phase)

    values = np.ascontiguousarray(batch.values.astype(config.fit_dtype, copy=False))
    estimator = _sklearn_pca(config)
    estimator.fit(values)

    artifact = PCAArtifact(
        config=config,
        n_samples_fit=len(batch.sample_ids),
        n_features_in=int(estimator.n_features_in_),
        input_feature_order_sha256=hash_feature_order(cifar_raw_feature_names()),
        output_feature_order_sha256=hash_feature_order(pca_feature_names(config.n_components)),
        fit_authorization=authorization,
        mean=_frozen_array(estimator.mean_, config.fit_dtype),
        components=_frozen_array(estimator.components_, config.fit_dtype),
        explained_variance=_frozen_array(estimator.explained_variance_, config.fit_dtype),
        explained_variance_ratio=_frozen_array(estimator.explained_variance_ratio_, config.fit_dtype),
        singular_values=_frozen_array(estimator.singular_values_, config.fit_dtype),
    )
    artifact._validated_arrays()
    return artifact


def _frozen_array(value: object, dtype_name: str) -> np.ndarray:
    array = np.ascontiguousarray(np.asarray(value, dtype=dtype_name)).copy()
    array.setflags(write=False)
    return array


def transform_pca(
    artifact: PCAArtifact,
    batch: NormalizedBatch,
    *,
    ledger: SplitLedger,
    purpose: str,
    final_test_authorized: bool = False,
) -> PCATransformedBatch:
    _validate_normalized_batch(batch)
    artifact._validated_arrays()
    authorize_transform(
        ledger,
        batch.sample_ids,
        purpose=purpose,
        final_test_authorized=final_test_authorized,
    )

    values = np.ascontiguousarray(batch.values.astype(artifact.config.fit_dtype, copy=False))
    transformed = (values - artifact.mean) @ artifact.components.T
    transformed = np.ascontiguousarray(transformed, dtype=artifact.config.fit_dtype)
    if transformed.shape != (len(batch.sample_ids), artifact.config.n_components):
        raise LeakageError(f"PCA transform shape mismatch: {transformed.shape}")
    if not np.isfinite(transformed).all():
        raise LeakageError("PCA transform produced non-finite values")

    feature_names = artifact.feature_names
    receipt = make_stage_receipt(
        stage="pca",
        operation="transform",
        purpose=purpose,
        input_values=batch.values,
        output_values=transformed,
        sample_ids=batch.sample_ids,
        input_feature_names=cifar_raw_feature_names(),
        output_feature_names=feature_names,
        fit_authorization=artifact.fit_authorization,
        artifact_sha256=artifact.artifact_sha256,
    )

    labels = batch.labels.copy()
    labels.setflags(write=False)
    transformed.setflags(write=False)
    return PCATransformedBatch(
        sample_ids=batch.sample_ids,
        labels=labels,
        values=transformed,
        feature_names=feature_names,
        receipt=receipt,
    )


def save_pca_artifact(artifact: PCAArtifact, path: Path) -> str:
    payload = artifact.to_bytes()
    Path(path).write_bytes(payload)
    return sha256(payload).hexdigest()


def load_pca_artifact(path: Path) -> PCAArtifact:
    payload = Path(path).read_bytes()
    artifact = PCAArtifact.from_bytes(payload)
    if sha256(artifact.to_bytes()).hexdigest() != sha256(payload).hexdigest():
        raise LeakageError("PCA artifact canonical roundtrip hash mismatch")
    return artifact
