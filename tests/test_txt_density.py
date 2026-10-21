import base64

import pytest

from lifecycle_mapper.acquisition import (
    POLICY_VERSION,
    acquire,
    replay,
    source_kind,
    txt_folder_counts,
)
from lifecycle_mapper.canonical import write_json


@pytest.mark.parametrize("count,excluded", [(5, False), (6, True)])
def test_immediate_folder_threshold_and_old_policy(count, excluded):
    paths = [f"data/{i}.TXT" for i in range(count)] + [
        "data/nested/one.txt",
        "docs/readme.txt",
        "README.md",
    ]
    counts = txt_folder_counts(paths)
    assert (source_kind(paths[0], txt_counts=counts)[0] is None) == excluded
    assert source_kind("data/nested/one.txt", txt_counts=counts)[0] == "documentation"
    assert source_kind("docs/readme.txt", txt_counts=counts)[0] == "documentation"
    assert source_kind("README.md", txt_counts=counts)[0] == "documentation"
    assert source_kind(paths[0], "eligibility-3-programming-catalog", counts)[0] == "documentation"


@pytest.mark.parametrize("transport", ["api", "raw"])
def test_dense_txt_not_downloaded_and_replay_is_contextual(tmp_path, monkeypatch, transport):
    from lifecycle_mapper import acquisition

    content = b"Example documentation.\n"
    commit = "a" * 40
    files = [
        {
            "path": f"data/{i}.txt",
            "type": "blob",
            "mode": "100644",
            "sha": str(i) * 40,
            "size": 1000000,
        }
        for i in range(6)
    ]
    files.append(
        {
            "path": "README.md",
            "type": "blob",
            "mode": "100644",
            "sha": "b" * 40,
            "size": len(content),
        }
    )
    downloads = []

    def api(endpoint):
        if "/branches/main" in endpoint:
            return {
                "commit": {
                    "sha": commit,
                    "commit": {"tree": {"sha": "c" * 40}},
                    "html_url": "https://github.com/a/b/commit/" + commit,
                }
            }
        if "/git/trees/" in endpoint:
            return {"tree": files, "truncated": False}
        downloads.append(endpoint)
        assert endpoint.endswith("b" * 40)
        return {"encoding": "base64", "content": base64.b64encode(content).decode()}

    def raw(repo, sha, path, blob, cap):
        downloads.append(path)
        assert path == "README.md"
        return content

    monkeypatch.setattr(acquisition, "raw_get", raw)
    snapshot = tmp_path / "snapshot"
    manifest = acquire("https://github.com/a/b", snapshot, api_client=api, blob_transport=transport)
    assert len(downloads) == 1
    assert manifest["policy_version"] == POLICY_VERSION
    skipped = [f for f in manifest["files"] if f["path"].endswith(".txt")]
    assert len(skipped) == 6
    assert all(
        f["source"] is None
        and f["status"] == "excluded"
        and f["reason"] == "txt-folder-more-than-5"
        for f in skipped
    )
    _, contents = replay(snapshot)
    assert set(contents) == {"README.md"}
    manifest["files"][1]["source"] = "documentation"
    write_json(snapshot / "manifest.json", manifest)
    with pytest.raises(ValueError, match="Invalid inventory source/status"):
        replay(snapshot)
