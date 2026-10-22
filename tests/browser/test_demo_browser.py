"""Browser smoke test for the advertised minimal UI, using a captured-result stub."""

import json
import os
import subprocess
import threading
from pathlib import Path

import pytest

from lifecycle_mapper import STAGES
from lifecycle_mapper.demo import Demo, make_server

pytestmark = pytest.mark.skipif(
    os.environ.get("RLM_BROWSER_TEST") != "1", reason="Enable with RLM_BROWSER_TEST=1"
)


def test_minimal_url_to_evidence_flow(tmp_path, monkeypatch):
    from playwright.sync_api import sync_playwright

    def run(command, **kwargs):
        output = Path(command[command.index("--output") + 1])
        directory = output / "repositories" / "hash"
        directory.mkdir(parents=True)
        result = {
            "requested_url": "https://github.com/example/research",
            "commit": "a" * 40,
            "modes": [
                {
                    "mode": mode,
                    "predictions": dict.fromkeys(STAGES, 1),
                    "evidence": [{"path": "README.md", "excerpt": "<script>unsafe</script>"}],
                }
                for mode in ["documentation-only", "code-only", "combined"]
            ],
        }
        (directory / "result.json").write_text(json.dumps(result))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("lifecycle_mapper.demo.subprocess.run", run)
    server = make_server(Demo(tmp_path), 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{server.server_port}")
            page.get_by_label("GitHub repository URL").fill("https://github.com/example/research")
            page.get_by_role("button", name="Analyze").click()
            page.get_by_role("link", name="Download result JSON").wait_for()
            assert page.locator("table tr").count() == 4
            assert page.locator("table td").count() == 21
            page.get_by_text("Evidence and full result", exact=True).click()
            assert "<script>unsafe</script>" in page.locator("pre").inner_text()
            assert page.locator("#result script").count() == 0
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
