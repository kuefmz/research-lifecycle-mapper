"""Explicit Agreement Final import; schema mapping and approval are external inputs."""

import csv
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from . import STAGES
from .acquisition import repository_id
from .annotations import NS
from .canonical import read_json, sha256, write_csv, write_json

SHEET = "Agreement Final"
FIELDS = [
    "repository",
    "original_repository_url",
    "original_row_id",
    "worksheet_row",
    "stage",
    "label",
    "original_label",
    "cell",
    "consensus_status",
    "approval_reference",
]


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


def import_final(
    source: Path, output: Path, config_path: Path, approval_path: Path | None = None
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("Import output must be new; original workbook remains unchanged")
    config = read_json(config_path)
    sheet = config.get("worksheet")
    if sheet not in {SHEET, "final_agreement"} or config.get("layout") != "wide":
        raise ValueError("Explicit Agreement Final wide-layout mapping required")
    if set(config["stage_columns"]) != set(STAGES):
        raise ValueError("Map exactly six stage columns; never silently rename Implementation")
    columns = [
        config["repository_column"],
        *([config["row_id_column"]] if config.get("row_id_column") else []),
        *config["stage_columns"].values(),
    ]
    if len(set(columns)) != len(columns) or not all(
        re.fullmatch(r"[A-Z]+", value) for value in columns
    ):
        raise ValueError("Column mappings must be distinct Excel letter addresses")
    label_mapping = config.get("label_mapping", {"0": 0, "1": 1})
    if any(type(value) is not int or value not in (0, 1) for value in label_mapping.values()):
        raise ValueError("Label mapping must explicitly resolve only binary labels")
    raw_hash = sha256(source.read_bytes())
    approved = False
    approval_reference = ""
    if approval_path:
        approval = read_json(approval_path)
        if (
            approval.get("status") != "approved"
            or approval.get("worksheet") != sheet
            or approval.get("workbook_sha256") != raw_hash
            or approval.get("import_config_sha256") != sha256(config_path.read_bytes())
            or not approval.get("approval_reference")
        ):
            raise ValueError(
                "Consensus approval must identify the exact workbook, worksheet and import mapping"
            )
        approved = True
        approval_reference = approval["approval_reference"]
    rows = worksheet_cells(source, sheet)
    header_row = config.get("header_row", 1)
    headers = config["expected_headers"]
    if set(headers) != set(columns) or any(
        rows.get(header_row, {}).get(col) != title for col, title in headers.items()
    ):
        raise ValueError("Worksheet headers differ from explicitly approved import mapping")
    normalized = []
    repositories = []
    seen_repos = set()
    seen_rows = set()
    for number, cells in sorted(rows.items()):
        if number <= header_row:
            continue
        if not any(cells.get(col, "").strip() for col in columns):
            continue
        url = cells.get(config["repository_column"], "").strip()
        repo = repository_id(url)
        row_id = (
            cells.get(config["row_id_column"], "").strip()
            if config.get("row_id_column")
            else f"{sheet}!{number}"
        )
        if not row_id or row_id == "__UNRESOLVED_FORMULA_OR_ERROR__" or row_id in seen_rows:
            raise ValueError("Missing, duplicate or invalid original row identifier")
        if repo.casefold() in seen_repos:
            raise ValueError("Duplicate repository in Agreement Final")
        seen_repos.add(repo.casefold())
        seen_rows.add(row_id)
        labels = {}
        for stage in STAGES:
            column = config["stage_columns"][stage]
            raw_label = cells.get(column, "")
            key = raw_label.strip()
            if key not in label_mapping:
                raise ValueError(f"Missing, ambiguous or invalid label at {column}{number}")
            label = label_mapping[key]
            labels[stage] = label
            normalized.append(
                {
                    "repository": repo,
                    "original_repository_url": url,
                    "original_row_id": row_id,
                    "worksheet_row": number,
                    "stage": stage,
                    "label": label,
                    "original_label": raw_label,
                    "cell": f"{column}{number}",
                    "consensus_status": "approved" if approved else "candidate",
                    "approval_reference": approval_reference,
                }
            )
        repositories.append(
            {
                "repository": repo,
                "source_url": url,
                "labels": labels,
                "commit": None,
                "snapshot": None,
                "snapshot_sha256": None,
            }
        )
    expected = config.get("expected_repositories", 100)
    if len(repositories) != expected or len(normalized) != expected * 6:
        raise ValueError("Agreement Final does not contain the declared repository/stage count")
    if (
        expected != 100
        and not config.get("synthetic")
        and not config.get("count_correction_reference")
    ):
        raise ValueError("A real count correction requires a documented researcher decision")
    normalized.sort(key=lambda row: (row["repository"].casefold(), STAGES.index(row["stage"])))
    output.mkdir(parents=True)
    write_csv(output / "benchmark.csv", FIELDS, normalized)
    provenance = {
        "schema_version": 1,
        "version": config["version"],
        "source_worksheet": sheet,
        "workbook_sha256": raw_hash,
        "import_config": config,
        "import_config_sha256": sha256(config_path.read_bytes()),
        "repository_count": len(repositories),
        "pair_count": len(normalized),
        "gold_status": "approved" if approved else "candidate",
        "approval_reference": approval_reference,
        "approval_sha256": sha256(approval_path.read_bytes()) if approval_path else None,
        "consensus_table_sha256": sha256((output / "benchmark.csv").read_bytes()),
        "independent_annotations": "not-verified-by-consensus-import",
        "synthetic": bool(config.get("synthetic")),
    }
    write_json(output / "provenance.json", provenance)
    write_json(
        output / "manifest.json",
        {
            "schema_version": 1,
            "kind": "research",
            "status": "pending",
            "version": config["version"],
            "stages": list(STAGES),
            "consensus_status": provenance["gold_status"],
            "repositories": sorted(repositories, key=lambda row: row["repository"]),
            "missing": [
                "immutable revisions and snapshots",
                "approved human codebook",
                "verified sampling provenance",
                "independent annotations and disagreement provenance",
            ],
        },
    )
    return provenance


def publication_export(imported: Path, output: Path, release_approval: Path) -> dict[str, Any]:
    provenance = read_json(imported / "provenance.json")
    approval = read_json(release_approval)
    checksum = sha256((imported / "benchmark.csv").read_bytes())
    if (
        provenance["gold_status"] != "approved"
        or checksum != provenance["consensus_table_sha256"]
        or approval.get("status") != "approved"
        or approval.get("consensus_table_sha256") != checksum
        or not approval.get("release_reference")
    ):
        raise ValueError(
            "Publication export requires consensus and release approval for this exact table"
        )
    if output.exists():
        raise ValueError("Publication output already exists")
    with (imported / "benchmark.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    output.mkdir(parents=True)
    write_csv(
        output / "labels.csv",
        ["repository", "stage", "label"],
        [{key: row[key] for key in ["repository", "stage", "label"]} for row in rows],
    )
    manifest = {
        "version": provenance["version"],
        "labels_sha256": sha256((output / "labels.csv").read_bytes()),
        "source_table_sha256": checksum,
        "release_reference": approval["release_reference"],
        "excluded_fields": [
            "private notes",
            "row identifiers",
            "annotator identities",
            "workbook metadata",
        ],
    }
    write_json(output / "manifest.json", manifest)
    return manifest
