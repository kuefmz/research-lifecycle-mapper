import gzip
import hashlib
import io
import json
import shutil
import tarfile
from pathlib import Path

import pytest

from lifecycle_mapper import acquisition
from lifecycle_mapper.canonical import write_json
from lifecycle_mapper.corpus import export_tables, run_corpus, selected_records
from lifecycle_mapper.openaire import extract, normalize_github

BASE = Path(__file__).resolve().parents[1] / "benchmark/synthetic/snapshots"


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/Owner/Repo.git",
        "git@github.com:Owner/Repo.git",
        "https://github.com/Owner/Repo/tree/main",
        "git+https://github.com/Owner/Repo",
    ],
)
def test_normalizes_repository_references(url):
    assert normalize_github(url) == "https://github.com/owner/repo"


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com.evil.test/a/b",
        "https://github.com/topics/python",
        "https://github.com/a/..",
        "https://github.com/a/b/unknown/path",
        "https://github.com/a",
        "https://token@github.com/a/b",
        "https://github.com:444/a/b",
        "https://github.com/a%2fb/c",
    ],
)
def test_rejects_nonrepository_references(url):
    assert normalize_github(url) is None


def test_streams_archive_deduplicates_and_preserves_provenance(tmp_path):
    source = tmp_path / "software.tar"
    records = [
        {"id": "1", "codeRepositoryUrl": "https://github.com/A/B.git"},
        {
            "id": "2",
            "codeRepositoryUrl": [
                "https://github.com/a/b/tree/main",
                "https://github.com/A/B",
                "https://example.org/a/b",
            ],
        },
        {"id": "3", "description": "https://github.com/ignored/repo"},
    ]
    raw = gzip.compress("".join(json.dumps(r) + "\n" for r in records).encode())
    with tarfile.open(source, "w") as archive:
        item = tarfile.TarInfo("../../outside.json.gz")
        item.size = len(raw)
        archive.addfile(item, io.BytesIO(raw))
    output = tmp_path / "extracted"
    summary = extract(source, output, "https://zenodo.org/records/ACTUAL_RELEASE")
    assert summary["counts"]["software_records"] == 3
    assert summary["counts"]["unique_github_repositories"] == 1
    assert summary["counts"]["github_record_links"] == 2
    assert (output / "repositories.txt").read_text() == "https://github.com/a/b\n"
    assert not (tmp_path / "outside.json.gz").exists()
    with pytest.raises(FileExistsError):
        extract(source, output, "same")


def test_raw_pinned_hash_verified_token_never_sent(monkeypatch):
    data = b"We collect research data.\n"
    digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    requests = []

    class Response(io.BytesIO):
        pass

    def fake(request, timeout):
        requests.append(request)
        return Response(data)

    monkeypatch.setenv("GITHUB_TOKEN", "never-send-this-to-raw")
    monkeypatch.setattr(acquisition, "urlopen", fake)
    assert acquisition.raw_get("a/b", "a" * 40, "docs/a b.md", digest, 100) == data
    assert "a" * 40 in requests[0].full_url
    assert "a%20b.md" in requests[0].full_url
    assert not requests[0].has_header("Authorization")
    with pytest.raises(ValueError, match="checksum"):
        acquisition.raw_get("a/b", "a" * 40, "x", "b" * 40, 100)
    with pytest.raises(ValueError, match="size"):
        acquisition.raw_get("a/b", "a" * 40, "x", digest, 2)


def test_hybrid_uses_api_only_for_metadata_and_tree(monkeypatch, tmp_path):
    data = b"We collect research data.\n"
    digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    calls = []

    def api(endpoint):
        calls.append(endpoint)
        if endpoint == "/repos/a/b/branches/main":
            return {
                "commit": {
                    "sha": "a" * 40,
                    "commit": {"tree": {"sha": "b" * 40}},
                    "html_url": "https://github.com/a/b/commit/" + "a" * 40,
                }
            }
        if "/git/trees/" in endpoint:
            return {
                "truncated": False,
                "tree": [
                    {
                        "path": "README.md",
                        "type": "blob",
                        "mode": "100644",
                        "sha": digest,
                        "size": len(data),
                    }
                ],
            }
        pytest.fail("Hybrid downloaded a blob with the REST API")

    monkeypatch.setattr(acquisition, "raw_get", lambda *args: data)
    snapshot = tmp_path / "snapshot"
    manifest = acquisition.acquire(
        "https://github.com/a/b", snapshot, blob_transport="raw", api_client=api
    )
    assert len(calls) == 2
    assert manifest["transport"] == "github-api-raw"
    acquisition.replay(snapshot)


def test_resume_and_export_documentation_reference(monkeypatch, tmp_path):
    from lifecycle_mapper import corpus

    input_path = tmp_path / "repos.txt"
    input_path.write_text("https://github.com/synthetic/docs-positive\n")
    output = tmp_path / "run"
    calls = []

    def fake(url, snapshot, ref, max_bytes):
        calls.append(url)
        shutil.copytree(BASE / "docs-positive", snapshot)
        return json.loads((snapshot / "manifest.json").read_bytes())

    monkeypatch.setattr(corpus, "acquire_git", fake)
    first = run_corpus(input_path, output, transport="git", workers=1)
    second = run_corpus(input_path, output, transport="git", workers=1)
    assert first["complete"] == second["complete"] == 1
    assert len(calls) == 1
    reference = tmp_path / "reference.json"
    write_json(
        reference,
        {
            "kind": "lifecycle-benchmark-dataset",
            "schema_version": 1,
            "stages": list(corpus.STAGES),
            "runs": [],
            "repositories": [
                {
                    "repository": "synthetic/docs-positive",
                    "source_url": "https://github.com/synthetic/docs-positive",
                    "results": {},
                    "human_labels": {stage: 0 for stage in corpus.STAGES},
                }
            ],
        },
    )
    assert export_tables(output, reference)["repositories"] == 1
    assert "false-positive" in (output / "documentation_comparison.csv").read_text()
    with pytest.raises(ValueError, match="unchanged"):
        run_corpus(input_path, output, transport="git", workers=1, modes=("code-only",))


def test_shards_disjoint_and_pilot_deterministic(tmp_path):
    path = tmp_path / "repos.txt"
    path.write_text("".join(f"https://github.com/a/repo{i}\n" for i in range(20)))
    one = selected_records(path, None, "seed", 0, 2)
    two = selected_records(path, None, "seed", 1, 2)
    assert len(one) + len(two) == 20
    assert not {r["url"] for r in one} & {r["url"] for r in two}
    assert selected_records(path, 5, "seed", 0, 1) == selected_records(path, 5, "seed", 0, 1)


def test_code_additions_are_review_candidates_not_gold_errors(monkeypatch, tmp_path):
    from lifecycle_mapper import corpus

    input_path = tmp_path / "repos.txt"
    input_path.write_text("https://github.com/synthetic/code-positive\n")

    def fake(url, snapshot, ref, max_bytes):
        shutil.copytree(BASE / "code-positive", snapshot)
        return json.loads((snapshot / "manifest.json").read_bytes())

    monkeypatch.setattr(corpus, "acquire_git", fake)
    output = tmp_path / "run"
    run_corpus(input_path, output, transport="git", workers=1)
    export_tables(output)
    rows = (output / "additional_evidence_candidates.csv").read_text()
    assert "needs-human-review" in rows
    assert "false-positive" not in rows


def test_direct_head_resolution_and_documentation_only_download(monkeypatch, tmp_path):
    calls = []
    data = b"We collect research data.\n"

    def api(endpoint):
        calls.append(endpoint)
        if "/branches/main" in endpoint:
            return {
                "commit": {
                    "sha": "a" * 40,
                    "html_url": "https://github.com/renamed/repo/commit/" + "a" * 40,
                    "commit": {"tree": {"sha": "b" * 40}},
                }
            }
        assert endpoint.startswith("/repos/renamed/repo/git/trees/")
        return {
            "truncated": False,
            "tree": [
                {"path": path, "type": "blob", "mode": "100644", "sha": "c" * 40, "size": len(data)}
                for path in ["README.md", "src/main.py"]
            ],
        }

    raw_paths = []

    def raw(repo, commit, path, blob, max_bytes):
        raw_paths.append(path)
        return data

    monkeypatch.setattr(acquisition, "raw_get", raw)
    snapshot = tmp_path / "snapshot"
    manifest = acquisition.acquire(
        "https://github.com/old/repo",
        snapshot,
        blob_transport="raw",
        api_client=api,
        resolve_head_direct=True,
        sources=("documentation",),
    )
    assert len(calls) == 2
    assert raw_paths == ["README.md"]
    assert manifest["repository"] == "renamed/repo"
    assert manifest["files"][1]["reason"] == "source-not-requested"
    acquisition.replay(snapshot)


def test_api_pacing_respects_server_cooldown(monkeypatch):
    from lifecycle_mapper import corpus

    clock = [100.0]
    sleeps = []
    calls = []

    def sleep(delay):
        sleeps.append(delay)
        clock[0] += delay

    def fake(endpoint, **kwargs):
        calls.append(endpoint)
        if len(calls) == 1:
            raise acquisition.GitHubAPIError("rate-limit", 429, retry_after="7")
        return {"ok": True}

    monkeypatch.setattr(corpus.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(corpus.time, "sleep", sleep)
    monkeypatch.setattr(acquisition, "api_get", fake)
    assert corpus.PacedAPI()("/repos/a/b") == {"ok": True}
    assert sum(sleeps) >= 7


def test_failed_run_never_exports_six_negative_predictions(monkeypatch, tmp_path):
    from lifecycle_mapper import corpus

    def fail(*args):
        raise OSError("offline")

    monkeypatch.setattr(corpus, "acquire_git", fail)
    source = tmp_path / "repos.txt"
    source.write_text("https://github.com/a/b\n")
    output = tmp_path / "run"
    summary = run_corpus(source, output, transport="git", workers=1)
    assert summary["failed"] == 1
    export_tables(output)
    assert len((output / "predictions.csv").read_text().splitlines()) == 1


@pytest.mark.parametrize(
    "name",
    [
        "docs-positive",
        "code-positive",
        "excluded-negative",
        "generic-negative",
        "incomplete",
    ],
)
def test_single_pass_modes_identical_to_independent_analysis(name):
    from lifecycle_mapper.analysis import analyze, analyze_modes
    from lifecycle_mapper import MODES

    snapshot = BASE / name
    assert analyze_modes(snapshot, MODES) == [analyze(snapshot, mode) for mode in MODES]


def test_independent_import_computes_count_without_historical_constant(tmp_path):
    import csv
    from lifecycle_mapper.annotations import FIELDS, import_annotations
    from lifecycle_mapper import STAGES

    source = tmp_path / "independent.csv"
    with source.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(
            {
                "repository": "a/b",
                "stage": stage,
                "reviewer2": "1",
                "reviewer1": "0" if i == 0 else "1",
                "proposed_consensus": "",
                "approved_consensus": "",
                "approval_reference": "",
            }
            for i, stage in enumerate(STAGES)
        )
    provenance = import_annotations(
        source, tmp_path / "imported", "current", expected_repositories=1
    )
    assert provenance["initial_disagreements"] == 1
