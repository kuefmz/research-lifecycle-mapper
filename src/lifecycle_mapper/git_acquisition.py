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

from .acquisition import POLICY_VERSION, repository_id, source_kind
from .canonical import contained, sha256, write_json


def acquire_git(
    url: str, output: Path, ref: str | None = None, max_bytes: int = 250_000
) -> dict[str, Any]:
    repo = repository_id(url)
    if output.exists() or max_bytes < 1:
        raise ValueError("Snapshot must be new and max_bytes positive")
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
                    timeout=180,
                ).stdout
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                raise OSError("Git acquisition failed or timed out") from exc

        git(
            "clone",
            "--quiet",
            "--depth=1",
            f"--filter=blob:limit={max_bytes}",
            "--no-checkout",
            "--",
            f"https://github.com/{repo}.git",
            str(checkout),
        )
        if ref:
            if ref.startswith("-") or any(c in ref for c in "\r\n\x00"):
                raise ValueError("Invalid Git ref")
            git("-C", str(checkout), "fetch", "--quiet", "--depth=1", "origin", ref)
        commit = (
            git("-C", str(checkout), "rev-parse", "FETCH_HEAD" if ref else "HEAD").decode().strip()
        )
        tree = git("-C", str(checkout), "rev-parse", f"{commit}^{{tree}}").decode().strip()
        raw = git("-C", str(checkout), "ls-tree", "-r", "-l", "-z", commit)
        files: list[dict[str, Any]] = []
        output.mkdir(parents=True)
        for entry in raw.split(b"\0"):
            if not entry:
                continue
            metadata, name = entry.split(b"\t", 1)
            mode, kind, blob, size_text = metadata.decode().split()
            path = name.decode("utf-8")
            source, reason = source_kind(path)
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
            elif source is not None and (size is None or size > max_bytes):
                record.update(status="unavailable", reason="size-limit")
            elif source is not None:
                try:
                    data = git("-C", str(checkout), "cat-file", "blob", blob)
                    data.decode("utf-8")
                    if b"\0" in data or len(data) != size:
                        raise ValueError("Binary or mismatched blob")
                    target = contained(output / "content", path)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    record.update(status="captured", reason=None, sha256=sha256(data))
                except (OSError, ValueError) as exc:
                    record.update(status="unavailable", reason=type(exc).__name__)
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
            "requested_ref": ref,
            "acquired_at": datetime.now(timezone.utc).isoformat(),
        }
        write_json(output / "manifest.json", manifest)
        return manifest
