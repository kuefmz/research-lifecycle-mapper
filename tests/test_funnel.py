import io
import json
import tarfile

import pytest

from lifecycle_mapper.canonical import write_json
from lifecycle_mapper.funnel import build_funnel
from lifecycle_mapper.openaire import extract, file_hash


def inputs(tmp_path):
    source = tmp_path / "software.tar"
    records = [
        {"id": "a", "description": "experiment", "codeRepositoryUrl": "https://github.com/a/one"},
        {"id": "b", "description": "ordinary", "codeRepositoryUrl": "https://github.com/a/two"},
        {"id": "c", "codeRepositoryUrl": "https://github.com/a/three"},
    ]
    raw = "".join(json.dumps(r) + "\n" for r in records).encode()
    with tarfile.open(source, "w") as archive:
        member = tarfile.TarInfo("software.jsonl")
        member.size = len(raw)
        archive.addfile(member, io.BytesIO(raw))
    full, filtered = tmp_path / "full", tmp_path / "filtered"
    extract(source, full, "release")
    extract(source, filtered, "release", True)
    legacy, benchmark = tmp_path / "legacy.txt", tmp_path / "benchmark.txt"
    legacy.write_text("https://github.com/A/one.git\nhttps://github.com/a/outside\n")
    benchmark.write_text("https://github.com/a/one\n")
    return full, filtered, legacy, benchmark


def test_funnel_sets_paper_evidence_and_checkpoints(tmp_path):
    full, filtered, legacy, benchmark = inputs(tmp_path)
    paper = tmp_path / "papers.csv"
    paper.write_text("repository_url,paper_identifier\nhttps://github.com/a/outside,doi:example\n")
    run = tmp_path / "run"
    checkpoint = run / "repositories/key"
    checkpoint.mkdir(parents=True)
    write_json(run / "manifest.json", {"configuration": {"repository_count": 2}})
    write_json(
        checkpoint / "result.json",
        {
            "requested_url": "https://github.com/a/one",
            "commit": "abc",
            "complete": True,
            "selected_branch": "master",
        },
    )
    (checkpoint / "result.sha256").write_text(file_hash(checkpoint / "result.json"))
    output = tmp_path / "funnel"
    report = build_funnel(full, filtered, legacy, benchmark, output, runs=(run,), paper_links=paper)
    counts = {row["stage"]: row["count"] for row in report["stages"]}
    assert counts["union"] == 2 and counts["intersection"] == 1
    assert counts["legacy_absent_current_dump"] == 1
    assert counts["records_missing_description"] == 1
    assert counts["descriptions_present_nonmatching"] == 1
    assert counts["union_with_supplied_paper_evidence"] == 1
    assert counts["run_1_pending"] == 1 and counts["run_1_master"] == 1
    assert (output / "union_repositories.csv").read_text().splitlines() == [
        "github_repository_url",
        "https://github.com/a/one",
        "https://github.com/a/outside",
    ]
    refreshed = build_funnel(full, filtered, legacy, benchmark, output)
    assert refreshed["paper_evidence_status"].startswith("Not supplied")
    assert "union_with_supplied_paper_evidence" not in {r["stage"] for r in refreshed["stages"]}


def test_funnel_rejects_changed_extraction_or_source(tmp_path):
    full, filtered, legacy, benchmark = inputs(tmp_path)
    summary_path = filtered / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["source_tar_sha256"] = "wrong"
    write_json(summary_path, summary)
    with pytest.raises(ValueError, match="same source"):
        build_funnel(full, filtered, legacy, benchmark, tmp_path / "out")
    (filtered / "repositories.csv").write_text("tampered")
    with pytest.raises(ValueError, match="checksum"):
        build_funnel(full, filtered, legacy, benchmark, tmp_path / "out")
