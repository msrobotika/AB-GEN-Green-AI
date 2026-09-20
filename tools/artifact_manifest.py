"""Create and verify AB-GEN artifact manifests.

The manifest intentionally records filenames, sizes and SHA-256 digests but not
absolute local paths, so it can be shared without leaking a workstation layout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def current_git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def parse_artifact_specs(specs: list[str]) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"Artifact spec must be NAME=PATH, got: {spec!r}")
        name, raw_path = spec.split("=", 1)
        name = name.strip()
        if not name:
            raise ValueError("Artifact name cannot be empty")
        if name in artifacts:
            raise ValueError(f"Duplicate artifact name: {name}")
        path = Path(raw_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        artifacts[name] = path
    if not artifacts:
        raise ValueError("At least one --artifact NAME=PATH is required")
    return artifacts


def create_manifest(artifacts: dict[str, Path]) -> dict:
    entries = {}
    for name, path in sorted(artifacts.items()):
        entries[name] = {
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": current_git_commit(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "artifacts": entries,
    }


def write_manifest(manifest: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported manifest schema: {manifest.get('schema_version')!r}"
        )
    if not isinstance(manifest.get("artifacts"), dict):
        raise ValueError("Manifest does not contain an artifacts object")
    return manifest


def verify_manifest(manifest: dict, artifacts: dict[str, Path]) -> list[str]:
    errors: list[str] = []
    expected = manifest["artifacts"]

    missing_labels = sorted(set(expected) - set(artifacts))
    extra_labels = sorted(set(artifacts) - set(expected))
    if missing_labels:
        errors.append("Missing artifact labels: " + ", ".join(missing_labels))
    if extra_labels:
        errors.append("Unexpected artifact labels: " + ", ".join(extra_labels))

    for name in sorted(set(expected) & set(artifacts)):
        path = artifacts[name]
        entry = expected[name]
        actual_size = path.stat().st_size
        actual_sha = sha256_file(path)

        if entry.get("filename") != path.name:
            errors.append(
                f"{name}: filename mismatch: expected {entry.get('filename')!r}, got {path.name!r}"
            )
        if entry.get("size_bytes") != actual_size:
            errors.append(
                f"{name}: size mismatch: expected {entry.get('size_bytes')}, got {actual_size}"
            )
        if entry.get("sha256") != actual_sha:
            errors.append(
                f"{name}: SHA-256 mismatch: expected {entry.get('sha256')}, got {actual_sha}"
            )

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a manifest")
    create.add_argument("--artifact", action="append", default=[], metavar="NAME=PATH")
    create.add_argument("--output", required=True, type=Path)

    verify = sub.add_parser("verify", help="Verify files against a manifest")
    verify.add_argument("--manifest", required=True, type=Path)
    verify.add_argument("--artifact", action="append", default=[], metavar="NAME=PATH")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        artifacts = parse_artifact_specs(args.artifact)
        if args.command == "create":
            manifest = create_manifest(artifacts)
            write_manifest(manifest, args.output)
            print(f"Wrote artifact manifest: {args.output}")
            return 0

        manifest = load_manifest(args.manifest)
        errors = verify_manifest(manifest, artifacts)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 2
        print("Artifact manifest verification passed.")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
