"""Artificial captured-input fixtures for final-method regression tests."""

from pathlib import Path
from lifecycle_mapper.acquisition import replay, POLICY_VERSION
from lifecycle_mapper.canonical import sha256, write_json, read_json

BASE = Path(__file__).resolve().parent / "fixtures/snapshots"


def make_snapshot(tmp_path, text, path="src/activity.py"):
    manifest, _ = replay(BASE / "code-positive")
    source = "documentation" if path.endswith(".md") else "code"
    manifest["files"] = [
        {
            "path": path,
            "size": len(text.encode()),
            "source": source,
            "mode": "100644",
            "git_blob_sha": None,
            "status": "captured",
            "reason": None,
            "sha256": sha256(text.encode()),
        }
    ]
    target = tmp_path / "content" / path
    target.parent.mkdir(parents=True)
    target.write_text(text)
    write_json(tmp_path / "manifest.json", manifest)
    return tmp_path


def portable_snapshot(tmp_path, text, path):
    snapshot = make_snapshot(tmp_path, text, path)
    manifest = read_json(snapshot / "manifest.json")
    manifest["policy_version"] = POLICY_VERSION
    write_json(snapshot / "manifest.json", manifest)
    return snapshot
