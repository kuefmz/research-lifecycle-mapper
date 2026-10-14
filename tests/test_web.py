import json
import threading
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from lifecycle_mapper.web import Application, make_server
from test_batch import fake_acquisition

ROOT = Path(__file__).resolve().parents[1]


def wait_job(app, job_id):
    for _ in range(100):
        job = app.job(job_id)
        if job["status"] in {"completed", "failed"}:
            return job
        time.sleep(0.02)
    pytest.fail("Background job did not finish")


def test_live_ui_job_download_and_history_after_restart(tmp_path, monkeypatch):
    from lifecycle_mapper import batch

    monkeypatch.setattr(batch, "acquire", fake_acquisition)
    app = Application(ROOT, tmp_path / "ui")
    server = make_server(app, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base) as response:
            assert b"Run the benchmark" in response.read()
        payload = json.dumps(
            {
                "kind": "repository",
                "url": "https://github.com/synthetic/docs-positive",
                "mode": "all",
            }
        ).encode()
        request = Request(
            base + "/api/jobs", data=payload, headers={"Content-Type": "application/json"}
        )
        with urlopen(request) as response:
            job_id = json.load(response)["id"]
        job = wait_job(app, job_id)
        assert job["status"] == "completed"
        assert job["result"]["analyzed_count"] == 1
        with urlopen(base + f"/api/download/{job_id}/predictions.csv") as response:
            assert b"documentation-only" in response.read()
        restored = Application(ROOT, tmp_path / "ui")
        assert restored.job(job_id)["result"] == job["result"]
        assert restored.history()[0]["id"] == job_id
        restored.pool.shutdown()
    finally:
        server.shutdown()
        server.server_close()
        app.pool.shutdown()


def test_ui_invalid_input_and_cross_origin_rejected(tmp_path):
    app = Application(ROOT, tmp_path / "ui")
    with pytest.raises(ValueError):
        app.start({"url": "https://example.invalid/repository"})
    with pytest.raises(ValueError):
        app.start({"kind": "evaluation", "config": "../outside.json"})
    server = make_server(app, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/jobs",
            data=b"{}",
            headers={"Content-Type": "application/json", "Origin": "https://unrelated.invalid"},
        )
        with pytest.raises(HTTPError) as exc:
            urlopen(request)
        assert exc.value.code == 400
    finally:
        server.shutdown()
        server.server_close()
        app.pool.shutdown()


def test_pending_gold_does_not_block_predictions_but_blocks_evaluation(tmp_path):
    app = Application(ROOT, tmp_path / "ui")
    try:
        job_id = app.start({"kind": "evaluation", "config": "configs/benchmark.yaml"})["id"]
        job = wait_job(app, job_id)
        assert job["status"] == "failed" and "pending" in job["error"]
    finally:
        app.pool.shutdown()
