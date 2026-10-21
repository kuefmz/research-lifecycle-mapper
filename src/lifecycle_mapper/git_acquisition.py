"""Read-only Git transport for public repositories without an API-token dependency.

Only Git objects are read; no checkout, hooks, submodules, or repository code run.
Large blobs are inventoried without fetching them. Git must support partial clone.
"""

import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .acquisition import POLICY_VERSION, repository_id, source_kind, txt_folder_counts
from .canonical import contained, sha256, write_json
from .telemetry import emit
from .text_decoding import decode_text, POLICY as DECODING_POLICY


def acquire_git(
    url: str, output: Path, ref: str | None = None, max_bytes: int = 0
) -> dict[str, Any]:
    if ref not in {None, "", "main"}:
        raise ValueError("Live acquisition uses main, otherwise master; no other ref is accepted")
    repo = repository_id(url)
    if output.exists() or max_bytes < 0:
        raise ValueError("Snapshot must be new and max_bytes nonnegative; 0 means no size cap")
    # No environment token is put into a subprocess argument or an exported manifest.
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".rlm-git-", dir=output.parent) as directory:
        checkout = Path(directory) / "objects"

        def git(*args: str) -> bytes:
            try:
                return subprocess.run(
                    ["git", "-c", "core.hooksPath=/dev/null", *args],
                    env=env,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ).stdout
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                raise OSError("Git acquisition failed or timed out") from exc

        heads = (
            git(
                "ls-remote",
                "--heads",
                "--",
                f"https://github.com/{repo}.git",
                "refs/heads/main",
                "refs/heads/master",
            )
            .decode()
            .splitlines()
        )
        names = {line.split()[1] for line in heads if len(line.split()) == 2}
        selected_branch = (
            "main"
            if "refs/heads/main" in names
            else "master"
            if "refs/heads/master" in names
            else None
        )
        if selected_branch is None:
            raise OSError("Neither main nor master branch is available")
        emit(phase="git-clone")
        git(
            "clone",
            "--quiet",
            "--depth=1",
            "--single-branch",
            f"--branch={selected_branch}",
            f"--filter=blob:limit={max_bytes}" if max_bytes else "--filter=blob:none",
            "--no-checkout",
            "--",
            f"https://github.com/{repo}.git",
            str(checkout),
        )
        # A tag with the same name cannot substitute for this remote branch.
        commit = (
            git("-C", str(checkout), "rev-parse", f"refs/remotes/origin/{selected_branch}")
            .decode()
            .strip()
        )
        tree = git("-C", str(checkout), "rev-parse", f"{commit}^{{tree}}").decode().strip()
        emit(phase="tree-inventory")
        raw = git("-C", str(checkout), "ls-tree", "-r", "-l", "-z", commit)
        files: list[dict[str, Any]] = []
        metadata_entries = [entry.split(b"\t", 1) for entry in raw.split(b"\0") if entry]
        txt_counts = txt_folder_counts(
            [
                name.decode("utf-8")
                for meta, name in metadata_entries
                if meta.decode().split()[0] in {"100644", "100755"}
            ]
        )
        eligible_sizes = [
            int(meta.decode().split()[-1])
            for meta, name in metadata_entries
            if meta.decode().split()[-1] != "-"
            and source_kind(name.decode("utf-8"), txt_counts=txt_counts)[0] is not None
        ]
        emit(
            phase="acquisition",
            inventory_entries=len(metadata_entries),
            eligible_files=len(eligible_sizes),
            total_eligible_bytes=sum(eligible_sizes),
            largest_eligible_file_bytes=max(eligible_sizes, default=0),
        )
        attempted = captured = captured_bytes = 0
        output.mkdir(parents=True)
        for entry in raw.split(b"\0"):
            if not entry:
                continue
            metadata, name = entry.split(b"\t", 1)
            mode, kind, blob, size_text = metadata.decode().split()
            path = name.decode("utf-8")
            source, reason = source_kind(path, txt_counts=txt_counts)
            if source is not None:
                attempted += 1
                emit(phase="acquisition", current_file=path, files_attempted=attempted)
            size = int(size_text) if size_text != "-" else None
            record = {
                "path": path,
                "git_blob_sha": blob,
                "mode": mode,
                "size": size,
                "source": source,
                "status": "excluded",
                "reason": reason,
                "sha256": None,
            }
            if kind != "blob" or mode == "120000":
                record["reason"] = "submodule-or-symlink"
            elif source is not None and (size is None or (max_bytes and size > max_bytes)):
                record.update(status="unavailable", reason="size-limit")
            elif source is not None:
                try:
                    data = git("-C", str(checkout), "cat-file", "blob", blob)
                    _, text_encoding = decode_text(data)
                    if b"\0" in data or len(data) != size:
                        raise ValueError("Binary or mismatched blob")
                    target = contained(output / "content", path)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    record.update(
                        status="captured",
                        reason=None,
                        sha256=sha256(data),
                        text_encoding=text_encoding,
                        decoding_policy=DECODING_POLICY,
                    )
                    captured += 1
                    captured_bytes += len(data)
                    emit(files_captured=captured, captured_bytes=captured_bytes)
                except (OSError, ValueError) as exc:
                    record.update(status="unavailable", reason=type(exc).__name__)
                    emit(last_error=record["reason"], last_error_file=path)
            files.append(record)
        manifest = {
            "schema_version": 1,
            "repository": repo,
            "source_url": f"https://github.com/{repo}",
            "commit": commit,
            "tree_sha": tree,
            "inventory_complete": True,
            "policy_version": POLICY_VERSION,
            "max_bytes": max_bytes,
            "files": sorted(files, key=lambda x: x["path"]),
            "redistribution": "not-reviewed",
            "synthetic": False,
            "transport": "git-partial-clone",
            "requested_ref": selected_branch,
            "selected_branch": selected_branch,
            "branch_policy": "main-then-master-v1",
            "acquired_at": datetime.now(timezone.utc).isoformat(),
        }
        write_json(output / "manifest.json", manifest)
        return manifest
