import errno
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from lifecycle_mapper import telemetry


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch):
    monkeypatch.setattr(telemetry, "_path", None)
    monkeypatch.setattr(telemetry, "_state", {})


def test_parallel_updates_use_atomic_unique_files(tmp_path):
    target = tmp_path / "heartbeat.json"
    telemetry.configure(target)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda i: telemetry.emit(counter=i), range(100)))
    assert "counter" in json.loads(target.read_text())
    assert not list(tmp_path.glob(".heartbeat-*"))


def test_logging_file_not_found_is_nonfatal_and_diagnostic(monkeypatch, tmp_path):
    target = tmp_path / "nested/heartbeat.json"
    telemetry.configure(target)

    def fail(*args):
        raise FileNotFoundError(errno.ENOENT, "missing temporary file")

    monkeypatch.setattr(telemetry.os, "replace", fail)
    telemetry.emit(phase="acquisition", files_captured=34)
    state = telemetry.current_state()
    assert state["files_captured"] == 34
    assert state["telemetry_write_error"] == "FileNotFoundError"
    assert not list(target.parent.glob(".heartbeat-*"))
