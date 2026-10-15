"""Immutable GitHub acquisition and network-free integrity-checked replay."""

import base64
import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .canonical import contained, json_bytes, read_json, sha256, write_json

POLICY_VERSION = "eligibility-1"
DOC_SUFFIXES = {".md", ".rst", ".adoc", ".txt"}
CODE_SUFFIXES = {
    ".py",
    ".r",
    ".jl",
    ".js",
    ".ts",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".cc",
    ".h",
    ".hpp",
    ".sh",
    ".scala",
    ".m",
}
EXCLUDED_PARTS = {
    "vendor",
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
    "fixtures",
    "testdata",
    "third_party",
}


def source_kind(path: str) -> tuple[str | None, str | None]:
    parts = PurePosixPath(path.lower()).parts
    if any(part in EXCLUDED_PARTS for part in parts):
        return None, "vendored-generated-or-fixture"
    name = PurePosixPath(path).name.lower()
    suffix = PurePosixPath(path).suffix.lower()
    if name in {"license", "license.txt", "license.md", "copying", "authors.txt"}:
        return None, "administrative"
    if suffix in DOC_SUFFIXES:
        return "documentation", None
    if suffix in CODE_SUFFIXES:
        return "code", None
    return None, "unsupported-artifact"


def repository_id(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise ValueError("Expected https://github.com/OWNER/REPO")
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 2 or parsed.query or parsed.fragment:
        raise ValueError("Supply a repository URL, not a branch/file URL")
    owner, name = parts
    name = name.removesuffix(".git")
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) and p not in {".", ".."} for p in (owner, name)):
        raise ValueError("Invalid GitHub repository identifier")
    return f"{owner}/{name}"


class GitHubAPIError(OSError):
    """Sanitized failure; response bodies and authorization headers never persist."""

    def __init__(self, code: str, status: int | None = None, reset: str | None = None):
        self.code = code
        self.status = status
        self.reset = reset
        super().__init__(code)


def api_get(endpoint: str) -> Any:
    if not endpoint.startswith("/") or endpoint.startswith("//"):
        raise ValueError("Expected a relative GitHub API endpoint")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "lifecycle-mapper/0.3",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    request = Request("https://api.github.com" + endpoint, headers=headers)
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            if exc.code in {500, 502, 503, 504} and attempt < 2:
                time.sleep(attempt + 1)
                continue
            rate_limited = exc.code == 429 or (
                exc.code == 403 and exc.headers.get("X-RateLimit-Remaining") == "0"
            )
            code = (
                "rate-limit"
                if rate_limited
                else "invalid-token"
                if exc.code == 401
                else "not-found-or-inaccessible"
                if exc.code == 404
                else "api-http-error"
            )
            raise GitHubAPIError(code, exc.code, exc.headers.get("X-RateLimit-Reset")) from None
        except (URLError, TimeoutError):
            raise GitHubAPIError("network-error") from None
    raise GitHubAPIError("retry-exhausted")


def tree_inventory(repo: str, tree_sha: str) -> list[dict[str, Any]]:
    """Explicit tree walking avoids GitHub's truncated recursive-tree response."""
    recursive = api_get(f"/repos/{repo}/git/trees/{tree_sha}?recursive=1")
    if not recursive.get("truncated"):
        return sorted(
            [item for item in recursive["tree"] if item["type"] != "tree"],
            key=lambda item: item["path"],
        )
    result: list[dict[str, Any]] = []

    def walk(tree: str, prefix: str) -> None:
        payload = api_get(f"/repos/{repo}/git/trees/{tree}")
        if payload.get("truncated"):
            raise ValueError("Incomplete GitHub tree: acquisition aborted")
        for entry in sorted(payload["tree"], key=lambda item: item["path"]):
            path = prefix + entry["path"]
            if entry["type"] == "tree":
                walk(entry["sha"], path + "/")
            else:
                result.append({**entry, "path": path})

    walk(tree_sha, "")
    return sorted(result, key=lambda item: item["path"])


def acquire(
    url: str, output: Path, ref: str | None = None, max_bytes: int = 250_000
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("Snapshot output must not already exist")
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    requested = repository_id(url)
    metadata = api_get(f"/repos/{requested}")
    repo = metadata["full_name"]
    commit = api_get(f"/repos/{repo}/commits/{quote(ref or metadata['default_branch'], safe='')}")
    commit_sha = commit["sha"]
    inventory = tree_inventory(repo, commit["commit"]["tree"]["sha"])
    output.mkdir(parents=True)
    files = []
    rate_limited = False
    acquisition_order = sorted(
        inventory,
        key=lambda item: (
            not Path(item["path"]).name.lower().startswith("readme"),
            source_kind(item["path"])[0] != "documentation",
            item["path"],
        ),
    )
    for item in acquisition_order:
        path = item["path"]
        source, reason = source_kind(path)
        record = {
            "path": path,
            "git_blob_sha": item["sha"],
            "mode": item["mode"],
            "size": item.get("size"),
            "source": source,
            "status": "excluded",
            "reason": reason,
            "sha256": None,
        }
        if item["type"] != "blob" or item["mode"] == "120000":
            record["reason"] = "submodule-or-symlink"
        elif source is not None and item.get("size", max_bytes + 1) > max_bytes:
            record.update(status="unavailable", reason="size-limit")
        elif source is not None and rate_limited:
            record.update(status="unavailable", reason="rate-limit")
        elif source is not None:
            try:
                blob = api_get(f"/repos/{repo}/git/blobs/{item['sha']}")
                if blob.get("encoding") != "base64":
                    raise ValueError("Unsupported GitHub blob encoding")
                data = base64.b64decode(blob["content"].replace("\n", ""), validate=True)
                if len(data) > max_bytes:
                    raise ValueError("Blob exceeds acquisition size limit")
                if len(data) != item["size"]:
                    raise ValueError("Blob size mismatch")
                data.decode("utf-8")
                if b"\x00" in data:
                    raise ValueError("Binary content")
                target = contained(output / "content", path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                record.update(status="captured", reason=None, sha256=sha256(data))
            except Exception as exc:
                # Stable error class; never persist response bodies/tokens or volatile messages.
                rate_limited = getattr(exc, "code", None) == "rate-limit"
                record.update(
                    status="unavailable", reason=str(getattr(exc, "code", type(exc).__name__))
                )
        files.append(record)
    manifest = {
        "schema_version": 1,
        "repository": repo,
        "source_url": f"https://github.com/{repo}",
        "commit": commit_sha,
        "tree_sha": commit["commit"]["tree"]["sha"],
        "inventory_complete": True,
        "policy_version": POLICY_VERSION,
        "max_bytes": max_bytes,
        "files": sorted(files, key=lambda item: item["path"]),
        "redistribution": "not-reviewed",
        "synthetic": False,
        "transport": "github-api",
        "requested_ref": ref,
        "acquired_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def replay(root: Path, expected_hash: str | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    raw = (root / "manifest.json").read_bytes()
    if expected_hash is not None and sha256(raw) != expected_hash:
        raise ValueError("Snapshot manifest checksum mismatch")
    manifest = read_json(root / "manifest.json")
    if raw != json_bytes(manifest):
        raise ValueError("Snapshot manifest must use canonical serialization")
    if manifest.get("schema_version") != 1 or manifest.get("policy_version") != POLICY_VERSION:
        raise ValueError("Unsupported snapshot schema or eligibility policy")
    if not re.fullmatch(r"[0-9a-f]{40}", manifest.get("commit", "")):
        raise ValueError("Snapshot requires an immutable 40-character commit SHA")
    if repository_id(manifest["source_url"]) != manifest["repository"]:
        raise ValueError("Snapshot repository identifier mismatch")
    files = manifest["files"]
    paths = [item["path"] for item in files]
    if paths != sorted(set(paths)):
        raise ValueError("Snapshot inventory must be unique and sorted")
    contents = {}
    for item in files:
        target = contained(root / "content", item["path"])
        source, _ = source_kind(item["path"])
        if item["source"] != source or item["status"] not in {
            "captured",
            "excluded",
            "unavailable",
        }:
            raise ValueError("Invalid inventory source/status")
        if item["status"] == "captured":
            if source is None or item.get("mode") == "120000":
                raise ValueError("Captured ineligible artifact")
            data = target.read_bytes()
            if sha256(data) != item["sha256"] or len(data) != item["size"]:
                raise ValueError(f"Content integrity failure: {item['path']}")
            text = data.decode("utf-8")
            if "\x00" in text:
                raise ValueError("Binary captured artifact")
            contents[item["path"]] = text
        elif (
            source is not None
            and item["status"] == "excluded"
            and item.get("reason") != "submodule-or-symlink"
        ):
            raise ValueError("Eligible file silently excluded")
    return manifest, contents
