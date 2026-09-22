from __future__ import annotations

import json
from functools import lru_cache
from hashlib import sha256

import pytest

from clean_baseline.contracts import LeakageError
from clean_baseline.ledger_io import read_ledger_rows, verify_ledger_package
from clean_baseline.oof_plan import build_oof_fold_sets, verify_oof_plan, write_oof_plan
from clean_baseline.split_ledger import SourceSample, build_ledger_rows, write_ledger_package


def _sid(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _rows():
    samples: list[SourceSample] = []
    for label in range(10):
        for index in range(5_000):
            samples.append(
                SourceSample(
                    sample_id=_sid(f"train:{label}:{index}"),
                    label=label,
                    source_partition="train",
                    source_file=f"data_batch_{1 + (index % 5)}",
                    source_index=label * 5_000 + index,
                )
            )
        for index in range(1_000):
            samples.append(
                SourceSample(
                    sample_id=_sid(f"test:{label}:{index}"),
                    label=label,
                    source_partition="test",
                    source_file="test_batch",
                    source_index=label * 1_000 + index,
                )
            )
    return build_ledger_rows(tuple(samples))


def _source_hashes() -> dict[str, str]:
    return {
        "data_batch_1": "1" * 64,
        "data_batch_2": "2" * 64,
        "data_batch_3": "3" * 64,
        "data_batch_4": "4" * 64,
        "data_batch_5": "5" * 64,
        "test_batch": "6" * 64,
    }


def test_ledger_package_roundtrip_and_hash_binding(tmp_path):
    manifest = write_ledger_package(_rows(), _source_hashes(), tmp_path)
    ledger = tmp_path / "split_ledger.csv"
    manifest_path = tmp_path / "split_ledger.manifest.json"

    verified = verify_ledger_package(ledger, manifest_path)
    assert verified["ledger_sha256"] == manifest["ledger_sha256"]
    loaded = read_ledger_rows(ledger)
    assert loaded == _rows()

    ledger.write_bytes(ledger.read_bytes() + b"\n")
    with pytest.raises(LeakageError, match="hash mismatch"):
        verify_ledger_package(ledger, manifest_path)


def test_oof_plan_is_exact_five_way_partition(tmp_path):
    fold_sets = build_oof_fold_sets(_rows())
    assert set(fold_sets) == {0, 1, 2, 3, 4}
    held_union: set[str] = set()
    for producer, held in fold_sets.values():
        assert len(producer) == 36_000
        assert len(held) == 9_000
        assert not (set(producer) & set(held))
        held_union.update(held)
    assert len(held_union) == 45_000


def test_oof_plan_roundtrip_detects_tampered_id_file(tmp_path):
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    ledger_manifest = write_ledger_package(_rows(), _source_hashes(), ledger_dir)
    ledger_path = ledger_dir / "split_ledger.csv"

    out = tmp_path / "oof"
    plan = write_oof_plan(
        _rows(),
        ledger_sha256=str(ledger_manifest["ledger_sha256"]),
        output_dir=out,
    )
    plan_path = out / "oof_plan.json"
    verified = verify_oof_plan(plan_path, ledger_path)
    assert verified["fold_count"] == 5
    assert len(verified["folds"]) == 5

    target = out / str(plan["folds"][0]["held_out_ids_file"])
    original = target.read_text(encoding="ascii")
    target.write_text(original.replace("\n", "\nBAD", 1), encoding="ascii")
    with pytest.raises(LeakageError, match="content mismatch"):
        verify_oof_plan(plan_path, ledger_path)


def test_oof_plan_rejects_wrong_ledger_binding(tmp_path):
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    manifest = write_ledger_package(_rows(), _source_hashes(), ledger_dir)
    ledger_path = ledger_dir / "split_ledger.csv"
    out = tmp_path / "oof"
    write_oof_plan(_rows(), ledger_sha256=str(manifest["ledger_sha256"]), output_dir=out)

    plan_path = out / "oof_plan.json"
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["ledger_sha256"] = "f" * 64
    plan_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(LeakageError, match="not bound"):
        verify_oof_plan(plan_path, ledger_path)
