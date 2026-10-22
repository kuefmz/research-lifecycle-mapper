"""Killable repository subprocesses with an end-to-end wall-clock deadline."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .canonical import json_bytes, read_json, sha256
from .openaire import file_hash

REPOSITORY_TIMEOUT_SECONDS = 120


def worker_process(
    command: list[str], directory: Path, timeout: float = REPOSITORY_TIMEOUT_SECONDS
) -> dict[str, Any]:
    """Kill the entire POSIX process group, including Git, on deadline or interruption."""
    started = time.monotonic()
    with (directory / "worker.log").open("a") as log:
        process = subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True)
        timed_out = False
        try:
            process.wait(timeout=max(0.0, timeout - (time.monotonic() - started)))
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            if timed_out or process.poll() is None or process.returncode != 0:
                if os.name == "posix":
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    process.kill()
                process.wait()
    heartbeat = directory / "heartbeat.json"
    return {
        "timed_out": timed_out,
        "worker_exit_code": process.returncode,
        "elapsed_seconds": time.monotonic() - started,
        "diagnostics": read_json(heartbeat) if heartbeat.exists() else {"phase": "starting"},
    }


def run_guarded_repository(
    record: dict[str, Any],
    output: Path,
    modes: tuple[str, ...],
    transport: str,
    max_bytes: int,
    api: Any,
    retry_failed: bool,
    rules_dir: Path | None = None,
) -> dict[str, Any]:
    from .corpus import atomic_json

    key = sha256(json_bytes([record["url"].casefold(), "main-then-master-v1"]))
    directory = output / "repositories" / key
    directory.mkdir(parents=True, exist_ok=True)
    result_path = directory / "result.json"
    if result_path.exists():
        if file_hash(result_path) != (directory / "result.sha256").read_text().strip():
            raise ValueError("Checkpoint checksum mismatch")
        saved = read_json(result_path)
        if not retry_failed or saved.get("complete"):
            return {**saved, "checkpoint_reused": True}
    heartbeat = directory / "heartbeat.json"
    heartbeat.unlink(missing_ok=True)
    job = {
        "record": record,
        "output": str(output.resolve()),
        "modes": list(modes),
        "transport": transport,
        "max_bytes": max_bytes,
        "api_interval": api.interval,
        "retry_failed": retry_failed,
        "rules_dir": str(rules_dir.resolve()) if rules_dir else None,
        "heartbeat": str(heartbeat.resolve()),
    }
    job_path = directory / "worker-job.json"
    atomic_json(job_path, job)
    try:
        outcome = worker_process(
            [sys.executable, "-m", "lifecycle_mapper.repository_worker", str(job_path.resolve())],
            directory,
            REPOSITORY_TIMEOUT_SECONDS,
        )
    finally:
        # Absolute local paths are needed only to launch the worker; do not retain them.
        job_path.unlink(missing_ok=True)
    if not outcome["timed_out"] and outcome["worker_exit_code"] == 0:
        if file_hash(result_path) != (directory / "result.sha256").read_text().strip():
            raise ValueError("Checkpoint checksum mismatch")
        result = read_json(result_path)
        if result.get("error"):
            atomic_json(directory / "stop.json", result)
        return result
    state = outcome["diagnostics"]
    error = "repository-timeout" if outcome["timed_out"] else "worker-process-failed"
    result = {
        "requested_url": record["url"],
        "requested_ref": "main",
        "complete": False,
        "modes": [],
        "error": error,
        "stop_reason": error,
        "timeout_seconds": REPOSITORY_TIMEOUT_SECONDS,
        **outcome,
        "captured_bytes": state.get("captured_bytes", 0),
        "api_calls": state.get("api_calls", 0),
        "rate_limit_wait_seconds": state.get("rate_limit_wait_seconds", 0),
    }
    atomic_json(directory / "stop.json", result)
    atomic_json(result_path, result)
    (directory / "result.sha256").write_text(file_hash(result_path) + "\n")
    return result
