from __future__ import annotations

import argparse
import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .contracts import LeakageError
from .ledger_io import verify_ledger_package
from .oof_plan import verify_oof_plan
from .split_ledger import PROTOCOL_ID, sha256_file


def _require_sha256(value: str, name: str) -> str:
    if len(value) != 64:
        raise LeakageError(f"{name} must be a 64-character SHA-256 value")
    try:
        int(value, 16)
    except ValueError as exc:
        raise LeakageError(f"{name} is not hexadecimal") from exc
    return value.lower()


def _require_commit_sha(value: str) -> str:
    if len(value) != 40:
        raise LeakageError("source_commit must be a full 40-character Git commit SHA")
    try:
        int(value, 16)
    except ValueError as exc:
        raise LeakageError("source_commit is not hexadecimal") from exc
    return value.lower()


def _relative_display(path: Path, root: Path) -> str:
    path = Path(path).resolve()
    root = Path(root).resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _hash_entries(paths: Sequence[Path], root: Path) -> list[dict[str, object]]:
    if not paths:
        raise LeakageError("candidate freeze requires at least one fitted/pretest artifact")
    seen: set[Path] = set()
    entries: list[dict[str, object]] = []
    for raw_path in paths:
        path = Path(raw_path).resolve()
        if path in seen:
            raise LeakageError(f"duplicate artifact path in candidate freeze: {path}")
        seen.add(path)
        if not path.is_file():
            raise LeakageError(f"candidate artifact does not exist: {path}")
        entries.append(
            {
                "path": _relative_display(path, root),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    entries.sort(key=lambda item: str(item["path"]))
    return entries


def _load_template(path: Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LeakageError("candidate manifest template must be a JSON object")
    if payload.get("protocol_id") != PROTOCOL_ID:
        raise LeakageError("candidate manifest template protocol_id mismatch")
    return payload


def freeze_candidate(
    *,
    template_path: Path,
    candidate_id: str,
    source_commit: str,
    dataset_source_description: str,
    raw_source_sha256: str,
    ledger_path: Path,
    ledger_manifest_path: Path,
    oof_plan_path: Path,
    frozen_config_path: Path,
    environment_lock_path: Path,
    feature_order_path: Path,
    artifact_paths: Sequence[Path],
    commands: Sequence[str],
    output_dir: Path,
) -> tuple[Path, Path]:
    if not candidate_id.strip() or candidate_id == "UNSET":
        raise LeakageError("candidate_id must be a non-empty frozen identifier")
    if not dataset_source_description.strip():
        raise LeakageError("dataset_source_description must be non-empty")
    if not commands or any(not command.strip() for command in commands):
        raise LeakageError("candidate freeze requires at least one exact non-empty command")

    source_commit = _require_commit_sha(source_commit)
    raw_source_sha256 = _require_sha256(raw_source_sha256, "raw_source_sha256")

    ledger_path = Path(ledger_path)
    ledger_manifest_path = Path(ledger_manifest_path)
    oof_plan_path = Path(oof_plan_path)
    frozen_config_path = Path(frozen_config_path)
    environment_lock_path = Path(environment_lock_path)
    feature_order_path = Path(feature_order_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ledger_manifest = verify_ledger_package(ledger_path, ledger_manifest_path)
    verify_oof_plan(oof_plan_path, ledger_path)

    for path, label in (
        (frozen_config_path, "frozen config"),
        (environment_lock_path, "environment lock"),
        (feature_order_path, "feature order"),
    ):
        if not path.is_file():
            raise LeakageError(f"{label} file does not exist: {path}")

    artifact_entries = _hash_entries(tuple(artifact_paths), output_dir)
    pretest_manifest: dict[str, object] = {
        "protocol_id": PROTOCOL_ID,
        "candidate_id": candidate_id,
        "source_commit": source_commit,
        "dataset": {
            "source_description": dataset_source_description,
            "raw_source_sha256": raw_source_sha256,
        },
        "split_ledger": {
            "path": _relative_display(ledger_path, output_dir),
            "sha256": str(ledger_manifest["ledger_sha256"]),
            "manifest_path": _relative_display(ledger_manifest_path, output_dir),
            "manifest_sha256": sha256_file(ledger_manifest_path),
        },
        "oof_plan": {
            "path": _relative_display(oof_plan_path, output_dir),
            "sha256": sha256_file(oof_plan_path),
        },
        "frozen_config": {
            "path": _relative_display(frozen_config_path, output_dir),
            "sha256": sha256_file(frozen_config_path),
        },
        "environment_lock": {
            "path": _relative_display(environment_lock_path, output_dir),
            "sha256": sha256_file(environment_lock_path),
        },
        "feature_order": {
            "path": _relative_display(feature_order_path, output_dir),
            "sha256": sha256_file(feature_order_path),
        },
        "artifacts": artifact_entries,
        "commands": list(commands),
        "final_test_access_count_at_freeze": 0,
        "note": "This evidence freeze does not authorize final-test evaluation. Leakage and batch-invariance gates must still pass and the final-test seal must be opened explicitly.",
    }
    pretest_bytes = (json.dumps(pretest_manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    pretest_path = output_dir / "pretest_evidence_manifest.json"
    pretest_path.write_bytes(pretest_bytes)
    pretest_sha = sha256(pretest_bytes).hexdigest()

    manifest = deepcopy(_load_template(template_path))
    manifest["candidate_id"] = candidate_id
    manifest["status"] = "FROZEN_PRETEST"
    manifest["source_commit"] = source_commit

    dataset = manifest["dataset"]
    splits = manifest["splits"]
    config = manifest["config"]
    environment = manifest["environment"]
    features = manifest["features"]
    artifacts = manifest["artifacts"]
    final_test = manifest["final_test"]
    if not all(isinstance(section, dict) for section in (dataset, splits, config, environment, features, artifacts, final_test)):
        raise LeakageError("candidate manifest template structure is invalid")

    dataset["source_description"] = dataset_source_description
    dataset["raw_source_sha256"] = raw_source_sha256
    splits["ledger_path"] = _relative_display(ledger_path, output_dir)
    splits["ledger_sha256"] = str(ledger_manifest["ledger_sha256"])
    config["path"] = _relative_display(frozen_config_path, output_dir)
    config["frozen_config_sha256"] = sha256_file(frozen_config_path)
    environment["lock_path"] = _relative_display(environment_lock_path, output_dir)
    environment["lock_sha256"] = sha256_file(environment_lock_path)
    features["feature_order_path"] = _relative_display(feature_order_path, output_dir)
    features["feature_order_sha256"] = sha256_file(feature_order_path)
    artifacts["pretest_manifest_path"] = pretest_path.name
    artifacts["pretest_manifest_sha256"] = pretest_sha
    manifest["commands"] = list(commands)
    final_test["sealed"] = False
    final_test["decisions_frozen"] = True
    final_test["access_count_before_seal"] = 0
    final_test["first_authorized_command"] = "UNSET"
    final_test["result_path"] = "UNSET"

    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest_path = output_dir / "candidate.manifest.json"
    manifest_path.write_bytes(manifest_bytes)
    return pretest_path, manifest_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Freeze a Clean Baseline v1 candidate evidence package before final-test authorization"
    )
    parser.add_argument("--template", type=Path, default=Path(__file__).with_name("manifest.template.json"))
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--dataset-source-description", required=True)
    parser.add_argument("--raw-source-sha256", required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--ledger-manifest", type=Path, required=True)
    parser.add_argument("--oof-plan", type=Path, required=True)
    parser.add_argument("--frozen-config", type=Path, required=True)
    parser.add_argument("--environment-lock", type=Path, required=True)
    parser.add_argument("--feature-order", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, action="append", required=True)
    parser.add_argument("--command", action="append", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)

    pretest_path, manifest_path = freeze_candidate(
        template_path=args.template,
        candidate_id=args.candidate_id,
        source_commit=args.source_commit,
        dataset_source_description=args.dataset_source_description,
        raw_source_sha256=args.raw_source_sha256,
        ledger_path=args.ledger,
        ledger_manifest_path=args.ledger_manifest,
        oof_plan_path=args.oof_plan,
        frozen_config_path=args.frozen_config,
        environment_lock_path=args.environment_lock,
        feature_order_path=args.feature_order,
        artifact_paths=tuple(args.artifact),
        commands=tuple(args.command),
        output_dir=args.out_dir,
    )
    print(f"PASS: candidate evidence frozen at {manifest_path}")
    print(f"PASS: pretest evidence manifest written at {pretest_path}")
    print("SEALED: final test remains unauthorized until leakage and batch-invariance gates pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
