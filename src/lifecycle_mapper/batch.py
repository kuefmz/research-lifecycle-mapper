"""Strict repository-list parsing for the corpus runner."""

import csv
import io
from pathlib import Path
from typing import Any
from .acquisition import repository_id
from .canonical import read_json
from .workbook import worksheet_cells

URL_FIELDS = (
    "repository_url",
    "github_repository_url",
    "source_url",
    "original_repository_url",
    "repository",
)


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value.startswith("https://"):
        value = "https://github.com/" + value.removeprefix("github.com/")
    return "https://github.com/" + repository_id(value.rstrip("/"))


def records_from_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for number, row in enumerate(rows, 1):
        values = [normalize_url(str(row[field])) for field in URL_FIELDS if row.get(field)]
        if not values or len({url.casefold() for url in values}) != 1:
            raise ValueError(f"Row {number}: missing or conflicting repository identifiers")
        url = values[0]
        ref = row.get("commit") or row.get("ref") or None
        key = url.casefold()
        if key in result and result[key]["ref"] != ref:
            raise ValueError(f"Conflicting revisions for {url}")
        if key not in result:
            result[key] = {"url": url, "ref": ref, "source_rows": []}
        result[key]["source_rows"].append(row.get("worksheet_row", number))
    if not result:
        raise ValueError("No repository URLs found")
    return sorted(result.values(), key=lambda item: item["url"].casefold())


def read_inputs(
    path: Path,
    repository_column: str = "B",
    worksheet: str = "Agreement Final",
    header_row: int = 1,
) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".xlsx":
        if not repository_column.isalpha() or not repository_column.isupper():
            raise ValueError("Choose an Excel column letter, such as B")
        rows = worksheet_cells(path, worksheet)
        return records_from_rows(
            [
                {"repository_url": cells[repository_column], "worksheet_row": number}
                for number, cells in sorted(rows.items())
                if number > header_row and cells.get(repository_column, "").strip()
            ]
        )
    if path.suffix.lower() == ".json":
        payload = read_json(path)
        rows = payload.get("repositories", []) if isinstance(payload, dict) else payload
        return records_from_rows(
            [{"repository_url": row} if isinstance(row, str) else row for row in rows]
        )
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".csv":
        return records_from_rows(list(csv.DictReader(io.StringIO(text))))
    return records_from_rows(
        [{"repository_url": line.strip()} for line in text.splitlines() if line.strip()]
    )
