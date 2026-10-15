"""Batch predictions are independent of human labels; evaluation remains separate."""

import csv
import io
import json
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import MODES, STAGES
from .acquisition import acquire, replay, repository_id
from .analysis import analyze, load_rules
from .benchmark import git_state, implementation_hash
from .canonical import contained, json_bytes, read_json, sha256, write_csv, write_json
from .consensus import worksheet_cells
from .git_acquisition import acquire_git

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


def sample_records(
    records: list[dict[str, Any]], count: int | None, seed: str
) -> list[dict[str, Any]]:
    if count is None:
        return records
    if not 1 <= count <= len(records):
        raise ValueError("Sample size must be between 1 and the repository count")
    selected = random.Random(seed).sample(records, count)
    return sorted(selected, key=lambda row: row["url"].casefold())


def predict_batch(
    records: list[dict[str, Any]],
    output: Path,
    modes: tuple[str, ...] = MODES,
    replay_run: Path | None = None,
    progress: Callable[[dict[str, Any]], None] | None = None,
    max_bytes: int = 250_000,
    root: Path | None = None,
    input_provenance: dict[str, Any] | None = None,
    reference: dict[str, dict[str, int]] | None = None,
    transport: str = "api",
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("Batch output must be a new directory")
    if not records or any(mode not in MODES for mode in modes):
        raise ValueError("Supply repositories and valid prediction modes")
    if transport not in {"api", "git"}:
        raise ValueError("Transport must be api or git")
    started_at = datetime.now(timezone.utc).isoformat()
    root = root or Path.cwd()
    output.mkdir(parents=True)
    results = []
    predictions = []
    evidence: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    errors = []
    inventory = []
    _, catalog_hash = load_rules()
    for index, record in enumerate(records):
        url = record["url"]
        snapshot_relative = f"snapshots/{index + 1:04d}"
        snapshot = output / snapshot_relative
        if progress:
            progress({"completed": index, "total": len(records), "current_repository": url})
        try:
            if replay_run:
                original_snapshot = contained(replay_run, record["snapshot"])
                manifest, _ = replay(original_snapshot, record["snapshot_sha256"])
                shutil.copytree(original_snapshot, snapshot)
            else:
                acquire_fn = acquire_git if transport == "git" else acquire
                manifest = acquire_fn(url, snapshot, ref=record.get("ref"), max_bytes=max_bytes)
            snapshot_hash = sha256((snapshot / "manifest.json").read_bytes())
            analyzed = [analyze(snapshot, mode, expected_hash=snapshot_hash) for mode in modes]
            results.append(
                {
                    "repository": manifest["repository"],
                    "source_url": manifest["source_url"],
                    "commit": manifest["commit"],
                    "modes": analyzed,
                }
            )
            inventory.append(
                {
                    **record,
                    "url": manifest["source_url"],
                    "commit": manifest["commit"],
                    "snapshot": snapshot_relative,
                    "snapshot_sha256": snapshot_hash,
                    "status": "analyzed",
                }
            )
            for result in analyzed:
                for stage in STAGES:
                    predictions.append(
                        {
                            "repository": result["repository"],
                            "commit": result["commit"],
                            "mode": result["mode"],
                            "stage": stage,
                            "prediction": (
                                int(stage in result["labels"])
                                if stage in result["labels"] or result["scan_complete"]
                                else ""
                            ),
                            "scan_complete": result["scan_complete"],
                        }
                    )
                evidence.extend({"mode": result["mode"], **item} for item in result["evidence"])
                excluded.extend(
                    {"mode": result["mode"], **item} for item in result["excluded_evidence"]
                )
                if not result["scan_complete"]:
                    allowed = (
                        {"documentation"}
                        if result["mode"] == MODES[0]
                        else {"code"}
                        if result["mode"] == MODES[1]
                        else {"documentation", "code"}
                    )
                    for item in manifest["files"]:
                        if item["source"] in allowed and item["status"] == "unavailable":
                            errors.append(
                                {
                                    "repository": result["repository"],
                                    "mode": result["mode"],
                                    "path": item["path"],
                                    "reason": item["reason"],
                                    "detail": "unavailable-artifact",
                                }
                            )
                    for item in result["analysis_errors"]:
                        errors.append(
                            {
                                "repository": result["repository"],
                                "mode": result["mode"],
                                "path": item["path"],
                                "reason": item["reason"],
                                "detail": "analysis-error",
                            }
                        )
        except Exception as exc:
            reason = type(exc).__name__
            detail = str(getattr(exc, "code", ""))
            results.append(
                {
                    "repository": repository_id(url),
                    "source_url": url,
                    "error": f"{reason}{': ' + detail if detail else ''}",
                    "modes": [],
                }
            )
            inventory.append({**record, "status": "failed", "reason": reason})
            errors.append(
                {
                    "repository": repository_id(url),
                    "mode": "",
                    "path": "",
                    "reason": reason,
                    "detail": detail,
                }
            )
        if progress:
            progress({"completed": index + 1, "total": len(records), "current_repository": url})
    for row, original in zip(results, records, strict=True):
        row["human_labels"] = (reference or {}).get(repository_id(original["url"]).casefold())
    write_csv(
        output / "predictions.csv",
        ["repository", "commit", "mode", "stage", "prediction", "scan_complete"],
        predictions,
    )
    write_csv(output / "errors.csv", ["repository", "mode", "path", "reason", "detail"], errors)
    (output / "evidence.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in evidence),
        encoding="utf-8",
    )
    (output / "excluded_evidence.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in excluded),
        encoding="utf-8",
    )
    counts = [
        {
            "repository": row["repository"],
            "commit": row.get("commit", ""),
            "mode": m["mode"],
            "stage": stage,
            **m["evidence_counts"][stage],
        }
        for row in results
        for m in row["modes"]
        for stage in STAGES
    ]
    write_csv(
        output / "evidence_counts.csv",
        ["repository", "commit", "mode", "stage", "documentation", "code", "overall"],
        counts,
    )
    payload = {
        "repositories": results,
        "repository_count": len(records),
        "analyzed_count": sum(bool(row["modes"]) for row in results),
        "purpose": "heuristic predictions; no human labels or performance metrics used",
    }
    write_json(output / "results.json", payload)
    write_json(
        output / "manifest.json",
        {
            "schema_version": 1,
            "purpose": "batch-prediction",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "transport": transport,
            "repositories": inventory,
            "modes": list(modes),
            "rule_catalog_hash": catalog_hash,
            "classifier": git_state(root),
            "classifier_source_sha256": implementation_hash(root),
            "input_hash": sha256(json_bytes(records)),
            "replay": replay_run is not None,
            "max_bytes": max_bytes,
            "input_provenance": input_provenance or {},
        },
    )
    return payload
