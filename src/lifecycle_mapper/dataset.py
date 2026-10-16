"""Versioned benchmark JSON with atomic, checkpointed run history.

Reference labels are metadata, never classifier inputs. Snapshots remain in run
folders; each JSON result links them and embeds the complete evidence payload.
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import MODES, STAGES
from .analysis import load_rules
from .batch import predict_batch, read_inputs, normalize_url
from .benchmark import git_state, implementation_hash
from .canonical import json_bytes, read_json, sha256
from .reference import final_reference

DEFAULT_DATASET = Path("data/research_lifecycle_benchmark_100_msr27.json")


def convert_workbook(source: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise ValueError("Dataset output already exists")
    labels = final_reference(source)
    records = read_inputs(source, "A", "final_agreement", 1)
    payload = {
        "schema_version": 1,
        "kind": "lifecycle-benchmark-dataset",
        "stages": list(STAGES),
        "source": {
            "file": source.name,
            "sha256": sha256(source.read_bytes()),
            "worksheet": "final_agreement",
            "repository_column": "A",
            "stage_columns": {s: chr(66 + i) for i, s in enumerate(STAGES)},
        },
        "repositories": [
            {
                "repository": r["url"].removeprefix("https://github.com/"),
                "source_url": r["url"],
                "human_labels": labels[r["url"].removeprefix("https://github.com/").casefold()],
                "worksheet_row": r["source_rows"][0],
                "results": {},
            }
            for r in records
        ],
        "runs": [],
    }
    atomic_write(output, payload)
    return payload


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(json_bytes(payload))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


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


def execute_dataset(
    path: Path = DEFAULT_DATASET,
    output: Path | None = None,
    transport: str = "api",
    modes: tuple[str, ...] = MODES,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    lock = path.with_suffix(path.suffix + ".lock")
    try:
        with lock.open("x") as stream:
            stream.write(str(os.getpid()))
    except FileExistsError:
        raise ValueError("Dataset is locked by another run; inspect its .lock file") from None
    payload = None
    run: dict[str, Any] | None = None
    try:
        payload = read_json(path)
        reference = dataset_reference(payload)
        records = read_inputs_payload(payload)
        run_id = uuid.uuid4().hex
        output = (output or Path("local/benchmark-runs") / run_id).resolve()
        if output.exists():
            raise ValueError("Run output must be a new directory")
        root = Path.cwd()
        run = {
            "id": run_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "input_sha256": sha256(path.read_bytes()),
            "modes": list(modes),
            "transport": transport,
            "rule_catalog_hash": load_rules()[1],
            "classifier": git_state(root),
            "classifier_source_sha256": implementation_hash(root),
            "output_directory": os.path.relpath(output, path.resolve().parent),
            "completed": 0,
        }
        payload["runs"].append(run)
        atomic_write(path, payload)
        by_url = {
            normalize_url(row["source_url"]).casefold(): row for row in payload["repositories"]
        }

        def checkpoint(result: dict[str, Any], inventory: dict[str, Any]) -> None:
            assert run is not None and payload is not None
            # Match the requested URL even if GitHub redirects to another canonical URL.
            original = records[run["completed"]]["url"]
            row = by_url[original.casefold()]
            row["results"][run_id] = {
                "status": "failed"
                if result.get("error")
                else "partial"
                if any(not m["scan_complete"] for m in result["modes"])
                else "analyzed",
                "analysis": {**result, "human_labels": row["human_labels"]},
                "acquisition": inventory,
            }
            run["completed"] += 1
            atomic_write(path, payload)

        predict_batch(
            records,
            output,
            modes,
            root=root,
            reference=reference,
            transport=transport,
            input_provenance={
                "dataset": path.name,
                "dataset_sha256": run["input_sha256"],
                "dataset_run_id": run_id,
            },
            on_result=checkpoint,
            progress=progress,
        )
        run.update(status="completed", finished_at=datetime.now(timezone.utc).isoformat())
        atomic_write(path, payload)
        return {
            "dataset": str(path),
            "run_id": run_id,
            "output_directory": str(output),
            "completed": run["completed"],
        }
    except Exception as exc:
        if payload is not None and run is not None:
            run.update(
                status="failed",
                error=type(exc).__name__,
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
            atomic_write(path, payload)
        raise
    finally:
        lock.unlink(missing_ok=True)


def dataset_results(payload: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    """Project one saved run into the existing read-only result-review schema."""
    dataset_reference(payload)
    if not payload["runs"]:
        raise ValueError("This dataset has no saved runs; execute the benchmark first")
    chosen = run_id or payload["runs"][-1]["id"]
    if not any(run["id"] == chosen for run in payload["runs"]):
        raise ValueError("Dataset run not found")
    repositories = []
    for row in payload["repositories"]:
        saved = row["results"].get(chosen)
        repositories.append(
            saved["analysis"]
            if saved
            else {
                "repository": row["repository"],
                "source_url": row["source_url"],
                "human_labels": row["human_labels"],
                "modes": [],
                "error": "not-analyzed-in-this-run",
            }
        )
    return {
        "repositories": repositories,
        "repository_count": len(repositories),
        "dataset_run_id": chosen,
        "purpose": "saved benchmark dataset review",
    }
