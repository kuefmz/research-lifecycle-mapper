import json
import shutil
from pathlib import Path

import pytest

from lifecycle_mapper.acquisition import acquire, replay, repository_id, source_kind
from lifecycle_mapper.canonical import contained, write_json

BASE = Path(__file__).resolve().parents[1] / "benchmark/synthetic/snapshots"


@pytest.mark.parametrize(
    "value",
    [
        "http://github.com/a/b",
        "https://evil.invalid/a/b",
        "https://github.com/a/b/tree/main",
        "https://github.com/a/..",
    ],
)
def test_invalid_repository_urls(value):
    with pytest.raises(ValueError):
        repository_id(value)


def test_repository_url_and_eligibility():
    assert repository_id("https://github.com/Owner/Repo.git") == "Owner/Repo"
    assert source_kind("vendor/research.py")[0] is None
    assert source_kind("README.md")[0] == "documentation"
    assert source_kind("src/README.md")[0] == "documentation"
    assert source_kind("requirements.txt")[0] == "documentation"  # No rule fires from dependencies.
    assert source_kind("notebook.ipynb")[0] is None


def test_replay_hashes_and_inventory(tmp_path):
    shutil.copytree(BASE / "docs-positive", tmp_path / "snapshot")
    snapshot = tmp_path / "snapshot"
    with pytest.raises(ValueError, match="manifest checksum"):
        replay(snapshot, "0" * 64)
    (snapshot / "content/README.md").write_text("tampered")
    with pytest.raises(ValueError, match="integrity"):
        replay(snapshot)


def test_replay_rejects_unsorted_duplicate_paths(tmp_path):
    shutil.copytree(BASE / "docs-positive", tmp_path / "snapshot")
    snapshot = tmp_path / "snapshot"
    data = json.loads((snapshot / "manifest.json").read_bytes())
    data["files"] *= 2
    write_json(snapshot / "manifest.json", data)
    with pytest.raises(ValueError, match="unique and sorted"):
        replay(snapshot)


def test_traversal_and_symlink_rejection(tmp_path):
    with pytest.raises(ValueError, match="Unsafe"):
        contained(tmp_path, "../elsewhere")
    (tmp_path / "escape").symlink_to(tmp_path.parent)
    with pytest.raises(ValueError, match="escapes"):
        contained(tmp_path, "escape/secret")


def test_live_resolves_commit_and_captures_errors(monkeypatch, tmp_path):
    from lifecycle_mapper import acquisition
    import base64

    calls = []
    immutable = "a" * 40
    content = b"We collect raw research data.\n"

    def fake(endpoint):
        calls.append(endpoint)
        if endpoint == "/repos/owner/repo/branches/main":
            return {
                "commit": {
                    "sha": immutable,
                    "commit": {"tree": {"sha": "b" * 40}},
                    "html_url": "https://github.com/Owner/Repo/commit/" + immutable,
                }
            }
        if "/git/trees/" in endpoint:
            return {
                "tree": [
                    {
                        "path": "README.md",
                        "sha": "c" * 40,
                        "type": "blob",
                        "mode": "100644",
                        "size": len(content),
                    },
                    {
                        "path": "src.py",
                        "sha": "d" * 40,
                        "type": "blob",
                        "mode": "100644",
                        "size": 10,
                    },
                ],
                "truncated": False,
            }
        if endpoint.endswith("c" * 40):
            return {"content": base64.b64encode(content).decode(), "encoding": "base64"}
        raise OSError("simulated download failure")

    monkeypatch.setattr(acquisition, "api_get", fake)
    manifest = acquire("https://github.com/owner/repo", tmp_path / "snapshot")
    assert manifest["commit"] == immutable
    assert manifest["repository"] == "Owner/Repo"
    assert manifest["files"][1]["status"] == "unavailable"
    assert manifest["files"][1]["reason"] == "OSError"
    replay(tmp_path / "snapshot")
    monkeypatch.setattr(acquisition, "api_get", lambda _: pytest.fail("Replay used network"))
    replay(tmp_path / "snapshot")


def test_truncated_tree_aborts(monkeypatch, tmp_path):
    from lifecycle_mapper import acquisition

    def fake(endpoint):
        if "/branches/main" in endpoint:
            return {
                "commit": {
                    "sha": "a" * 40,
                    "commit": {"tree": {"sha": "b" * 40}},
                    "html_url": "https://github.com/owner/repo/commit/" + "a" * 40,
                }
            }
        return {"truncated": True}

    monkeypatch.setattr(acquisition, "api_get", fake)
    with pytest.raises(ValueError, match="Incomplete GitHub tree"):
        acquire("https://github.com/owner/repo", tmp_path / "snapshot")
    assert not (tmp_path / "snapshot").exists()
