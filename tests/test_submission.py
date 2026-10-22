"""Final default equivalence, cohort subtraction, and local demo integration."""

import importlib.util
import json
import subprocess
import sys
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from lifecycle_mapper import analysis
from lifecycle_mapper.demo import Demo, make_server

ROOT = Path(__file__).resolve().parents[1]


def test_final_default_is_exact_frozen_profile():
    expected, digest = analysis.load_rules(ROOT / "configs/heuristics")
    actual, default_digest = analysis.load_rules()
    assert len(actual) == 105
    assert actual == expected and digest == default_digest
    for name in ["docs-positive", "code-positive", "generic-negative", "excluded-negative"]:
        snapshot = ROOT / "benchmark/synthetic/snapshots" / name
        for mode in ["documentation-only", "code-only", "combined"]:
            assert analysis.analyze(snapshot, mode) == analysis.analyze(
                snapshot, mode, rules_dir=ROOT / "configs/heuristics"
            )
    subprocess.run([sys.executable, "scripts/verify_final_profile.py"], cwd=ROOT, check=True)


def test_ordered_subtraction_preserves_identity_and_audit(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "selection", ROOT / "scripts/select_repositories.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source, old = tmp_path / "input.txt", tmp_path / "old.txt"
    source.write_text(
        "https://github.com/A/B/tree/main\nhttps://github.com/c/d\nhttps://github.com/a/b\n"
    )
    old.write_text("https://github.com/a/b.git\n")
    output = tmp_path / "remaining.txt"
    result = module.select(source, old, output)
    assert result["candidate_unique"] == 2 and result["overlap_excluded"] == 1
    assert output.read_text() == "https://github.com/c/d\n"
    assert output.with_suffix(".normalization.csv").exists()


def test_demo_uses_guarded_corpus_runner_and_renders_json(tmp_path, monkeypatch):
    seen = []

    def run(command, **kwargs):
        seen.append(command)
        output = Path(command[command.index("--output") + 1])
        directory = output / "repositories" / "hash"
        directory.mkdir(parents=True)
        (directory / "result.json").write_text(
            json.dumps({"requested_url": "https://github.com/a/b", "modes": []})
        )
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("lifecycle_mapper.demo.subprocess.run", run)
    app = Demo(tmp_path)
    server = make_server(app, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert b"GitHub repository URL" in urlopen(base).read()
        request = Request(
            base + "/jobs",
            data=b'{"url":"https://github.com/a/b"}',
            headers={"Content-Type": "application/json"},
        )
        job = json.load(urlopen(request))["id"]
        # Join the actual short local worker without sleeps.
        for thread in threading.enumerate():
            if thread.name.endswith("(execute)"):
                thread.join(timeout=3)
        assert json.load(urlopen(base + "/jobs/" + job))["status"] == "finished"
        assert "--max-bytes" in seen[0] and "10485760" in seen[0]
        assert "lifecycle_mapper.corpus" in seen[0]
        bad = Request(
            base + "/jobs",
            data=b'{"url":"https://github.com/a/b"}',
            headers={"Origin": "https://example.org"},
        )
        try:
            urlopen(bad)
        except HTTPError as error:
            assert error.code == 403
        else:
            raise AssertionError("Cross-origin request accepted")
    finally:
        server.shutdown()
        server.server_close()
