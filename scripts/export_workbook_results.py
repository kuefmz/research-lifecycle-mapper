"""Export selected benchmark worksheets as exact cached-value A1:G101 CSV tables.

The source workbook is never modified. No missing or Unverified label becomes zero.
"""

import argparse
import csv
import hashlib
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
SELECTION = [
    ("reviewer1", "research_lifecycle_benchmark_10", None),
    ("reviewer2", "Hoja 10", None),
    ("agreement", "agreement", None),
    ("final_agreement", "final_agreement", None),
    ("llm_documentation", "Hoja 11", None),
    ("llm_code", "Hoja 12", None),
    ("llm_combined", "Hoja 13", None),
    ("heuristics_documentation", "benchmark_100_heuristics_doc_la", "Hoja 14"),
    ("heuristics_code", "benchmark_100_heuristics_code_l", "Hoja 15"),
    ("heuristics_combined", "benchmark_100_heuristics_both_l", "Hoja 16"),
]


def read_workbook(source: Path) -> dict:
    with zipfile.ZipFile(source) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = [
                "".join(node.text or "" for node in item.findall(".//s:t", NS))
                for item in ET.fromstring(archive.read("xl/sharedStrings.xml"))
            ]
        relationships = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        }
        result = {}
        for sheet in ET.fromstring(archive.read("xl/workbook.xml")).findall("s:sheets/s:sheet", NS):
            target = relationships[sheet.attrib[REL]]
            target = target.lstrip("/") if target.startswith("/") else "xl/" + target
            root = ET.fromstring(archive.read(target))
            cells = {}
            for cell in root.findall(".//s:sheetData/s:row/s:c", NS):
                value_node = cell.find("s:v", NS)
                value = value_node.text or "" if value_node is not None else ""
                if cell.attrib.get("t") == "s":
                    value = strings[int(value)]
                elif cell.attrib.get("t") == "inlineStr":
                    value = "".join(n.text or "" for n in cell.findall(".//s:t", NS))
                if cell.find("s:f", NS) is not None and value_node is None:
                    raise ValueError(
                        f"No cached formula value: {sheet.attrib['name']}!{cell.attrib['r']}"
                    )
                cells[cell.attrib["r"]] = value
            result[sheet.attrib["name"]] = cells
    return result


def export(source: Path, output: Path) -> dict:
    sheets = read_workbook(source)
    known = {name for _, name, _ in SELECTION} | {name for _, _, name in SELECTION if name}
    if set(sheets) != known:
        raise ValueError("Workbook sheet set changed; review the explicit selection mapping")
    output.mkdir(parents=True, exist_ok=True)
    entries, conversations = [], []
    for role, name, superseded in SELECTION:
        cells = sheets[name]
        rows = [[cells.get(f"{column}{row}", "") for column in "ABCDEFG"] for row in range(1, 102)]
        if rows[0][1:] != [
            "Collection",
            "Processing",
            "Method",
            "Experimentation",
            "Evaluation",
            "Dissemination",
        ]:
            raise ValueError(f"Unexpected stage headers in {name}")
        if (
            any(not row[0] for row in rows[1:])
            or len({row[0].casefold() for row in rows[1:]}) != 100
        ):
            raise ValueError(f"Expected 100 unique repository rows in {name}")
        path = output / f"{role}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerows(rows)
        entries.append(
            {
                "role": role,
                "source_sheet": name,
                "range": "A1:G101",
                "csv": path.name,
                "rows_including_header": 101,
                "columns": 7,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "superseded_sheet_omitted": superseded,
            }
        )
        if role.startswith("llm_"):
            url = cells.get("H1", "")
            if not url.startswith("https://chatgpt.com/share/"):
                raise ValueError(f"Missing shared conversation at {name}!H1")
            conversations.append(
                {
                    "mode": role.removeprefix("llm_"),
                    "source_sheet": name,
                    "source_cell": "H1",
                    "url": url,
                }
            )
    manifest = {
        "source_workbook_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source": "Attached workbook snapshot; original Google Sheet unchanged",
        "selection_policy": "Use explicitly named latest heuristic tabs, not inferred modification dates. Export all other distinct sheet roles.",
        "reviewer_mapping": "Matched all 600 labels per reviewer to the existing independent annotation CSV; no names exported.",
        "value_policy": "Cached cell text preserved; formulas, styling, hyperlinks, comments and out-of-range notes excluded. Blanks and Unverified preserved.",
        "sheets": entries,
        "conversations": conversations,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/benchmark-100/workbook"))
    args = parser.parse_args()
    result = export(args.workbook, args.output)
    print(f"Exported {len(result['sheets'])} CSVs, each 101 rows by 7 columns")


if __name__ == "__main__":
    main()
