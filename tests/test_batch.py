import csv
import json
import shutil
from pathlib import Path

import pytest

from lifecycle_mapper.batch import predict_batch, read_inputs, records_from_rows, sample_records

ROOT = Path(__file__).resolve().parents[1]


def fake_acquisition(url, output, ref=None, max_bytes=250000):
    if url.endswith("unavailable"):
        raise OSError("simulated network error")
    source = ROOT / "benchmark/synthetic/snapshots/docs-positive"
    shutil.copytree(source, output)
    return json.loads((output / "manifest.json").read_bytes())


def test_prediction_batch_needs_no_gold_and_replays_offline(tmp_path, monkeypatch):
    from lifecycle_mapper import batch

    monkeypatch.setattr(batch, "acquire", fake_acquisition)
    records = records_from_rows([{"repository_url": "https://github.com/synthetic/docs-positive"}])
    first = predict_batch(records, tmp_path / "live", root=ROOT)
    assert first["analyzed_count"] == 1
    assert len(first["repositories"][0]["modes"]) == 3
    manifest = json.loads((tmp_path / "live/manifest.json").read_text())
    monkeypatch.setattr(
        batch, "acquire", lambda *args, **kwargs: pytest.fail("Replay used network")
    )
    second = predict_batch(
        manifest["repositories"], tmp_path / "replay", replay_run=tmp_path / "live", root=ROOT
    )
    for name in ["predictions.csv", "evidence.jsonl", "errors.csv", "results.json"]:
        assert (tmp_path / "live" / name).read_bytes() == (tmp_path / "replay" / name).read_bytes()
    assert first == second
    repeated = json.loads((tmp_path / "replay/manifest.json").read_text())
    predict_batch(
        repeated["repositories"],
        tmp_path / "replay-again",
        replay_run=tmp_path / "replay",
        root=ROOT,
    )


def test_failures_do_not_become_negative_predictions(tmp_path, monkeypatch):
    from lifecycle_mapper import batch

    monkeypatch.setattr(batch, "acquire", fake_acquisition)
    records = records_from_rows([{"repository": "synthetic/unavailable"}])
    result = predict_batch(records, tmp_path / "run", root=ROOT)
    assert result["analyzed_count"] == 0
    assert result["repositories"][0]["error"] == "OSError"
    assert list(csv.DictReader((tmp_path / "run/predictions.csv").open())) == []


def test_csv_gold_columns_ignored_and_repositories_deduplicated(tmp_path):
    path = tmp_path / "benchmark.csv"
    path.write_text(
        "repository,stage,label\nowner/repo,Collection,unresolved\nowner/repo,Method,unresolved\nother/repo,Processing,1\n"
    )
    records = read_inputs(path)
    assert len(records) == 2 and all("label" not in row for row in records)
    assert sample_records(records, 1, "seed") == sample_records(records, 1, "seed")


def test_conflicting_revisions_rejected():
    with pytest.raises(ValueError, match="Conflicting revisions"):
        records_from_rows(
            [
                {"repository": "owner/repo", "commit": "a"},
                {"repository": "owner/repo", "commit": "b"},
            ]
        )


def test_workbook_predictions_ignore_unresolved_stage_labels(tmp_path):
    from test_consensus import fixture

    path, _ = fixture(tmp_path, mutation=lambda row, i: row.__setitem__(2, "unresolved"))
    records = read_inputs(path, "B")
    assert len(records) == 100
    assert records[0]["source_rows"] == [2]
