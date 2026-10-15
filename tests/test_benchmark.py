import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from lifecycle_mapper import STAGES
from lifecycle_mapper.annotations import FIELDS, import_annotations
from lifecycle_mapper.benchmark import calculate_metrics, run, validate_manifest, verify
from lifecycle_mapper.canonical import write_json

ROOT = Path(__file__).resolve().parents[1]


def test_known_metrics():
    negative = dict.fromkeys(STAGES, 0)
    positive = {**negative, "Collection": 1}
    metrics = calculate_metrics([positive, negative], [[], ["Collection"]])
    assert metrics["per_stage"][0] == {
        "stage": "Collection",
        "TP": 0,
        "FP": 1,
        "TN": 0,
        "FN": 1,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 1,
        "accuracy": 0.0,
    }
    assert metrics["hamming_loss"] == round(2 / 12, 8)
    assert metrics["exact_match_accuracy"] == 0
    assert calculate_metrics([], [])["repository_count"] == 0


def test_benchmark_outputs_and_failure_policy(tmp_path):
    output = run(ROOT / "configs/synthetic.yaml", tmp_path / "run")
    metrics = json.loads((output / "metrics.json").read_bytes())
    assert metrics["documentation-only"]["repository_count"] == 4
    assert metrics["code-only"]["repository_count"] == 5
    assert metrics["combined"]["repository_count"] == 4
    assert metrics["documentation-only"]["analysis_failure_rate"] == 0.2
    assert metrics["combined"]["micro"]["f1"] == 1.0
    errors = list(csv.DictReader((output / "errors.csv").open()))
    assert any(row["type"] == "FN" for row in errors)
    assert any(row["type"] == "acquisition-failure" for row in errors)
    with pytest.raises(ValueError, match="new directory"):
        run(ROOT / "configs/synthetic.yaml", output)


def test_deterministic_rerun(tmp_path):
    hashes = verify(ROOT / "configs/synthetic.yaml", tmp_path / "verify")
    assert "manifest.json" in hashes
    assert len(hashes["metrics.json"]) == 64


def test_pending_research_benchmark_rejected(tmp_path):
    with pytest.raises(ValueError, match="pending"):
        run(ROOT / "configs/benchmark.yaml", tmp_path / "run")


def test_leakage_guard(tmp_path):
    data = json.loads((ROOT / "benchmark/synthetic/manifest.json").read_bytes())
    data.update(
        kind="research", held_out_approval_reference="approval", used_for_rule_development=True
    )
    path = tmp_path / "manifest.json"
    write_json(path, data)
    with pytest.raises(ValueError, match="leakage"):
        validate_manifest(path, "held-out", ["synthetic/docs-positive"])


def test_synthetic_cannot_be_research_results():
    with pytest.raises(ValueError, match="Synthetic metrics"):
        validate_manifest(ROOT / "benchmark/synthetic/manifest.json", "exploratory", [])


def annotation_source(tmp_path, change=None):
    path = tmp_path / "annotations.csv"
    rows = []
    for index, stage in enumerate(STAGES):
        row = dict(
            repository="owner/repo",
            stage=stage,
            jenifer="1",
            esteban="0" if index == 0 else "1",
            proposed_consensus="1",
            approved_consensus="",
            approval_reference="",
        )
        if change:
            change(row, index)
        rows.append(row)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_annotation_import_preserves_source_and_provisional_status(tmp_path):
    path = annotation_source(tmp_path)
    before = path.read_bytes()
    provenance = import_annotations(path, tmp_path / "imported", "test-v1", 1, 1)
    assert path.read_bytes() == before
    assert provenance["gold_status"] == "pending"
    assert provenance["initial_disagreements"] == 1


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row, index: row.update(jenifer="maybe") if index == 0 else None,
        lambda row, index: row.update(stage="Implementation") if index == 0 else None,
        lambda row, index: row.update(approved_consensus="1") if index == 0 else None,
        lambda row, index: row.update(stage="Collection") if index == 1 else None,
    ],
)
def test_malformed_annotation_rejected(tmp_path, mutation):
    path = annotation_source(tmp_path, mutation)
    with pytest.raises(ValueError):
        import_annotations(path, tmp_path / "imported", "test-v1", 1, 1)
    assert not (tmp_path / "imported").exists()


def test_missing_annotation_rows(tmp_path):
    path = annotation_source(tmp_path)
    path.write_text("\n".join(path.read_text().splitlines()[:-1]) + "\n")
    with pytest.raises(ValueError, match="six labels"):
        import_annotations(path, tmp_path / "imported", "test-v1", 1, 1)


def test_snapshot_identity_mismatch(tmp_path):
    root = tmp_path / "project"
    (root / "configs").mkdir(parents=True)
    shutil.copytree(ROOT / "benchmark/synthetic", root / "benchmark/synthetic")
    data = json.loads((root / "benchmark/synthetic/manifest.json").read_bytes())
    data["repositories"][0]["commit"] = "a" * 40
    write_json(root / "benchmark/synthetic/manifest.json", data)
    config = json.loads((ROOT / "configs/synthetic.yaml").read_bytes())
    config.pop("rules_dir")
    write_json(root / "configs/synthetic.yaml", config)
    with pytest.raises(ValueError, match="identity mismatch"):
        run(root / "configs/synthetic.yaml", tmp_path / "run")


def test_cli_offline_replay(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lifecycle_mapper",
            "analyze",
            "--snapshot",
            str(ROOT / "benchmark/synthetic/snapshots/docs-positive"),
        ],
        cwd=ROOT,
        env={"PATH": str(Path(sys.executable).parent), "PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["labels"] == list(STAGES)
