import csv
import hashlib
import io
import shutil
from pathlib import Path
from urllib.error import HTTPError

import pytest

from lifecycle_mapper import acquisition, corpus
from lifecycle_mapper.analysis import load_rules
from lifecycle_mapper.canonical import read_json, write_json

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def inline_fake_acquisition(monkeypatch):
    monkeypatch.setattr(corpus, "run_guarded_repository", corpus.run_repository)


def test_100_repositories_export_all_rows_including_failure(monkeypatch, tmp_path):
    source = tmp_path / "repos.txt"
    source.write_text("".join(f"https://github.com/a/repo{i:03d}\n" for i in range(100)))
    rules = ROOT / "configs/heuristics"

    def fake(url, snapshot, ref, max_bytes):
        if url.endswith("repo099"):
            raise OSError("unavailable")
        shutil.copytree(ROOT / "tests/fixtures/snapshots/docs-positive", snapshot)
        manifest = read_json(snapshot / "manifest.json")
        manifest.update(repository=url.removeprefix("https://github.com/"), source_url=url)
        write_json(snapshot / "manifest.json", manifest)
        return manifest

    monkeypatch.setattr(corpus, "acquire_git", fake)
    output = tmp_path / "run"
    result = corpus.run_corpus(
        source, output, transport="git", workers=2, rules_dir=rules, expected_repositories=100
    )
    assert result["finished"] == 100
    assert result["failed"] == 1
    assert result["all_repositories_accounted_for"]
    log = (output / "progress.log").read_text()
    assert "[100/100]" in log
    assert log.count("  documentation-only:") == 100
    assert log.count("  code-only:") == 100
    assert "? | ? | ? | ? | ? | ?" in log
    assert corpus.export_tables(output)["repositories"] == 100
    rows = list(csv.DictReader((output / "predictions.csv").open()))
    assert len(rows) == 1800
    assert len({r["repository"] for r in rows}) == 100
    failed = [r for r in rows if r["repository"] == "a/repo099"]
    assert len(failed) == 18 and all(r["prediction"] == "" for r in failed)
    checkpoint = next(
        p for p in (output / "repositories").glob("*/result.json") if read_json(p)["modes"]
    )
    assert read_json(checkpoint)["modes"][0]["rule_catalog_hash"] == load_rules(rules)[1]
    with pytest.raises(ValueError, match="unchanged"):
        corpus.run_corpus(source, output, transport="git", workers=2, max_bytes=1)


def test_expected_count_fails_before_acquisition(tmp_path):
    source = tmp_path / "repos.txt"
    source.write_text("https://github.com/a/b\n")
    with pytest.raises(ValueError, match="Expected 100"):
        corpus.run_corpus(source, tmp_path / "run", transport="git", expected_repositories=100)
    assert not (tmp_path / "run").exists()


def test_raw_waits_for_retry_after_without_token(monkeypatch):
    data = b"research source"
    blob = hashlib.sha1(b"blob 15\0" + data).hexdigest()
    calls = []
    sleeps = []

    def fake(request, timeout):
        calls.append(request)
        if len(calls) == 1:
            raise HTTPError(request.full_url, 429, "throttled", {"Retry-After": "121"}, None)
        return io.BytesIO(data)

    monkeypatch.setenv("GITHUB_TOKEN", "must-not-be-sent")
    monkeypatch.setattr(acquisition, "urlopen", fake)
    monkeypatch.setattr(acquisition.time, "sleep", sleeps.append)
    assert acquisition.raw_get("a/b", "a" * 40, "README.md", blob, 100) == data
    assert sleeps == [60, 60, 1]
    assert not any(r.has_header("Authorization") for r in calls)


def test_benchmark_list_matches_all_final_labels():
    from lifecycle_mapper.reference import final_reference

    labels = final_reference(ROOT / "results/benchmark-100/workbook/final_agreement.csv")
    records = corpus.selected_records(ROOT / "data/corpus/benchmark_100.txt", None, "unused", 0, 1)
    assert len(records) == len(labels) == 100
    assert {r["url"].removeprefix("https://github.com/").casefold() for r in records} == set(labels)


def test_logging_preserves_mode_and_unknown_values():
    totals = {"finished": 1, "repository_count": 100, "complete": 0, "partial": 1, "failed": 0}
    predictions = dict(zip(corpus.STAGES, [True, False, None, False, True, None]))
    result = {
        "requested_url": "https://github.com/a/b",
        "complete": False,
        "modes": [
            {"mode": "documentation-only", "predictions": predictions, "scan_complete": False}
        ],
        "checkpoint_reused": True,
    }
    block = corpus.repository_log(result, totals, corpus.MODES)
    assert "documentation-only: 1 | 0 | ? | 0 | 1 | ?" in block
    assert "code-only: ? | ? | ? | ? | ? | ?" in block
    assert "combined: ? | ? | ? | ? | ? | ?" in block
    assert "cached checkpoint" in block
    assert "scan incomplete" in block
    agreement = dict(zip(corpus.STAGES, [1, 0, 1, 0, 1, 0]))
    before = repr(result)
    annotated = corpus.repository_log(result, totals, corpus.MODES, agreement)
    assert "author agreement (final_agreement): 1 | 0 | 1 | 0 | 1 | 0" in annotated
    assert repr(result) == before
    assert "documentation-only: 1 | 0 | ? | 0 | 1 | ?" in annotated


def test_failure_location_does_not_expose_local_paths(monkeypatch, tmp_path):
    def fail(*args):
        raise FileNotFoundError(2, "missing", "/private-test/missing")

    monkeypatch.setattr(corpus, "acquire_git", fail)
    source = tmp_path / "repos.txt"
    source.write_text("https://github.com/a/b\n")
    output = tmp_path / "run"
    corpus.run_corpus(source, output, transport="git", workers=1)
    path = next((output / "repositories").glob("*/result.json"))
    result = read_json(path)
    assert result["error_filename"] == "missing"
    assert result["error_location"][-1]["function"] == "fail"
    assert "private-person" not in path.read_text()
