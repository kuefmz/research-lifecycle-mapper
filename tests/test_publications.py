import io
import json
import tarfile

import pytest

from lifecycle_mapper.openaire import extract
from lifecycle_mapper.publications import select_publications
from lifecycle_mapper.funnel import build_funnel


def archive(path, records):
    raw = "".join(json.dumps(r) + "\n" for r in records).encode()
    with tarfile.open(path, "w") as stream:
        item = tarfile.TarInfo("data.jsonl")
        item.size = len(raw)
        stream.addfile(item, io.BytesIO(raw))


def test_join_publication_endpoints_before_repository_deduplication(tmp_path):
    software = tmp_path / "software.tar"
    archive(
        software,
        [
            {
                "id": "s1",
                "description": "experiment",
                "codeRepositoryUrl": "https://github.com/a/shared",
            },
            {
                "id": "s2",
                "description": "experiments",
                "codeRepositoryUrl": "https://github.com/a/shared",
            },
            {
                "id": "s3",
                "description": "experiment",
                "codeRepositoryUrl": "https://github.com/a/other",
            },
            {
                "id": "s4",
                "description": "ordinary",
                "codeRepositoryUrl": "https://github.com/a/excluded",
            },
        ],
    )
    candidates = tmp_path / "candidates"
    full = tmp_path / "full"
    extract(software, candidates, "release", True)
    extract(software, full, "release")
    relations = tmp_path / "relations.tar"
    records = [
        {
            "source": "p1",
            "sourceType": "publication",
            "target": "s2",
            "targetType": "software",
            "relType": {"name": "References"},
        },
        {
            "source": "s1",
            "sourceType": "software",
            "target": "d1",
            "targetType": "dataset",
            "relType": {"name": "IsRelatedTo"},
        },
        {
            "source": "s3",
            "target": "p2",
            "targetType": "product",
            "relType": {"name": "IsRelatedTo"},
        },
        {
            "source": "s4",
            "target": "p1",
            "targetType": "publication",
            "relType": {"name": "References"},
        },
        {
            "source": {"id": "s2", "type": "software"},
            "target": {"id": "p3", "type": "publication"},
            "reltype": {"name": "IsRelatedTo"},
        },
    ]
    archive(relations, records + [records[0]])
    out = tmp_path / "selected"
    result = select_publications(candidates, out, (relations,), "release")
    assert result["counts"]["unique_github_repositories"] == 1
    assert result["counts"]["software_ids_with_publication"] == 1
    assert result["counts"]["publication_relations_retained"] == 2
    assert result["counts"]["endpoints_not_confirmed_as_publications"] == 2
    assert (out / "repositories.txt").read_text() == "https://github.com/a/shared\n"
    assert "s1" not in (out / "software_links.csv").read_text()
    pubs = tmp_path / "publication.tar"
    archive(pubs, [{"id": "p2"}])
    extended = select_publications(
        candidates, tmp_path / "extended", (relations,), "release", publication_archives=(pubs,)
    )
    assert extended["counts"]["unique_github_repositories"] == 2
    restricted = select_publications(
        candidates, tmp_path / "restricted", (relations,), "release", relation_names=("References",)
    )
    assert restricted["counts"]["publication_relations_retained"] == 1
    legacy = tmp_path / "legacy.txt"
    legacy.write_text("https://github.com/a/shared\n")
    report = build_funnel(
        full, candidates, legacy, legacy, tmp_path / "funnel", publication_extraction=out
    )
    assert report["eligibility"]["publication_linked_description_count"] == 1
    assert report["eligibility"]["publication_linkage_status"].startswith("Explicit graph")
    with pytest.raises(ValueError, match="source-record"):
        select_publications(candidates, tmp_path / "bad", (relations,), "wrong")
    with pytest.raises(ValueError, match="one or more"):
        select_publications(candidates, tmp_path / "none", (), "release")
