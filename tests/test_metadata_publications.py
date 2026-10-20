import io
import json
import tarfile

import pytest

from lifecycle_mapper.metadata_publications import paper_evidence, select_metadata
from lifecycle_mapper.openaire import extract
from lifecycle_mapper.funnel import build_funnel


def test_textual_evidence_does_not_treat_software_pid_or_future_paper_as_publication():
    record = {
        "pids": [{"scheme": "doi", "value": "10.5281/zenodo.123"}],
        "instances": [
            {"type": "Software", "pids": [{"scheme": "doi", "value": "10.5281/zenodo.456"}]}
        ],
        "descriptions": [
            "paper-ready data",
            'A future paper "Planned study title"',
            "Software for experiments. DOI 10.5281/zenodo.123",
            "The paper uses this software 10.5281/zenodo.456",
        ],
        "indicators": {"citationImpact": {"citationCount": 2}},
    }
    assert paper_evidence(record) == []
    record["descriptions"] += [
        'Code to replicate the study "A sufficiently specific research title."',
        "Associated paper: https://doi.org/10.1234/example.",
        "See https://arxiv.org/abs/2401.01234",
    ]
    evidence = paper_evidence(record)
    assert {r["kind"] for r in evidence} == {
        "named_paper_or_study",
        "external_doi_near_paper_mention",
        "arxiv_reference",
    }
    assert (
        next(r["reference"] for r in evidence if r["kind"] == "external_doi_near_paper_mention")
        == "10.1234/example"
    )


def test_metadata_pipeline_preserves_unresolved_and_deduplicates(tmp_path):
    records = [
        {
            "id": "s1",
            "description": 'An experiment. Replicate the study "Specific research paper title"',
            "codeRepositoryUrl": "https://github.com/a/one",
        },
        {
            "id": "s2",
            "description": "experiments with paper-ready data",
            "codeRepositoryUrl": "https://github.com/a/two",
        },
        {
            "id": "s3",
            "description": "experiments; the paper https://doi.org/10.1234/example",
            "codeRepositoryUrl": "https://github.com/a/one",
        },
    ]
    source = tmp_path / "software.tar"
    raw = "".join(json.dumps(r) + "\n" for r in records).encode()
    with tarfile.open(source, "w") as stream:
        item = tarfile.TarInfo("data.jsonl")
        item.size = len(raw)
        stream.addfile(item, io.BytesIO(raw))
    candidates = tmp_path / "candidates"
    full = tmp_path / "full"
    extract(source, candidates, "release", True)
    extract(source, full, "release")
    out = tmp_path / "out"
    report = select_metadata(candidates, source, out, "release")
    assert report["counts"]["unique_github_repositories"] == 1
    assert report["counts"]["software_ids_with_association_candidates"] == 2
    assert report["counts"]["software_ids_unresolved"] == 1
    assert "unresolved" in (out / "metadata_audit.csv").read_text()
    assert report["selection"]["publication_required"] is False
    legacy = tmp_path / "legacy.txt"
    legacy.write_text("https://github.com/a/one\n")
    funnel = build_funnel(
        full, candidates, legacy, legacy, tmp_path / "funnel", publication_extraction=out
    )
    assert funnel["eligibility"]["publication_linked_description_count"] is None
    assert funnel["paper_evidence_status"].startswith("Unreviewed")
    assert any(r["stage"] == "metadata_association_candidates" for r in funnel["stages"])
    with pytest.raises(ValueError, match="archive/release"):
        select_metadata(candidates, source, tmp_path / "wrong", "other-release")
