"""Bounded, resumable corpus execution using the existing frozen classifier."""

import argparse
import csv
import json
import os
import sys
import threading
import time
import traceback
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

from . import MODES, STAGES
from . import acquisition
from .analysis import analyze_modes, load_rules
from .batch import read_inputs
from .benchmark import git_state, implementation_hash
from .canonical import json_bytes, read_json, sha256
from .git_acquisition import acquire_git
from .openaire import file_hash
from .execution import run_guarded_repository, REPOSITORY_TIMEOUT_SECONDS
from .telemetry import emit, current_state


def atomic_json(path: Path, payload: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(json_bytes(payload))
    temporary.replace(path)


def repository_log(result: dict[str, Any], totals: dict[str, Any], modes: tuple[str, ...]) -> str:
    """One flushed block per result; missing evidence is unknown, never zero."""
    status = "failed" if result.get("error") else "complete" if result["complete"] else "partial"
    lines = [
        f"[{totals['finished']}/{totals['repository_count']}] {result['requested_url']} | {status}"
        + (" | cached checkpoint" if result.get("checkpoint_reused") else ""),
        "  stages: " + " | ".join(STAGES),
    ]
    payloads = {payload["mode"]: payload for payload in result.get("modes", [])}
    for mode in modes:
        payload = payloads.get(mode)
        values = []
        for stage in STAGES:
            value = payload["predictions"].get(stage) if payload else None
            values.append("1" if value is True else "0" if value is False else "?")
        scan = "complete" if payload and payload["scan_complete"] else "incomplete"
        lines.append(f"  {mode}: " + " | ".join(values) + f"  (scan {scan})")
    if result.get("error"):
        lines.append("  error: " + result["error"])
        if result.get("error_location"):
            location = result["error_location"][-1]
            lines.append(
                f"  error location: {location['module']}:{location['line']} ({location['function']})"
            )
    if result.get("coverage_issues"):
        from collections import Counter

        reasons = Counter(issue["reason"] for issue in result["coverage_issues"])
        lines.append(
            "  coverage issues: "
            + ", ".join(f"{key}={value}" for key, value in sorted(reasons.items()))
        )
    if result.get("diagnostics"):
        state = result["diagnostics"]
        lines.append(
            f"  stop diagnostics: phase={state.get('phase', 'unknown')}"
            f" files={state.get('files_attempted', 0)}/{state.get('eligible_files', '?')}"
            f" bytes={state.get('captured_bytes', 0)}"
            f" largest_file_bytes={state.get('largest_eligible_file_bytes', 0)}"
            f" current_file={state.get('current_file', '')}"
            f" last_error={state.get('last_error', '')}"
        )
    lines.append(
        f"  totals: complete={totals['complete']} partial={totals['partial']} failed={totals['failed']}"
        + f" | repo={result.get('elapsed_seconds', 0):.1f}s"
        + f" | REST calls={result.get('api_calls', 0)}"
    )
    return "\n".join(lines)


class PacedAPI:
    """Serialize a worker's REST traffic and honor server cooldowns."""

    def __init__(self, interval: float = 0.8):
        self.interval = interval
        self.lock = threading.RLock()
        self.next_request = 0.0
        self.local = threading.local()
        self.network_calls = 0
        self.rate_limit_wait_seconds = 0.0
        self.rate_limit_until = 0.0

    def requested(self) -> None:
        self.wait_gate()
        self.next_request = time.monotonic() + self.interval
        self.network_calls += 1
        self.local.calls = getattr(self.local, "calls", 0) + 1
        emit(phase="rest-request", api_calls=self.network_calls)

    def wait_gate(self) -> None:
        while (delay := self.next_request - time.monotonic()) > 0:
            chunk = min(60.0, delay)
            self.rate_limit_wait_seconds += max(
                0.0, min(chunk, self.rate_limit_until - time.monotonic())
            )
            time.sleep(chunk)
            emit(rate_limit_wait_seconds=self.rate_limit_wait_seconds)

    def response(self, headers: Any) -> None:
        if headers.get("X-RateLimit-Remaining") == "0":
            try:
                delay = max(1.0, float(headers.get("X-RateLimit-Reset")) - time.time() + 2)
            except (TypeError, ValueError):
                delay = 60.0
            self.cooldown(delay, "primary quota exhausted")

    def cooldown(self, delay: float, reason: str) -> None:
        self.next_request = max(self.next_request, time.monotonic() + delay)
        self.rate_limit_until = max(self.rate_limit_until, time.monotonic() + delay)
        emit(phase="rate-limit-wait", pending_wait_seconds=delay, wait_reason=reason)
        print(
            f"GitHub: {reason}; waiting at least {delay:.0f}s before the next REST request.",
            file=sys.stderr,
            flush=True,
        )

    def __call__(self, endpoint: str) -> Any:
        secondary_attempt = 0
        while True:
            # Hold the gate through response handling so another worker cannot
            # issue a request between quota exhaustion and its cooldown update.
            with self.lock:
                self.wait_gate()
                try:
                    return acquisition.api_get(
                        endpoint, on_response=self.response, on_request=self.requested
                    )
                except acquisition.GitHubAPIError as exc:
                    if exc.code != "rate-limit":
                        raise
                    try:
                        reset_delay = (
                            max(1.0, float(exc.reset) - time.time() + 2) if exc.reset else 0.0
                        )
                        retry_delay = float(exc.retry_after) if exc.retry_after else 0.0
                    except ValueError:
                        reset_delay, retry_delay = 0.0, 0.0
                    if not exc.reset:
                        secondary_attempt += 1
                        if secondary_attempt > 5:
                            raise
                    delay = max(
                        reset_delay,
                        retry_delay,
                        60.0 * 2 ** max(0, secondary_attempt - 1) if not exc.reset else 0.0,
                    )
                    self.cooldown(delay, "rate limit")


def selected_records(
    input_path: Path, sample: int | None, seed: str, shard_index: int, shard_count: int
) -> list[dict[str, Any]]:
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("Require 0 <= shard-index < shard-count")
    records = read_inputs(input_path)
    if any(row.get("ref") not in {None, "", "main"} for row in records):
        raise ValueError(
            "Corpus acquisition uses main, otherwise master; input refs cannot override it"
        )
    records = [{**row, "ref": "main"} for row in records]
    if sample is not None:
        if not 1 <= sample <= len(records):
            raise ValueError("Invalid pilot/sample size")
        records = sorted(
            records, key=lambda r: sha256((seed + ":" + r["url"].casefold()).encode())
        )[:sample]
    return [
        row
        for row in records
        if int(sha256(row["url"].casefold().encode()), 16) % shard_count == shard_index
    ]


def run_repository(
    record: dict[str, Any],
    output: Path,
    modes: tuple[str, ...],
    transport: str,
    max_bytes: int,
    api: PacedAPI,
    retry_failed: bool,
    rules_dir: Path | None = None,
) -> dict[str, Any]:
    if record.get("ref") not in {None, "", "main"}:
        raise ValueError("Corpus acquisition uses main, otherwise master")
    record = {**record, "ref": "main"}
    key = sha256(json_bytes([record["url"].casefold(), "main-then-master-v1"]))
    directory = output / "repositories" / key
    directory.mkdir(parents=True, exist_ok=True)
    result_path = directory / "result.json"
    if result_path.exists():
        raw = result_path.read_bytes()
        if file_hash(result_path) != (directory / "result.sha256").read_text().strip():
            raise ValueError("Checkpoint checksum mismatch")
        saved = json.loads(raw)
        if not retry_failed or saved.get("complete"):
            return {**saved, "checkpoint_reused": True}
    started = time.monotonic()
    emit(phase="acquisition", transport=transport)
    api.local.calls = 0
    result: dict[str, Any] = {
        "requested_url": record["url"],
        "requested_ref": record.get("ref"),
        "modes": [],
        "complete": False,
    }
    # Preserve interrupted/failed attempts; reuse a completed acquisition after interruption.
    attempts = sorted(directory.glob("attempt-*"))
    attempt = attempts[-1] if attempts else directory / "attempt-0001"
    if (attempt / "snapshot").exists() and (
        result_path.exists() or not (attempt / "snapshot/manifest.json").exists()
    ):
        attempt = directory / f"attempt-{len(attempts) + 1:04d}"
    attempt.mkdir(exist_ok=True)
    snapshot = attempt / "snapshot"
    try:
        if (snapshot / "manifest.json").exists():
            manifest, _ = acquisition.replay(snapshot)
            if manifest.get("branch_policy") != "main-then-master-v1":
                raise ValueError("Snapshot does not attest the current branch policy")
        elif transport == "git":
            manifest = acquire_git(record["url"], snapshot, record.get("ref"), max_bytes)
        else:
            manifest = acquisition.acquire(
                record["url"],
                snapshot,
                record.get("ref"),
                max_bytes,
                blob_transport="raw" if transport == "hybrid" else "api",
                api_client=api,
                resolve_head_direct=True,
                sources=(
                    ("documentation",)
                    if modes == ("documentation-only",)
                    else ("code",)
                    if modes == ("code-only",)
                    else ("documentation", "code")
                ),
            )
        acquired = time.monotonic()
        emit(phase="integrity-check")
        snapshot_hash = file_hash(snapshot / "manifest.json")
        result.update(
            repository=manifest["repository"],
            commit=manifest["commit"],
            selected_branch=manifest.get("selected_branch"),
            branch_policy=manifest.get("branch_policy"),
            snapshot=str(snapshot.relative_to(output)),
            snapshot_sha256=snapshot_hash,
            inventory_entries=len(manifest["files"]),
            eligible_files=sum(f["source"] is not None for f in manifest["files"]),
            captured_bytes=sum(f["size"] for f in manifest["files"] if f["status"] == "captured"),
            acquisition_seconds=acquired - started,
        )
        # Preserve precisely the existing classifier and its three mode semantics.
        emit(phase="analysis", current_file="")
        result["modes"] = analyze_modes(
            snapshot, modes, expected_hash=snapshot_hash, rules_dir=rules_dir
        )
        result["analysis_seconds"] = time.monotonic() - acquired
        result["complete"] = all(m["scan_complete"] for m in result["modes"])
        issues = [
            {"path": f["path"], "reason": f["reason"]}
            for f in manifest["files"]
            if f["status"] == "unavailable"
        ]
        for mode in result["modes"]:
            issues.extend(mode["analysis_errors"])
        result["coverage_issues"] = list({(i["path"], i["reason"]): i for i in issues}.values())
    except Exception as exc:
        result["error"] = str(getattr(exc, "code", type(exc).__name__))
        result["diagnostics"] = current_state()
        result["error_location"] = [
            {"module": Path(frame.filename).name, "function": frame.name, "line": frame.lineno}
            for frame in traceback.extract_tb(exc.__traceback__)[-6:]
        ]
        if isinstance(exc, OSError):
            result["error_errno"] = exc.errno
            result["error_filename"] = Path(exc.filename).name if exc.filename else None
    result["elapsed_seconds"] = time.monotonic() - started
    result["api_calls"] = getattr(api.local, "calls", 0)
    result["rate_limit_wait_seconds"] = api.rate_limit_wait_seconds
    emit(
        phase="writing-result",
        api_calls=result["api_calls"],
        rate_limit_wait_seconds=api.rate_limit_wait_seconds,
    )
    atomic_json(result_path, result)
    (directory / "result.sha256").write_text(file_hash(result_path) + "\n")
    return result


def run_corpus(
    input_path: Path,
    output: Path,
    transport: str = "hybrid",
    workers: int = 2,
    modes: tuple[str, ...] = MODES,
    sample: int | None = None,
    seed: str = "msr27-pilot-v1",
    shard_index: int = 0,
    shard_count: int = 1,
    max_bytes: int = 0,
    retry_failed: bool = False,
    api_interval: float = 0.8,
    rules_dir: Path | None = None,
    expected_repositories: int | None = None,
) -> dict[str, Any]:
    if workers not in range(1, 9) or max_bytes < 0 or api_interval < 0.8:
        raise ValueError(
            "Use 1..8 workers, max-bytes >= 0 (0 is unlimited) and api-interval >= 0.8"
        )
    if transport not in {"api", "hybrid", "git"} or not modes or any(m not in MODES for m in modes):
        raise ValueError("Invalid transport or modes")
    if transport != "git" and not os.environ.get("GITHUB_TOKEN"):
        raise ValueError("Set GITHUB_TOKEN locally, or use --transport git")
    records = selected_records(input_path, sample, seed, shard_index, shard_count)
    if not records:
        raise ValueError("Empty selected corpus")
    if expected_repositories is not None and len(records) != expected_repositories:
        raise ValueError(f"Expected {expected_repositories} repositories; selected {len(records)}")
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    config = {
        "schema_version": 1,
        "input_sha256": file_hash(input_path),
        "selection_sha256": sha256(json_bytes(records)),
        "repository_count": len(records),
        "transport": transport,
        "branch_policy": "main-then-master-v1",
        "modes": list(modes),
        "max_bytes": max_bytes,
        "repository_timeout_seconds": REPOSITORY_TIMEOUT_SECONDS,
        "catalog_sha256": load_rules(rules_dir)[1],
        "implementation_sha256": implementation_hash(root),
        "sample": sample,
        "seed": seed,
        "shard_index": shard_index,
        "shard_count": shard_count,
    }
    lock = output / ".corpus.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError(
            "Run lock exists; remove only after verifying no runner is active"
        ) from None
    os.close(fd)
    try:
        manifest_path = output / "manifest.json"
        if manifest_path.exists():
            if read_json(manifest_path)["configuration"] != config:
                raise ValueError(
                    "Resume requires unchanged inputs, implementation, rules and parameters"
                )
        else:
            atomic_json(
                manifest_path,
                {
                    "configuration": config,
                    "source": git_state(root),
                    "purpose": "exploratory corpus predictions, not human validation",
                },
            )
        started = time.monotonic()
        api = PacedAPI(api_interval)
        iterator = iter(records)
        totals: dict[str, Any] = {
            "repository_count": len(records),
            "finished": 0,
            "complete": 0,
            "failed": 0,
            "partial": 0,
            "timed_out": 0,
            "captured_bytes": 0,
            "api_calls": 0,
        }
        # At most workers tasks/results are live; never retain corpus evidence in RAM.
        with ThreadPoolExecutor(max_workers=workers) as pool:
            pending = set()

            def submit_next() -> None:
                record = next(iterator, None)
                if record is not None:
                    pending.add(
                        pool.submit(
                            run_guarded_repository,
                            record,
                            output,
                            modes,
                            transport,
                            max_bytes,
                            api,
                            retry_failed,
                            rules_dir,
                        )
                    )

            for _ in range(workers):
                submit_next()
            while pending:
                done, pending = wait(pending, return_when=FIRST_COMPLETED)
                for future in done:
                    result = future.result()
                    if not result.get("checkpoint_reused"):
                        api.network_calls += result.get("api_calls", 0)
                        api.rate_limit_wait_seconds += result.get("rate_limit_wait_seconds", 0)
                    if result.get("error") == "invalid-token":
                        raise ValueError(
                            "GitHub rejected GITHUB_TOKEN; run stopped. Correct it locally "
                            "and resume with --retry-failed."
                        )
                    totals["finished"] += 1
                    totals["complete"] += bool(result["complete"])
                    totals["failed"] += bool(result.get("error"))
                    totals["timed_out"] += result.get("error") == "repository-timeout"
                    totals["partial"] += not result["complete"] and not result.get("error")
                    totals["captured_bytes"] += result.get("captured_bytes", 0)
                    totals["api_calls"] += result.get("api_calls", 0)
                    totals["session_wall_seconds"] = time.monotonic() - started
                    atomic_json(output / "progress.json", totals)
                    block = repository_log(result, totals, modes)
                    with (output / "progress.log").open("a") as log:
                        log.write(block + "\n")
                    print(block, file=sys.stderr, flush=True)
                    submit_next()
        # Includes cached results; do not extrapolate a resumed session as a fresh pilot.
        totals["timing_note"] = "Fresh pilots only: resumed checkpoints distort session throughput"
        totals["session_api_network_calls"] = api.network_calls
        totals["rate_limit_wait_seconds"] = api.rate_limit_wait_seconds
        totals["api_calls_note"] = (
            "api_calls includes saved checkpoint request counts; session_api_network_calls counts actual REST attempts this invocation"
        )
        totals["all_repositories_accounted_for"] = totals["finished"] == len(records)
        # Includes timeout and other unsuccessful attempts with observed diagnostics.
        stop_records = []
        for path in sorted((output / "repositories").glob("*/result.json")):
            saved = read_json(path)
            if saved.get("error"):
                stop_records.append(saved)
        atomic_json(output / "stopped_repositories.json", stop_records)
        atomic_json(output / "summary.json", totals)
        return totals
    finally:
        lock.unlink()


def export_tables(output: Path, reference_path: Path | None = None) -> dict[str, int]:
    """Stream compact predictions and review candidates; never relabel the reference."""
    from .dataset import dataset_reference
    from .reference import final_reference

    reference = (
        final_reference(reference_path)
        if reference_path and reference_path.suffix == ".xlsx"
        else dataset_reference(read_json(reference_path))
        if reference_path
        else {}
    )
    count = candidates = 0
    configuration = read_json(output / "manifest.json")["configuration"]
    requested_modes = configuration["modes"]
    with (
        (output / "predictions.csv").open("w", newline="") as predictions,
        (output / "documentation_comparison.csv").open("w", newline="") as comparison,
        (output / "additional_evidence_candidates.csv").open("w", newline="") as additions,
        (output / "repository_status.csv").open("w", newline="") as statuses,
    ):
        pw, cw, aw = csv.writer(predictions), csv.writer(comparison), csv.writer(additions)
        sw = csv.writer(statuses)
        sw.writerow(
            [
                "requested_url",
                "repository",
                "status",
                "error",
                "commit",
                "stop_phase",
                "files_attempted",
                "eligible_files",
                "captured_bytes",
                "largest_eligible_file_bytes",
                "current_file",
                "last_error",
                "elapsed_seconds",
            ]
        )
        pw.writerow(["repository", "commit", "mode", "stage", "prediction", "scan_complete"])
        cw.writerow(
            [
                "repository",
                "commit",
                "stage",
                "human_documentation",
                "prediction",
                "outcome",
                "scan_complete",
            ]
        )
        aw.writerow(
            [
                "repository",
                "commit",
                "stage",
                "human_documentation",
                "documentation_prediction",
                "path",
                "start_line",
                "end_line",
                "url",
                "evidence_id",
                "review_status",
            ]
        )
        for path in sorted((output / "repositories").glob("*/result.json")):
            if file_hash(path) != path.with_name("result.sha256").read_text().strip():
                raise ValueError("Checkpoint checksum mismatch")
            result = read_json(path)
            count += 1
            modes = {r["mode"]: r for r in result["modes"]}
            repo = result.get(
                "repository", result["requested_url"].removeprefix("https://github.com/")
            )
            gold = reference.get(
                repo.casefold(),
                reference.get(
                    result["requested_url"].removeprefix("https://github.com/").casefold(), {}
                ),
            )
            sw.writerow(
                [
                    result["requested_url"],
                    repo,
                    "failed"
                    if result.get("error")
                    else "complete"
                    if result["complete"]
                    else "partial",
                    result.get("error", ""),
                    result.get("commit", ""),
                    *[
                        result.get("diagnostics", {}).get(key, "")
                        for key in (
                            "phase",
                            "files_attempted",
                            "eligible_files",
                            "captured_bytes",
                            "largest_eligible_file_bytes",
                            "current_file",
                            "last_error",
                        )
                    ],
                    result.get("elapsed_seconds", ""),
                ]
            )
            for mode in requested_modes:
                payload = modes.get(mode)
                for stage in STAGES:
                    value = payload["predictions"][stage] if payload else None
                    pw.writerow(
                        [
                            repo,
                            result.get("commit", ""),
                            mode,
                            stage,
                            "" if value is None else int(value),
                            payload["scan_complete"] if payload else False,
                        ]
                    )
            docs = modes.get("documentation-only")
            code = modes.get("code-only")
            for stage in STAGES:
                expected = gold.get(stage)
                observed = docs["predictions"][stage] if docs else None
                if expected is not None:
                    outcome = (
                        "unknown"
                        if observed is None
                        else "agreement"
                        if observed == bool(expected)
                        else "false-positive"
                        if observed
                        else "false-negative"
                    )
                    cw.writerow(
                        [
                            repo,
                            result.get("commit", ""),
                            stage,
                            expected,
                            "" if observed is None else int(observed),
                            outcome,
                            docs["scan_complete"] if docs else False,
                        ]
                    )
                if code and observed is not True:
                    for evidence in code["evidence"]:
                        if evidence["stage"] != stage:
                            continue
                        candidates += 1
                        aw.writerow(
                            [
                                repo,
                                result["commit"],
                                stage,
                                expected,
                                "" if observed is None else int(observed),
                                evidence["path"],
                                evidence["start_line"],
                                evidence["end_line"],
                                evidence["url"],
                                evidence["evidence_id"],
                                "documentation-incomplete"
                                if observed is None
                                else "needs-human-review",
                            ]
                        )
    return {"repositories": count, "candidate_occurrences": candidates}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--input", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--transport", choices=["hybrid", "api", "git"], default="hybrid")
    run.add_argument("--workers", type=int, default=2)
    run.add_argument("--mode", choices=[*MODES, "all"], default="all")
    run.add_argument("--sample", type=int)
    run.add_argument("--seed", default="msr27-pilot-v1")
    run.add_argument("--shard-index", type=int, default=0)
    run.add_argument("--shard-count", type=int, default=1)
    run.add_argument(
        "--max-bytes",
        type=int,
        default=0,
        help="Per-file size cap in bytes; 0 disables size exclusions",
    )
    run.add_argument("--api-interval", type=float, default=0.8)
    run.add_argument("--retry-failed", action="store_true")
    run.add_argument("--rules-dir", type=Path)
    run.add_argument("--expected-repositories", type=int)
    export = commands.add_parser("export")
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--reference", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "export":
            result = export_tables(args.output, args.reference)
        else:
            result = run_corpus(
                args.input,
                args.output,
                args.transport,
                args.workers,
                MODES if args.mode == "all" else (args.mode,),
                args.sample,
                args.seed,
                args.shard_index,
                args.shard_count,
                args.max_bytes,
                args.retry_failed,
                args.api_interval,
                args.rules_dir,
                args.expected_repositories,
            )
        print(json.dumps(result, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
