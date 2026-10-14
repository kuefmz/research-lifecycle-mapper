"""Real browser flow, enabled explicitly in CI; no GitHub network or human data."""

import json
import os
import shutil
import threading
from pathlib import Path

import pytest

from lifecycle_mapper.web import Application, make_server

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(
    os.environ.get("RLM_BROWSER_TEST") != "1", reason="Enable browser tests with RLM_BROWSER_TEST=1"
)


@pytest.fixture
def ui(tmp_path, monkeypatch):
    from lifecycle_mapper import batch

    def acquire(url, output, ref=None, max_bytes=250000):
        shutil.copytree(ROOT / "benchmark/synthetic/snapshots/docs-positive", output)
        return json.loads((output / "manifest.json").read_bytes())

    monkeypatch.setattr(batch, "acquire", acquire)
    app = Application(ROOT, tmp_path / "ui")
    server = make_server(app, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", tmp_path
    server.shutdown()
    server.server_close()
    app.pool.shutdown()


def test_repository_benchmark_replay_and_history_in_browser(ui):
    from playwright.sync_api import sync_playwright

    url, tmp_path = ui
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 960})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url)
        page.screenshot(path=str(tmp_path / "ui-home.png"))
        page.locator("#repo-url").fill("https://github.com/synthetic/docs-positive")
        page.locator("#repo-mode").select_option("all")
        page.get_by_role("button", name="Analyze repository", exact=True).click()
        page.locator("#results").wait_for(state="visible")
        assert page.locator("tr[data-repo]").count() == 3
        assert page.locator(".evidence").count() > 0
        page.get_by_role("button", name="Run the benchmark", exact=True).click()
        page.locator("#batch-file").set_input_files(
            {
                "name": "benchmark.csv",
                "mimeType": "text/csv",
                "buffer": b"repository_url\nhttps://github.com/synthetic/docs-positive\n",
            }
        )
        page.get_by_role("status").filter(has_text="File ready").wait_for()
        page.get_by_role("button", name="Run benchmark heuristics", exact=True).click()
        page.locator("#results").wait_for(state="visible")
        page.get_by_role("button", name="Replay captured inputs").click()
        page.locator("#results").wait_for(state="visible")
        page.get_by_role("button", name="Previous runs", exact=True).click()
        page.locator(".history-item").first.wait_for()
        assert page.locator(".history-item").count() == 3
        assert not errors
        browser.close()


def test_mobile_form_has_no_horizontal_overflow(ui):
    from playwright.sync_api import sync_playwright

    url, tmp_path = ui
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(url)
        page.screenshot(path=str(tmp_path / "ui-mobile.png"))
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.get_by_role("button", name="Run the benchmark", exact=True).click()
        assert page.locator("#batch-urls").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        browser.close()
