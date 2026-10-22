"""Read worksheet values without modifying the source workbook."""

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def worksheet_cells(path: Path, sheet_name: str) -> dict[int, dict[str, str]]:
    """Read selected cells only; formulas/errors and duplicate cell addresses are rejected."""
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        matches = [
            s for s in workbook.findall("s:sheets/s:sheet", NS) if s.attrib["name"] == sheet_name
        ]
        if len(matches) != 1:
            raise ValueError(f"Workbook requires exactly one {sheet_name!r} worksheet")
        relation_id = matches[0].attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relationship = next(r for r in relations if r.attrib["Id"] == relation_id)
        if relationship.attrib.get("TargetMode") == "External":
            raise ValueError("External worksheet relationship")
        target = relationship.attrib["Target"]
        target = target.lstrip("/") if target.startswith("/") else "xl/" + target
        if ".." in Path(target).parts:
            raise ValueError("Unsafe workbook relationship")
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            table = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(t.text or "" for t in item.findall(".//s:t", NS)) for item in table]
        sheet = ET.fromstring(archive.read(target))
        rows: dict[int, dict[str, str]] = {}
        for row in sheet.findall("s:sheetData/s:row", NS):
            number = int(row.attrib["r"])
            if number in rows:
                raise ValueError("Duplicate worksheet row")
            cells = {}
            for cell in row.findall("s:c", NS):
                address = cell.attrib["r"]
                match = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", address)
                if match is None or int(match[2]) != number or match[1] in cells:
                    raise ValueError("Invalid or duplicate worksheet cell")
                if cell.find("s:f", NS) is not None or cell.attrib.get("t") == "e":
                    # Keep marker so unrelated private/formula columns do not enter exports.
                    value = "__UNRESOLVED_FORMULA_OR_ERROR__"
                elif cell.attrib.get("t") == "inlineStr":
                    value = "".join(t.text or "" for t in cell.findall(".//s:t", NS))
                else:
                    node = cell.find("s:v", NS)
                    value = node.text or "" if node is not None else ""
                    if cell.attrib.get("t") == "s":
                        value = strings[int(value)]
                cells[match[1]] = value
            rows[number] = cells
        return rows
