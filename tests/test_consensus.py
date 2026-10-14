import csv
import json
import zipfile
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest

from lifecycle_mapper import STAGES
from lifecycle_mapper.canonical import sha256, write_json
from lifecycle_mapper.consensus import import_final, publication_export

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def fixture(tmp_path, count=100, mutation=None, sheet_name="Agreement Final"):
    workbook = Element("workbook", xmlns=NS)
    sheets = SubElement(workbook, "sheets")
    SubElement(
        sheets,
        "sheet",
        name=sheet_name,
        sheetId="1",
        attrib={"{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id": "rId1"},
    )
    relations = Element(
        "Relationships", xmlns="http://schemas.openxmlformats.org/package/2006/relationships"
    )
    SubElement(
        relations, "Relationship", Id="rId1", Target="worksheets/sheet1.xml", Type="worksheet"
    )
    sheet = Element("worksheet", xmlns=NS)
    data = SubElement(sheet, "sheetData")
    headers = ["Row ID", "Repository URL", *STAGES, "Private notes"]
    rows = [headers]
    for index in range(count):
        row = [
            f"source-row-{index}",
            f"https://github.com/synthetic/repo-{index}",
            *[str((index + stage) % 2) for stage in range(6)],
            "PRIVATE TEST NOTE",
        ]
        if mutation:
            mutation(row, index)
        rows.append(row)
    for number, row in enumerate(rows, 1):
        element = SubElement(data, "row", r=str(number))
        for index, value in enumerate(row):
            cell = SubElement(element, "c", r=f"{chr(65 + index)}{number}", t="inlineStr")
            SubElement(SubElement(cell, "is"), "t").text = value
    path = tmp_path / "original.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", tostring(workbook))
        archive.writestr("xl/_rels/workbook.xml.rels", tostring(relations))
        archive.writestr("xl/worksheets/sheet1.xml", tostring(sheet))
    config = {
        "worksheet": "Agreement Final",
        "layout": "wide",
        "version": "synthetic-import-v1",
        "expected_repositories": 100,
        "header_row": 1,
        "row_id_column": "A",
        "repository_column": "B",
        "stage_columns": {stage: chr(67 + i) for i, stage in enumerate(STAGES)},
        "expected_headers": {chr(65 + i): title for i, title in enumerate(headers[:8])},
        "label_mapping": {"0": 0, "1": 1},
        "synthetic": True,
    }
    config_path = tmp_path / "import.json"
    write_json(config_path, config)
    return path, config_path


def test_exact_final_sheet_candidate_and_source_preservation(tmp_path):
    path, config = fixture(tmp_path)
    original = path.read_bytes()
    result = import_final(path, tmp_path / "imported", config)
    assert result["gold_status"] == "candidate"
    assert result["source_worksheet"] == "Agreement Final"
    assert result["pair_count"] == 600 and result["repository_count"] == 100
    assert result["workbook_sha256"] == sha256(original) and path.read_bytes() == original
    text = (tmp_path / "imported/benchmark.csv").read_text()
    assert "PRIVATE TEST NOTE" not in text
    rows = list(csv.DictReader(text.splitlines()))
    assert rows[0]["original_row_id"] == "source-row-0" and rows[0]["cell"] == "C2"
    assert json.loads((tmp_path / "imported/manifest.json").read_bytes())["status"] == "pending"


def test_verified_consensus_and_clean_release_export(tmp_path):
    path, config = fixture(tmp_path)
    approval = tmp_path / "approval.json"
    write_json(
        approval,
        {
            "status": "approved",
            "worksheet": "Agreement Final",
            "workbook_sha256": sha256(path.read_bytes()),
            "import_config_sha256": sha256(config.read_bytes()),
            "approval_reference": "synthetic-test-approval",
        },
    )
    result = import_final(path, tmp_path / "imported", config, approval)
    assert result["gold_status"] == "approved"
    release = tmp_path / "release.json"
    write_json(
        release,
        {
            "status": "approved",
            "consensus_table_sha256": result["consensus_table_sha256"],
            "release_reference": "synthetic-test-release",
        },
    )
    publication_export(tmp_path / "imported", tmp_path / "public", release)
    text = (tmp_path / "public/labels.csv").read_text()
    assert "original_row_id" not in text and "PRIVATE TEST NOTE" not in text


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row, i: row.__setitem__(2, "?") if i == 0 else None,
        lambda row, i: row.__setitem__(3, "") if i == 0 else None,
        lambda row, i: row.__setitem__(1, "https://github.com/synthetic/repo-0")
        if i == 1
        else None,
        lambda row, i: row.__setitem__(0, "source-row-0") if i == 1 else None,
    ],
)
def test_ambiguous_missing_duplicate_values_rejected(tmp_path, mutation):
    path, config = fixture(tmp_path, mutation=mutation)
    with pytest.raises(ValueError):
        import_final(path, tmp_path / "imported", config)
    assert not (tmp_path / "imported").exists()


def test_wrong_sheet_cannot_substitute_independent_annotations(tmp_path):
    path, config = fixture(tmp_path, sheet_name="annotations")
    with pytest.raises(ValueError, match="Agreement Final"):
        import_final(path, tmp_path / "imported", config)


def test_wrong_approval_checksum_rejected(tmp_path):
    path, config = fixture(tmp_path)
    approval = tmp_path / "approval.json"
    write_json(
        approval,
        {
            "status": "approved",
            "worksheet": "Agreement Final",
            "workbook_sha256": "0" * 64,
            "approval_reference": "fixture",
        },
    )
    with pytest.raises(ValueError, match="exact workbook"):
        import_final(path, tmp_path / "imported", config, approval)


def test_wrong_count_rejected(tmp_path):
    path, config = fixture(tmp_path, count=99)
    with pytest.raises(ValueError, match="declared"):
        import_final(path, tmp_path / "imported", config)


def test_candidate_labels_cannot_be_published(tmp_path):
    path, config = fixture(tmp_path)
    result = import_final(path, tmp_path / "imported", config)
    release = tmp_path / "release.json"
    write_json(
        release,
        {
            "status": "approved",
            "consensus_table_sha256": result["consensus_table_sha256"],
            "release_reference": "test",
        },
    )
    with pytest.raises(ValueError, match="consensus and release approval"):
        publication_export(tmp_path / "imported", tmp_path / "public", release)
