"""Description selection precedes repository deduplication and records its scope."""

import io
import json
import tarfile

from lifecycle_mapper.openaire import extract


def test_experiment_description_selection(tmp_path):
    descriptions = [
        "An EXPERIMENT.",
        ["Models", "Multiple experiments"],
        "experimental methods",
        "experimentation",
        None,
        "",
        {"value": "An experiment"},
        {"text": "Experiments!"},
        {"language": "experiment", "value": "No matching term"},
    ]
    records = [
        {
            "id": str(i),
            "description": description,
            "codeRepositoryUrl": f"https://github.com/a/repo{i}",
        }
        for i, description in enumerate(descriptions)
    ]
    records.extend(
        [
            {
                "id": "duplicate",
                "description": "experiment",
                "codeRepositoryUrl": "https://github.com/a/repo0.git",
            },
            {"id": "no-link", "description": "experiments"},
            {"id": "prose-only", "description": "experiment https://github.com/a/prose"},
            {
                "id": "title-only",
                "title": "experiment",
                "codeRepositoryUrl": "https://github.com/a/title",
            },
            {
                "id": "plural-field",
                "descriptions": ["experiment"],
                "codeRepositoryUrl": "https://github.com/a/plural",
            },
        ]
    )
    source = tmp_path / "software.tar"
    raw = "".join(json.dumps(r) + "\n" for r in records).encode()
    with tarfile.open(source, "w") as archive:
        member = tarfile.TarInfo("software.jsonl")
        member.size = len(raw)
        archive.addfile(member, io.BytesIO(raw))
    output = tmp_path / "filtered"
    summary = extract(source, output, "release", description_experiments=True)
    assert (output / "repositories.txt").read_text().splitlines() == [
        "https://github.com/a/plural",
        "https://github.com/a/repo0",
        "https://github.com/a/repo1",
        "https://github.com/a/repo6",
        "https://github.com/a/repo7",
    ]
    assert summary["counts"]["software_records"] == 14
    assert summary["counts"]["records_matching_description"] == 8
    assert summary["counts"]["records_excluded_by_description"] == 6
    assert summary["counts"]["github_record_links"] == 6
    assert summary["counts"]["unique_github_repositories"] == 5
    assert summary["selection"]["pattern"] == r"\bexperiments?\b"
    assert json.loads((output / "summary.json").read_text()) == summary
    unfiltered = extract(source, tmp_path / "all", "release")
    assert unfiltered["counts"]["unique_github_repositories"] == 11
    assert "selection" not in unfiltered
