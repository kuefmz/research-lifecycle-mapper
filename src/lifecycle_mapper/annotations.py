"""Read-only CSV/XLSX annotation import; no consensus inference or adjudication."""

import csv
import io
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from . import STAGES
from .canonical import sha256, write_csv, write_json

FIELDS = [
    "repository",
    "stage",
    "jenifer",
    "esteban",
    "proposed_consensus",
    "approved_consensus",
    "approval_reference",
]
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def workbook_rows(path: Path) -> list[dict[str, str]]:
    """Import XLSX sheet named annotations. Reject formulas rather than use stale caches."""
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets = workbook.findall("s:sheets/s:sheet", NS)
        sheet = next((sheet for sheet in sheets if sheet.attrib["name"] == "annotations"), None)
        if sheet is None:
            raise ValueError("XLSX requires a worksheet named annotations")
        rel_id = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = next(item.attrib["Target"] for item in relations if item.attrib["Id"] == rel_id)
        if target.startswith("/"):
            target = target.lstrip("/")
        else:
            target = "xl/" + target
        if ".." in Path(target).parts:
            raise ValueError("Unsafe workbook relationship")
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            table = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(node.itertext()) for node in table]
        sheet_xml = ET.fromstring(archive.read(target))
        matrix = []
        for row in sheet_xml.findall("s:sheetData/s:row", NS):
            values: dict[int, str] = {}
            for cell in row.findall("s:c", NS):
                if cell.find("s:f", NS) is not None:
                    raise ValueError("Annotation cells must contain literal values, not formulas")
                letters = re.match(r"[A-Z]+", cell.attrib["r"])
                if letters is None:
                    raise ValueError("Invalid worksheet cell address")
                column = 0
                for letter in letters.group():
                    column = column * 26 + ord(letter) - ord("A") + 1
                value_node = cell.find("s:v", NS)
                value = value_node.text or "" if value_node is not None else ""
                if cell.attrib.get("t") == "s":
                    value = strings[int(value)]
                elif cell.attrib.get("t") == "inlineStr":
                    inline = cell.find("s:is", NS)
                    value = "".join(inline.itertext()) if inline is not None else ""
                values[column - 1] = value
            if values:
                matrix.append([values.get(index, "") for index in range(max(values) + 1)])
        if not matrix or matrix[0] != FIELDS:
            raise ValueError(f"Worksheet headers must be exactly {FIELDS}")
        result = []
        for values_list in matrix[1:]:
            if len(values_list) > len(FIELDS):
                raise ValueError("Unexpected worksheet columns")
            values_list += [""] * (len(FIELDS) - len(values_list))
            result.append(dict(zip(FIELDS, values_list, strict=True)))
        return result


def import_annotations(
    source: Path,
    output: Path,
    version: str,
    expected_repositories: int = 100,
    expected_disagreements: int | None = 247,
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("Import output must be a new directory; source is never modified")
    raw = source.read_bytes()
    if source.suffix.lower() == ".xlsx":
        rows = workbook_rows(source)
    elif source.suffix.lower() == ".csv":
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if reader.fieldnames != FIELDS:
            raise ValueError(f"CSV headers must be exactly {FIELDS}")
        rows = list(reader)
    else:
        raise ValueError("Supported annotation inputs: CSV and XLSX")
    normalized = []
    seen = set()
    for row in rows:
        if set(row) != set(FIELDS) or any(value is None for value in row.values()):
            raise ValueError("Malformed annotation row")
        item = {field: row[field].strip() for field in FIELDS}
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", item["repository"]):
            raise ValueError("Annotation repository must be owner/name")
        if item["stage"] not in STAGES:
            raise ValueError("Unknown lifecycle stage; Implementation is not Method")
        for field in ["jenifer", "esteban"]:
            if item[field] not in {"0", "1"}:
                raise ValueError("Independent labels must be literal 0 or 1")
        for field in ["proposed_consensus", "approved_consensus"]:
            if item[field] not in {"", "0", "1"}:
                raise ValueError("Consensus fields must be empty, 0, or 1")
        if bool(item["approved_consensus"]) != bool(item["approval_reference"]):
            raise ValueError("Every approved label requires an explicit approval reference")
        key = (item["repository"].lower(), item["stage"])
        if key in seen:
            raise ValueError("Duplicate repository-stage annotation")
        seen.add(key)
        normalized.append(item)
    repositories = {row["repository"].lower() for row in normalized}
    if len(repositories) != expected_repositories or len(normalized) != expected_repositories * 6:
        raise ValueError("Annotation set must contain six labels per expected repository")
    disagreements = [row for row in normalized if row["jenifer"] != row["esteban"]]
    if expected_disagreements is not None and len(disagreements) != expected_disagreements:
        raise ValueError("Independent disagreement count differs from declared provenance")
    normalized.sort(key=lambda row: (row["repository"].lower(), STAGES.index(row["stage"])))
    output.mkdir(parents=True)
    write_csv(output / "annotations.csv", FIELDS, normalized)
    write_csv(
        output / "disagreements.csv",
        FIELDS,
        sorted(
            disagreements, key=lambda row: (row["repository"].lower(), STAGES.index(row["stage"]))
        ),
    )
    provenance = {
        "schema_version": 1,
        "version": version,
        "original_checksum": sha256(raw),
        "original_filename": source.name,
        "annotators": ["Jenifer", "Esteban"],
        "process": "independent-labeling-followed-by-human-adjudication",
        "repository_count": len(repositories),
        "pair_count": len(normalized),
        "initial_disagreements": len(disagreements),
        "gold_status": "approved"
        if all(row["approved_consensus"] for row in normalized)
        else "pending",
        "annotations_sha256": sha256((output / "annotations.csv").read_bytes()),
    }
    write_json(output / "provenance.json", provenance)
    return provenance
