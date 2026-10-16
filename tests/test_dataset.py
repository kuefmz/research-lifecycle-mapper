from pathlib import Path

import pytest

from lifecycle_mapper import STAGES
from lifecycle_mapper.canonical import read_json, sha256, write_json
from lifecycle_mapper.dataset import (
    DEFAULT_DATASET,
    convert_workbook,
    dataset_reference,
    execute_dataset,
)
from lifecycle_mapper.reference import final_reference
from test_batch import fake_acquisition
from test_evidence_review import final_workbook

ROOT = Path(__file__).resolve().parents[1]


def test_bundled_json_exactly_reproduces_excel_reference(tmp_path):
    source = ROOT / "data/research_lifecycle_benchmark_100_msr27.xlsx"
    dataset = read_json(ROOT / DEFAULT_DATASET)
    assert dataset["source"]["sha256"] == sha256(source.read_bytes())
    labels = dataset_reference(dataset)
    assert labels == final_reference(source)
    assert len(labels) == 100
    assert [sum(row[s] for row in labels.values()) for s in STAGES] == [36, 44, 71, 88, 66, 79]
    output = tmp_path / "fresh.json"
    convert_workbook(source, output)
    assert output.read_bytes() == (ROOT / DEFAULT_DATASET).read_bytes()
    assert not dataset["runs"] and all(not r["results"] for r in dataset["repositories"])


def test_checkpoints_append_history_without_changing_reference(tmp_path, monkeypatch):
    from lifecycle_mapper import batch

    source = final_workbook(tmp_path, count=2)
    original_workbook = source.read_bytes()
    path = tmp_path / "benchmark.json"
    convert_workbook(source, path)
    original_labels = dataset_reference(read_json(path))
    saved = []

    def acquire(url, output, ref=None, max_bytes=250000):
        # The second acquisition sees the first persisted checkpoint already.
        if saved:
            current = read_json(path)
            assert current["runs"][-1]["completed"] == 1
            assert sum(bool(r["results"]) for r in current["repositories"]) == 1
        saved.append(url)
        return fake_acquisition(url, output, ref, max_bytes)

    monkeypatch.setattr(batch, "acquire", acquire)
    first = execute_dataset(path, tmp_path / "first")
    data = read_json(path)
    assert data["runs"][0]["status"] == "completed"
    assert data["runs"][0]["completed"] == 2
    assert data["runs"][0]["output_directory"] == "first"
    assert all(
        len(r["results"][first["run_id"]]["analysis"]["modes"]) == 3 for r in data["repositories"]
    )
    assert all(
        r["results"][first["run_id"]]["analysis"]["modes"][0]["evidence"]
        for r in data["repositories"]
    )
    monkeypatch.setattr(batch, "acquire", fake_acquisition)
    second = execute_dataset(path, tmp_path / "second", modes=("documentation-only",))
    repeated = read_json(path)
    assert first["run_id"] != second["run_id"]
    assert len(repeated["runs"]) == 2
    assert all(
        set(r["results"]) == {first["run_id"], second["run_id"]} for r in repeated["repositories"]
    )
    assert dataset_reference(repeated) == original_labels
    assert not path.with_suffix(".json.lock").exists()
    assert source.read_bytes() == original_workbook


def test_failed_acquisition_is_checkpointed_as_failure_not_negative_labels(tmp_path, monkeypatch):
    from lifecycle_mapper import batch

    p = tmp_path / "benchmark.json"
    convert_workbook(final_workbook(tmp_path, count=1), p)

    def fail(*args, **kwargs):
        raise OSError("unreachable")

    monkeypatch.setattr(batch, "acquire", fail)
    result = execute_dataset(p, tmp_path / "run")
    record = read_json(p)["repositories"][0]["results"][result["run_id"]]
    assert record["status"] == "failed"
    assert record["analysis"]["modes"] == []
    assert record["analysis"]["error"] == "OSError"


def test_existing_lock_or_output_never_overwrites_history(tmp_path):
    p = tmp_path / "benchmark.json"
    convert_workbook(final_workbook(tmp_path, count=1), p)
    original = p.read_bytes()
    lock = p.with_suffix(".json.lock")
    lock.write_text("existing-owner")
    with pytest.raises(ValueError, match="locked"):
        execute_dataset(p)
    assert lock.read_text() == "existing-owner" and p.read_bytes() == original
    lock.unlink()
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(ValueError, match="new directory"):
        execute_dataset(p, output)
    assert p.read_bytes() == original
    with pytest.raises(ValueError, match="already exists"):
        convert_workbook(tmp_path / "not-read.xlsx", p)


def test_invalid_labels_and_duplicate_repositories_rejected(tmp_path):
    p = tmp_path / "benchmark.json"
    convert_workbook(final_workbook(tmp_path, count=1), p)
    data = read_json(p)
    data["repositories"][0]["human_labels"]["Method"] = None
    write_json(p, data)
    with pytest.raises(ValueError, match="binary"):
        execute_dataset(p)
    data["repositories"][0]["human_labels"]["Method"] = 1
    data["repositories"] *= 2
    with pytest.raises(ValueError, match="Duplicate"):
        dataset_reference(data)


def test_ui_bundled_benchmark_uses_dataset_checkpoints(tmp_path, monkeypatch):
    from lifecycle_mapper import batch
    from lifecycle_mapper.web import Application
    from test_web import wait_job

    root = tmp_path / "project"
    dataset = root / DEFAULT_DATASET
    dataset.parent.mkdir(parents=True)
    convert_workbook(final_workbook(tmp_path, count=1), dataset)
    monkeypatch.setattr(batch, "acquire", fake_acquisition)
    app = Application(root, tmp_path / "state")
    try:
        job = wait_job(app, app.start({"kind": "dataset", "mode": "all"})["id"])
        assert job["status"] == "completed", job
        assert job["result"]["repositories"][0]["human_labels"] is not None
        assert read_json(dataset)["runs"][0]["status"] == "completed"
    finally:
        app.pool.shutdown()


def test_dataset_json_reopens_latest_checkpoint_in_existing_ui(tmp_path, monkeypatch):
    from lifecycle_mapper import batch
    from lifecycle_mapper.dataset import dataset_results
    from lifecycle_mapper.web import Application

    p = tmp_path / "dataset.json"
    convert_workbook(final_workbook(tmp_path, count=1), p)
    with pytest.raises(ValueError, match="no saved runs"):
        dataset_results(read_json(p))
    monkeypatch.setattr(batch, "acquire", fake_acquisition)
    first = execute_dataset(p, tmp_path / "first")
    second = execute_dataset(p, tmp_path / "second", modes=("documentation-only",))
    data = read_json(p)
    assert dataset_results(data)["dataset_run_id"] == second["run_id"]
    assert len(dataset_results(data, first["run_id"])["repositories"][0]["modes"]) == 3
    app = Application(ROOT, tmp_path / "state")
    try:
        restored = app.import_results({"result": data})
        result = app.job(restored["id"])["result"]
        assert result["dataset_run_id"] == second["run_id"]
        assert result["repositories"][0]["human_labels"] == data["repositories"][0]["human_labels"]
    finally:
        app.pool.shutdown()
