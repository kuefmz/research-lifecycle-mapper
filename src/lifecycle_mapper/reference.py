"""Strict reference-label reading, independent from prediction feature inputs."""

import csv
from pathlib import Path
from typing import Any

from . import STAGES
from .acquisition import repository_id
from .workbook import worksheet_cells
from .batch import normalize_url


def final_reference(path: Path) -> dict[str, dict[str, int]]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as stream:
            table = list(csv.reader(stream))
        if any(len(row) != 7 for row in table if any(value.strip() for value in row)):
            raise ValueError("Final agreement CSV requires exactly seven columns")
        rows = {
            number: {chr(65 + i): value for i, value in enumerate(row)}
            for number, row in enumerate(table, 1)
        }
    else:
        rows = worksheet_cells(path, "final_agreement")
    headers = {"A": "GitHub URL", **{chr(66 + i): s for i, s in enumerate(STAGES)}}
    if any(rows.get(1, {}).get(c) != title for c, title in headers.items()):
        raise ValueError("final_agreement headers must be GitHub URL and the six stage names")
    labels: dict[str, dict[str, int]] = {}
    for number, cells in sorted(rows.items()):
        if number == 1 or not any(cells.get(c, "").strip() for c in headers):
            continue
        key = repository_id(cells.get("A", "")).casefold()
        if key in labels:
            raise ValueError("Duplicate repository in final_agreement")
        values = [cells.get(chr(66 + i), "").strip() for i in range(6)]
        if any(v not in {"0", "1", "0.0", "1.0"} for v in values):
            raise ValueError(f"Missing or nonbinary reference label at worksheet row {number}")
        labels[key] = {s: int(float(v)) for s, v in zip(STAGES, values, strict=True)}
    if not labels:
        raise ValueError("Empty final_agreement")
    return labels


def describe_reference(labels: dict[str, dict[str, int]]) -> dict[str, Any]:
    n = len(labels)
    return {
        "repository_count": n,
        "binary_label_count": n * 6,
        "stages": {
            s: {
                "positive": sum(r[s] for r in labels.values()),
                "negative": sum(1 - r[s] for r in labels.values()),
                "prevalence": sum(r[s] for r in labels.values()) / n,
            }
            for s in STAGES
        },
        "cooccurrence": {
            s: {t: sum(r[s] * r[t] for r in labels.values()) for t in STAGES} for s in STAGES
        },
        "label_cardinality": sum(sum(r.values()) for r in labels.values()) / n,
        "all_six_positive": sum(all(r.values()) for r in labels.values()),
        "all_six_negative": sum(not any(r.values()) for r in labels.values()),
    }


def audit_workbook(path: Path, annotator_sheets: tuple[str, str]) -> dict[str, Any]:
    """Compare independent annotations by repository identity, never row position."""
    from .canonical import sha256

    labels = final_reference(path)
    result = describe_reference(labels)
    result.update(
        workbook_sha256=sha256(path.read_bytes()),
        worksheet="final_agreement",
        repository_column="A",
        stage_columns={s: chr(66 + i) for i, s in enumerate(STAGES)},
    )
    annotations = []
    for sheet in annotator_sheets:
        cells = worksheet_cells(path, sheet)
        if any(cells.get(1, {}).get(chr(66 + i)) != stage for i, stage in enumerate(STAGES)):
            raise ValueError("Independent annotator stage headers differ")
        rows: dict[str, dict[str, Any]] = {}
        for number, row in cells.items():
            if number <= 1 or not row.get("A", "").strip():
                continue
            repo = repository_id(row["A"]).casefold()
            if repo in rows:
                raise ValueError("Duplicate independent annotation repository")
            rows[repo] = {"row": number, "cells": row}
        if set(rows) != set(labels):
            raise ValueError("Independent annotation repositories differ from reference")
        annotations.append(rows)
    counts: dict[str, dict[str, Any]] = {}
    missing = []
    for i, stage in enumerate(STAGES):
        column = chr(66 + i)
        agreement = disagreement = valid = 0
        first_positive = second_positive = 0
        for repo in labels:
            values = [a[repo]["cells"].get(column, "").strip() for a in annotations]
            if any(v not in {"0", "1", "0.0", "1.0"} for v in values):
                missing.append(
                    {
                        "repository": repo,
                        "stage": stage,
                        "column": column,
                        "values": values,
                        "rows": [a[repo]["row"] for a in annotations],
                    }
                )
                continue
            valid += 1
            first_positive += int(float(values[0]))
            second_positive += int(float(values[1]))
            if float(values[0]) == float(values[1]):
                agreement += 1
            else:
                disagreement += 1
        expected_agreement = (
            (
                (
                    first_positive * second_positive
                    + (valid - first_positive) * (valid - second_positive)
                )
                / valid**2
            )
            if valid
            else 1.0
        )
        kappa = (
            ((agreement / valid - expected_agreement) / (1 - expected_agreement))
            if valid and expected_agreement != 1
            else None
        )
        counts[stage] = {
            "valid_pairs": valid,
            "agreement": agreement,
            "disagreement": disagreement,
            "missing_pairs": len(labels) - valid,
            "cohen_kappa_valid_pairs": kappa,
        }
    result.update(
        annotator_sheets=list(annotator_sheets),
        independent_annotations=counts,
        missing_annotation_pairs=missing,
        valid_pairs=sum(r["valid_pairs"] for r in counts.values()),
        binary_disagreements=sum(r["disagreement"] for r in counts.values()),
        agreements=sum(r["agreement"] for r in counts.values()),
    )
    return result


def dataset_reference(payload: dict[str, Any]) -> dict[str, dict[str, int]]:
    if (
        payload.get("kind") != "lifecycle-benchmark-dataset"
        or payload.get("schema_version") != 1
        or payload.get("stages") != list(STAGES)
    ):
        raise ValueError("Unsupported benchmark dataset schema")
    read_inputs_payload(payload)
    labels = {}
    for row in payload["repositories"]:
        key = normalize_url(row["source_url"]).removeprefix("https://github.com/").casefold()
        human = row.get("human_labels")
        if (
            not isinstance(human, dict)
            or set(human) != set(STAGES)
            or any(type(v) is not int or v not in (0, 1) for v in human.values())
        ):
            raise ValueError("Dataset requires six literal binary human labels per repository")
        if not isinstance(row.get("results"), dict):
            raise ValueError("Dataset results must be a run-ID mapping")
        labels[key] = human
    if not isinstance(payload.get("runs"), list):
        raise ValueError("Dataset requires run history")
    return labels


def read_inputs_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    from .batch import records_from_rows

    rows = payload.get("repositories")
    if not isinstance(rows, list):
        raise ValueError("Dataset repositories must be a list")
    records = records_from_rows(rows)
    if len(records) != len(rows):
        raise ValueError("Duplicate repository in benchmark dataset")
    return records
