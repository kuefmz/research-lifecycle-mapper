import zipfile
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest

from lifecycle_mapper import STAGES
from lifecycle_mapper.annotations import FIELDS, import_annotations

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def build_workbook(path, formula=False):
    workbook = Element("workbook", xmlns=NS)
    sheets = SubElement(workbook, "sheets")
    SubElement(
        sheets,
        "sheet",
        name="annotations",
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
    values = [FIELDS] + [
        ["owner/repo", stage, "1", "0" if index == 0 else "1", "1", "", ""]
        for index, stage in enumerate(STAGES)
    ]
    for number, row in enumerate(values, 1):
        element = SubElement(data, "row", r=str(number))
        for index, value in enumerate(row):
            cell = SubElement(element, "c", r=f"{chr(65 + index)}{number}", t="inlineStr")
            SubElement(SubElement(cell, "is"), "t").text = value
            if formula and number == 2 and index == 2:
                SubElement(cell, "f").text = "1+0"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", tostring(workbook))
        archive.writestr("xl/_rels/workbook.xml.rels", tostring(relations))
        archive.writestr("xl/worksheets/sheet1.xml", tostring(sheet))


def test_xlsx_preserves_original_and_matches_schema(tmp_path):
    path = tmp_path / "original.xlsx"
    build_workbook(path)
    original = path.read_bytes()
    result = import_annotations(path, tmp_path / "imported", "xlsx-test-v1", 1, 1)
    assert result["gold_status"] == "pending"
    assert result["pair_count"] == 6
    assert path.read_bytes() == original


def test_xlsx_formulas_rejected(tmp_path):
    path = tmp_path / "original.xlsx"
    build_workbook(path, formula=True)
    with pytest.raises(ValueError, match="literal values"):
        import_annotations(path, tmp_path / "imported", "xlsx-test-v1", 1, 1)
