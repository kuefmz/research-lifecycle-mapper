import io
import shutil
import sys
import time
from pathlib import Path

from lifecycle_mapper import corpus, execution
from lifecycle_mapper.acquisition import raw_get
from lifecycle_mapper.canonical import json_bytes, read_json, sha256, write_json

ROOT = Path(__file__).resolve().parents[1]


def test_hard_deadline_terminates_busy_process_and_records_observed_diagnostics(tmp_path):
    # A CPU-bound loop cannot be cancelled by a thread Future timeout.
    script = (
        "import json;from pathlib import Path;"
        f"Path({str(tmp_path / 'heartbeat.json')!r}).write_text(json.dumps("
        "{'phase':'analysis','files_attempted':900,'eligible_files':901,"
        "'captured_bytes':30000000,'current_file':'large.py'}));"
        "exec('while True: pass')"
    )
    started = time.monotonic()
    outcome = execution.worker_process([sys.executable, "-c", script], tmp_path, timeout=0.4)
    assert outcome["timed_out"] and outcome["worker_exit_code"] != 0
    assert time.monotonic() - started < 3
    assert outcome["diagnostics"]["phase"] == "analysis"
    assert outcome["diagnostics"]["files_attempted"] == 900


def test_guarded_repository_runs_real_child_and_reads_finished_checkpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("PYTHONPATH", str(ROOT / "src"))
    record = {"url": "https://github.com/synthetic/docs-positive", "ref": "main"}
    key = sha256(json_bytes([record["url"].casefold(), "main-then-master-v1"]))
    directory = tmp_path / "repositories" / key
    snapshot = directory / "attempt-0001/snapshot"
    shutil.copytree(ROOT / "tests/fixtures/snapshots/docs-positive", snapshot)
    manifest = read_json(snapshot / "manifest.json")
    manifest["branch_policy"] = "main-then-master-v1"
    write_json(snapshot / "manifest.json", manifest)
    result = execution.run_guarded_repository(
        record, tmp_path, corpus.MODES, "git", 0, corpus.PacedAPI(), False
    )
    assert result["complete"]
    assert len(result["modes"]) == 3
    assert read_json(directory / "heartbeat.json")["phase"] == "writing-result"
    assert not (directory / "worker-job.json").exists()
    cached = execution.run_guarded_repository(
        record, tmp_path, corpus.MODES, "git", 0, corpus.PacedAPI(), False
    )
    assert cached["checkpoint_reused"]


def test_timeout_checkpoint_exports_unknown_not_false_and_cleans_job(monkeypatch, tmp_path):
    actual = execution.worker_process

    def slow(command, directory, timeout):
        script = "import time; time.sleep(10)"
        return actual([sys.executable, "-c", script], directory, timeout=0.1)

    monkeypatch.setattr(execution, "worker_process", slow)
    record = {"url": "https://github.com/a/b", "ref": "main"}
    result = execution.run_guarded_repository(
        record, tmp_path, corpus.MODES, "hybrid", 0, corpus.PacedAPI(), False
    )
    assert result["error"] == "repository-timeout"
    assert result["timeout_seconds"] == 120
    assert result["modes"] == []
    assert len(list(tmp_path.glob("repositories/*/stop.json"))) == 1
    assert not list(tmp_path.glob("repositories/*/worker-job.json"))
    write_json(tmp_path / "manifest.json", {"configuration": {"modes": list(corpus.MODES)}})
    corpus.export_tables(tmp_path)
    import csv

    rows = list(csv.DictReader((tmp_path / "predictions.csv").open()))
    assert len(rows) == 18 and all(row["prediction"] == "" for row in rows)
    assert "repository-timeout" in (tmp_path / "repository_status.csv").read_text()


def test_direct_download_no_size_cap(monkeypatch):
    import hashlib
    from lifecycle_mapper import acquisition

    data = b"x" * 2_100_000
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    monkeypatch.setattr(acquisition, "urlopen", lambda *args, **kwargs: io.BytesIO(data))
    assert raw_get("a/b", "a" * 40, "README.md", blob, 0) == data


def test_acquisition_does_not_exclude_large_file_by_default(monkeypatch, tmp_path):
    from lifecycle_mapper import acquisition

    data = b"z" * 2_100_000

    def api(endpoint):
        if "/branches/" in endpoint:
            return {
                "commit": {
                    "sha": "a" * 40,
                    "html_url": "https://github.com/a/b/commit/" + "a" * 40,
                    "commit": {"tree": {"sha": "b" * 40}},
                }
            }
        return {
            "truncated": False,
            "tree": [
                {
                    "path": "README.md",
                    "type": "blob",
                    "mode": "100644",
                    "sha": "c" * 40,
                    "size": len(data),
                }
            ],
        }

    def raw(repo, commit, path, blob, limit):
        assert limit == 0
        return data

    monkeypatch.setattr(acquisition, "raw_get", raw)
    manifest = acquisition.acquire(
        "https://github.com/a/b", tmp_path / "snapshot", blob_transport="raw", api_client=api
    )
    assert manifest["max_bytes"] == 0
    assert manifest["files"][0]["status"] == "captured"


def test_deadline_kills_child_process_group(tmp_path):
    import os
    import pytest

    if os.name != "posix":
        pytest.skip("POSIX process-group guarantee")
    marker = tmp_path / "child-survived"
    child = f"import time;from pathlib import Path;time.sleep(1);Path({str(marker)!r}).touch()"
    script = f"import subprocess,sys,time;subprocess.Popen([sys.executable,'-c',{child!r}]);time.sleep(10)"
    outcome = execution.worker_process([sys.executable, "-c", script], tmp_path, timeout=0.3)
    assert outcome["timed_out"]
    time.sleep(1.1)
    assert not marker.exists()
