"""Local research UI; background jobs reuse the classifier and benchmark commands."""

import base64
import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

from . import MODES, STAGES
from .batch import predict_batch, read_inputs, records_from_rows, sample_records
from .benchmark import run
from .canonical import contained, json_bytes, read_json, sha256, write_json
from .consensus import worksheet_cells
from .reference import final_reference
from .dataset import dataset_reference, DEFAULT_DATASET, execute_dataset, dataset_results


class Application:
    def __init__(self, root: Path, state_dir: Path):
        self.root = root.resolve()
        self.state_dir = state_dir.resolve()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.jobs: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=2)

    def start(self, request: dict[str, Any]) -> dict[str, str]:
        kind = request.get("kind", "repository")
        if kind not in {"repository", "batch", "evaluation", "replay", "dataset"}:
            raise ValueError("Unknown job type")
        mode = request.get("mode", "documentation-only")
        if mode not in (*MODES, "all"):
            raise ValueError("Unknown evidence mode")
        modes = MODES if mode == "all" else (mode,)
        transport = request.get("transport", "api")
        if transport not in {"api", "git"}:
            raise ValueError("Unknown acquisition transport")
        job_id = uuid.uuid4().hex
        directory = self.state_dir / "runs" / job_id
        provenance: dict[str, Any] = {"kind": kind}
        reference = None
        if kind == "repository":
            records = records_from_rows(
                [{"repository_url": request["url"], "ref": request.get("ref")}]
            )
        elif kind == "batch":
            if request.get("upload_id"):
                upload = contained(self.state_dir / "uploads", request["upload_id"])
                selected_sheet = request.get("worksheet") or "final_agreement"
                records = read_inputs(
                    upload,
                    request.get("repository_column", "A"),
                    selected_sheet,
                    int(request.get("header_row", 1)),
                )
                if upload.suffix == ".xlsx" and selected_sheet == "final_agreement":
                    reference = final_reference(upload)
                elif upload.suffix == ".json":
                    data = read_json(upload)
                    if isinstance(data, dict) and data.get("kind") == "lifecycle-benchmark-dataset":
                        reference = dataset_reference(data)
                provenance.update(
                    source_sha256=sha256(upload.read_bytes()),
                    worksheet=selected_sheet,
                    repository_column=request.get("repository_column", "A"),
                    header_row=int(request.get("header_row", 1)),
                )
            else:
                records = records_from_rows(
                    [
                        {"repository_url": value}
                        for value in request.get("urls", "").splitlines()
                        if value.strip()
                    ]
                )
            provenance.update(
                population_count=len(records),
                seed=str(request.get("seed", "rlm-ui-v1")),
                requested_sample_size=request.get("sample_size"),
            )
            records = sample_records(
                records,
                int(request["sample_size"]) if request.get("sample_size") else None,
                str(request.get("seed", "rlm-ui-v1")),
            )
        elif kind == "dataset":
            dataset_path = self.root / DEFAULT_DATASET
            records = read_inputs(dataset_path)
        elif kind == "replay":
            original = contained(self.state_dir / "runs", request["run_id"])
            manifest = read_json(original / "manifest.json")
            records = [row for row in manifest["repositories"] if row["status"] == "analyzed"]
            if not records:
                raise ValueError("This run has no captured repositories to replay")
            prior = read_json(original / "results.json")
            reference = {
                r["repository"].casefold(): r["human_labels"]
                for r in prior["repositories"]
                if r.get("human_labels")
            }
        else:
            configuration = contained(self.root, request.get("config", "configs/benchmark.yaml"))
            if not configuration.is_file():
                raise ValueError("Benchmark configuration file does not exist")
            records = []
        job = {
            "id": job_id,
            "kind": kind,
            "status": "queued",
            "completed": 0,
            "total": len(records),
            "current_repository": "",
            "result": None,
            "error": None,
        }
        with self.lock:
            self.jobs[job_id] = job

        def progress(value: dict[str, Any]) -> None:
            with self.lock:
                self.jobs[job_id].update(value)

        def execute() -> None:
            progress({"status": "running"})
            try:
                if kind == "dataset":
                    execute_dataset(dataset_path, directory, transport, modes, progress)
                    result = read_json(directory / "results.json")
                elif kind == "evaluation":
                    run(configuration, directory)
                    result = {"metrics": read_json(directory / "metrics.json"), "repositories": []}
                else:
                    result = predict_batch(
                        records,
                        directory,
                        modes,
                        original if kind == "replay" else None,
                        progress,
                        root=self.root,
                        input_provenance=provenance,
                        reference=reference,
                        transport=transport,
                    )
                progress({"status": "completed", "result": result})
            except Exception as exc:
                progress({"status": "failed", "error": str(exc)})

        self.pool.submit(execute)
        return {"id": job_id}

    def job(self, job_id: str) -> dict[str, Any]:
        with self.lock:
            if job_id in self.jobs:
                return dict(self.jobs[job_id])
        root = contained(self.state_dir / "runs", job_id)
        if (root / "results.json").is_file():
            return {
                "id": job_id,
                "kind": "batch",
                "status": "completed",
                "result": read_json(root / "results.json"),
            }
        raise ValueError("Run not found")

    def history(self) -> list[dict[str, Any]]:
        with self.lock:
            rows = [
                {key: job.get(key) for key in ["id", "kind", "status", "completed", "total"]}
                for job in self.jobs.values()
            ]
        known = {row["id"] for row in rows}
        directory = self.state_dir / "runs"
        if directory.exists():
            for root in sorted(directory.iterdir()):
                if root.name not in known and (root / "results.json").is_file():
                    result = read_json(root / "results.json")
                    rows.append(
                        {
                            "id": root.name,
                            "kind": "batch",
                            "status": "completed",
                            "completed": result["repository_count"],
                            "total": result["repository_count"],
                        }
                    )
        return rows

    def import_results(self, request: dict[str, Any]) -> dict[str, str]:
        result = request.get("result")
        if isinstance(result, dict) and result.get("kind") == "lifecycle-benchmark-dataset":
            result = dataset_results(result)
        if not isinstance(result, dict) or not isinstance(result.get("repositories"), list):
            raise ValueError("Choose an exported results.json")
        for row in result["repositories"]:
            if not isinstance(row, dict) or not isinstance(row.get("repository"), str):
                raise ValueError("Invalid repository result")
            if not isinstance(row.get("modes"), list):
                raise ValueError("Invalid result modes")
            for mode in row["modes"]:
                if mode.get("mode") not in MODES or not isinstance(mode.get("evidence"), list):
                    raise ValueError("Invalid evidence result")
                if not isinstance(mode.get("labels"), list) or any(
                    s not in STAGES for s in mode["labels"]
                ):
                    raise ValueError("Invalid predicted labels")
                for evidence in mode["evidence"]:
                    if (
                        not isinstance(evidence, dict)
                        or evidence.get("stage") not in STAGES
                        or evidence.get("source") not in {"documentation", "code"}
                        or any(type(evidence.get(k)) is not int for k in ("start_line", "end_line"))
                        or not 1 <= evidence["start_line"] <= evidence["end_line"]
                        or any(
                            not isinstance(evidence.get(k), str)
                            for k in ("path", "excerpt", "url", "rule_id")
                        )
                    ):
                        raise ValueError("Invalid evidence occurrence")
            human = row.get("human_labels")
            if human is not None and (
                not isinstance(human, dict)
                or set(human) != set(STAGES)
                or any(type(v) is not int or v not in (0, 1) for v in human.values())
            ):
                raise ValueError("Invalid human labels")
        job_id = uuid.uuid4().hex
        directory = self.state_dir / "runs" / job_id
        directory.mkdir(parents=True)
        write_json(
            directory / "results.json",
            {**result, "imported": True, "repository_count": len(result["repositories"])},
        )
        return {"id": job_id}

    def upload(self, request: dict[str, Any]) -> dict[str, Any]:
        suffix = Path(request["filename"]).suffix.lower()
        if suffix not in {".xlsx", ".csv", ".json", ".txt"}:
            raise ValueError("Upload an Excel workbook, CSV, JSON or URL text file")
        data = base64.b64decode(request["content"], validate=True)
        if len(data) > 15_000_000:
            raise ValueError("Upload exceeds 15 MB")
        upload_id = uuid.uuid4().hex + suffix
        target = contained(self.state_dir / "uploads", upload_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        preview: dict[str, Any] = {"upload_id": upload_id, "filename": request["filename"]}
        if suffix == ".xlsx":
            sheet = request.get("worksheet", "final_agreement")
            try:
                rows = worksheet_cells(target, sheet)
            except ValueError:
                sheet = "Agreement Final"
                rows = worksheet_cells(target, sheet)
            preview["worksheet"] = sheet
            preview["repository_column"] = "A" if sheet == "final_agreement" else "B"
            if sheet == "final_agreement":
                labels = final_reference(target)
                preview["reference_count"] = len(labels)
            preview["preview_rows"] = [
                {"row": number, "cells": cells} for number, cells in sorted(rows.items())[:5]
            ]
        else:
            preview["repository_count"] = len(read_inputs(target))
        return preview


def make_server(app: Application, port: int = 8000) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            pass

        def send(self, status: int, data: bytes, content_type: str = "application/json") -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            try:
                if path == "/":
                    self.send(
                        200,
                        Path(__file__).with_name("ui").joinpath("index.html").read_bytes(),
                        "text/html; charset=utf-8",
                    )
                elif path == "/api/history":
                    self.send(200, json_bytes(app.history()))
                elif path.startswith("/api/jobs/"):
                    self.send(200, json_bytes(app.job(path.removeprefix("/api/jobs/"))))
                elif path.startswith("/api/download/"):
                    relative = path.removeprefix("/api/download/")
                    target = contained(app.state_dir / "runs", relative)
                    if target.name not in {
                        "predictions.csv",
                        "evidence.jsonl",
                        "excluded_evidence.jsonl",
                        "evidence_counts.csv",
                        "errors.csv",
                        "results.json",
                        "manifest.json",
                        "metrics.json",
                        "metrics.csv",
                        "report.md",
                        "documentation_errors.csv",
                        "coverage.csv",
                        "mode_comparison.csv",
                    }:
                        raise ValueError("Download is not an exported result file")
                    self.send(200, target.read_bytes(), "application/octet-stream")
                else:
                    self.send(404, json_bytes({"error": "Not found"}))
            except (ValueError, OSError) as exc:
                self.send(400, json_bytes({"error": str(exc)}))

        def do_POST(self) -> None:
            try:
                origin = self.headers.get("Origin")
                if origin and origin not in {
                    f"http://127.0.0.1:{cast(ThreadingHTTPServer, self.server).server_port}",
                    f"http://localhost:{cast(ThreadingHTTPServer, self.server).server_port}",
                }:
                    raise ValueError("Cross-origin requests are not permitted")
                size = int(self.headers.get("Content-Length", 0))
                if not 0 < size <= 21_000_000:
                    raise ValueError("Invalid request size")
                request = json.loads(self.rfile.read(size))
                if not isinstance(request, dict):
                    raise ValueError("Request must be a JSON object")
                if self.path == "/api/jobs":
                    result = app.start(request)
                elif self.path == "/api/import-results":
                    result = app.import_results(request)
                elif self.path == "/api/uploads":
                    result = app.upload(request)
                else:
                    raise ValueError("Unknown endpoint")
                self.send(200, json_bytes(result))
            except Exception as exc:
                self.send(400, json_bytes({"error": str(exc)}))

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(root: Path, state_dir: Path, port: int = 8000) -> None:
    app = Application(root, state_dir)
    server = make_server(app, port)
    print(f"Research Lifecycle Mapper UI: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.pool.shutdown(wait=True)
