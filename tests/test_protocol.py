import json
import shutil
from pathlib import Path

import pytest

from lifecycle_mapper import STAGES
from lifecycle_mapper.benchmark import run
from lifecycle_mapper.canonical import sha256, write_json
from lifecycle_mapper.protocol import (
    config_hash,
    create_split,
    frozen_guard,
    partition,
    split_records,
)

ROOT = Path(__file__).resolve().parents[1]


def test_deterministic_whole_repository_stratification():
    rows = [
        {
            "repository": f"synthetic/r-{i:03}",
            "labels": {stage: (i + j) % 2 for j, stage in enumerate(STAGES)},
        }
        for i in range(100)
    ]
    first = split_records(rows, 0.2, "seed")
    assert first == split_records(list(reversed(rows)), 0.2, "seed")
    assert len(first["test"]) == 20 and len(first["development"]) == 80
    assert not set(first["test"]) & set(first["development"])
    by_id = {row["repository"]: row for row in rows}
    for stage in STAGES:
        assert sum(by_id[repo]["labels"][stage] for repo in first["test"]) == 10


def test_split_export_contains_only_development_labels(tmp_path):
    result = create_split(ROOT / "benchmark/synthetic/manifest.json", tmp_path / "split")
    table = (tmp_path / "split/development_labels.csv").read_text()
    assert all(repo not in table for repo in result["partitions"]["test"])


def test_development_run_never_analyzes_test_snapshots(tmp_path, monkeypatch):
    from lifecycle_mapper import benchmark as module

    shutil.copytree(ROOT / "benchmark/synthetic", tmp_path / "benchmark/synthetic")
    split = create_split(tmp_path / "benchmark/synthetic/manifest.json", tmp_path / "split")
    config = {
        "benchmark_manifest": "benchmark/synthetic/manifest.json",
        "evaluation_role": "synthetic",
        "split_manifest": "split/split.json",
        "split_manifest_sha256": sha256((tmp_path / "split/split.json").read_bytes()),
        "partition": "development",
        "output": "local/output",
    }
    write_json(tmp_path / "configs/synthetic.yaml", config)
    original = module.analyze

    def guarded(snapshot, *args):
        manifest = json.loads((snapshot / "manifest.json").read_bytes())
        assert manifest["repository"] not in split["partitions"]["test"]
        return original(snapshot, *args)

    monkeypatch.setattr(module, "analyze", guarded)
    output = run(tmp_path / "configs/synthetic.yaml", tmp_path / "run")
    predictions = (output / "predictions.csv").read_text()
    assert all(repo not in predictions for repo in split["partitions"]["test"])


def test_partition_integrity_and_test_access_guard(tmp_path):
    manifest = json.loads((ROOT / "benchmark/synthetic/manifest.json").read_bytes())
    split = create_split(ROOT / "benchmark/synthetic/manifest.json", tmp_path / "split")
    checksum = sha256((ROOT / "benchmark/synthetic/manifest.json").read_bytes())
    config = {
        "split_manifest": "split/split.json",
        "split_manifest_sha256": sha256((tmp_path / "split/split.json").read_bytes()),
        "evaluation_role": "exploratory",
        "partition": "test",
    }
    with pytest.raises(ValueError, match="cannot inspect"):
        partition(config, tmp_path, manifest, checksum)
    config["partition"] = "development"
    selected = partition(config, tmp_path, manifest, checksum)
    assert {row["repository"] for row in selected} == set(split["partitions"]["development"])


def test_frozen_configuration_and_single_final_run_gate(tmp_path):
    config = {"evaluation_role": "held-out", "partition": "test", "frozen_manifest": "frozen.json"}
    state = {"commit": "a" * 40, "dirty": False}
    frozen = {
        "approval_reference": "synthetic-test-protocol",
        "classifier_commit": state["commit"],
        "classifier_source_sha256": "source",
        "catalog_sha256": "rules",
        "config_sha256": config_hash(config),
        "benchmark_sha256": "benchmark",
        "lockfile_sha256": "lock",
    }
    write_json(tmp_path / "frozen.json", frozen)
    config["frozen_manifest_sha256"] = sha256((tmp_path / "frozen.json").read_bytes())
    ledger = frozen_guard(config, tmp_path, "benchmark", "rules", state, "source", "lock", False)
    assert ledger == tmp_path / "frozen.evaluation.json"
    with pytest.raises(ValueError, match="changed"):
        frozen_guard(
            config, tmp_path, "benchmark", "modified-rules", state, "source", "lock", False
        )
    write_json(ledger, {"canonical_hashes": {}})
    with pytest.raises(ValueError, match="already executed"):
        frozen_guard(config, tmp_path, "benchmark", "rules", state, "source", "lock", False)
    assert (
        frozen_guard(config, tmp_path, "benchmark", "rules", state, "source", "lock", True)
        == ledger
    )
