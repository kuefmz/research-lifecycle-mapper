from pathlib import Path
from types import SimpleNamespace
import pytest
from lifecycle_mapper import acquisition
from lifecycle_mapper.git_acquisition import acquire_git
from lifecycle_mapper.reference import audit_workbook


def branch_payload():
    return {
        "commit": {
            "sha": "a" * 40,
            "commit": {"tree": {"sha": "b" * 40}},
            "html_url": "https://github.com/a/b/commit/" + "a" * 40,
        }
    }


@pytest.mark.parametrize("ref", ["master", "HEAD", "v1.0", "a" * 40, "develop"])
def test_refs_cannot_override_policy(monkeypatch, tmp_path, ref):
    monkeypatch.setattr(acquisition, "api_get", lambda _: pytest.fail("Unexpected network"))
    with pytest.raises(ValueError, match="no other ref"):
        acquisition.acquire("https://github.com/a/b", tmp_path / "snapshot", ref=ref)


def test_main_preferred_even_if_master_exists(tmp_path):
    calls = []

    def getter(endpoint):
        calls.append(endpoint)
        if endpoint.endswith("/branches/main"):
            return branch_payload()
        assert "/git/trees/" in endpoint
        return {"tree": [], "truncated": False}

    m = acquisition.acquire("https://github.com/a/b", tmp_path / "s", api_client=getter)
    assert m["selected_branch"] == "main"
    assert m["branch_policy"] == "main-then-master-v1"
    assert len(calls) == 2 and not any("master" in c for c in calls)


def test_master_used_only_when_main_missing(tmp_path):
    calls = []

    def getter(endpoint):
        calls.append(endpoint)
        if endpoint.endswith("/branches/main"):
            raise acquisition.GitHubAPIError("not-found-or-inaccessible", 404)
        if endpoint.endswith("/branches/master"):
            return branch_payload()
        assert "/git/trees/" in endpoint
        return {"tree": [], "truncated": False}

    m = acquisition.acquire("https://github.com/a/b", tmp_path / "s", api_client=getter)
    assert m["selected_branch"] == "master" and len(calls) == 3
    assert m["commit"] == "a" * 40


def test_missing_both_never_uses_other_branches_or_tags(tmp_path):
    calls = []

    def getter(endpoint):
        calls.append(endpoint)
        raise acquisition.GitHubAPIError("not-found-or-inaccessible", 404)

    with pytest.raises(acquisition.GitHubAPIError, match="main-and-master"):
        acquisition.acquire("https://github.com/a/b", tmp_path / "s", api_client=getter)
    assert calls == ["/repos/a/b/branches/main", "/repos/a/b/branches/master"]
    assert not (tmp_path / "s").exists()


def test_rate_limit_does_not_trigger_master_fallback(tmp_path):
    calls = []

    def getter(endpoint):
        calls.append(endpoint)
        raise acquisition.GitHubAPIError("rate-limit", 403)

    with pytest.raises(acquisition.GitHubAPIError, match="rate-limit"):
        acquisition.acquire("https://github.com/a/b", tmp_path / "s", api_client=getter)
    assert len(calls) == 1


def test_git_uses_only_verified_remote_branch(monkeypatch, tmp_path):
    import lifecycle_mapper.git_acquisition as module

    calls = []

    def run(args, **kwargs):
        calls.append(args)
        if "ls-remote" in args:
            return SimpleNamespace(stdout=("a" * 40 + "\trefs/heads/master\n").encode())
        if "clone" in args:
            assert "--branch=master" in args and "--single-branch" in args
            return SimpleNamespace(stdout=b"")
        if "rev-parse" in args:
            return SimpleNamespace(
                stdout=(("b" * 40 if args[-1].endswith("^{tree}") else "a" * 40) + "\n").encode()
            )
        assert "ls-tree" in args
        return SimpleNamespace(stdout=b"")

    monkeypatch.setattr(module.subprocess, "run", run)
    m = acquire_git("https://github.com/a/b", tmp_path / "s")
    assert m["selected_branch"] == "master"
    assert any("refs/remotes/origin/master" in a for a in calls)


def test_corrected_workbook_has_complete_anonymous_reviewers():
    p = Path(__file__).resolve().parents[1] / "data/research_lifecycle_benchmark_100_msr27.xlsx"
    a = audit_workbook(p, ("reviewer1", "reviewer2"))
    assert (a["valid_pairs"], a["agreements"], a["binary_disagreements"]) == (600, 354, 246)
    assert not a["missing_annotation_pairs"]
