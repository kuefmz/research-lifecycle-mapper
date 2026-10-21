"""Immutable GitHub acquisition and network-free integrity-checked replay."""

import base64
import json
import hashlib
import os
import re
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from pathlib import Path, PurePosixPath
from typing import Any, Callable
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .canonical import contained, json_bytes, read_json, sha256, write_json
from .telemetry import emit
from .source_languages import language_names
from .text_decoding import decode_text, POLICY as DECODING_POLICY

POLICY_VERSION = "eligibility-7-bundled-data-test-exclusions"
RESOURCE_POLICIES = {POLICY_VERSION, "eligibility-6-generated-corpus-exclusions"}
DECODING_POLICIES = RESOURCE_POLICIES | {"eligibility-5-legacy-text-decoding"}
BROAD_POLICIES = {
    POLICY_VERSION,
    "eligibility-6-generated-corpus-exclusions",
    "eligibility-5-legacy-text-decoding",
    "eligibility-4-txt-folder-density",
    "eligibility-3-programming-catalog",
}
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


def txt_folder_counts(paths: list[str]) -> dict[str, int]:
    """Count case-insensitive .txt suffixes per exact immediate Git directory."""
    from collections import Counter

    return dict(
        Counter(
            str(PurePosixPath(path).parent)
            for path in paths
            if PurePosixPath(path).suffix.lower() == ".txt"
        )
    )


def source_kind(
    path: str,
    policy: str = POLICY_VERSION,
    txt_counts: dict[str, int] | None = None,
) -> tuple[str | None, str | None]:
    parts = PurePosixPath(path.lower()).parts
    if policy in RESOURCE_POLICIES:
        if re.search(r"\.min\.(?:js|css)(?:\.map)?$|\.(?:js|css)\.map$", path, re.I):
            return None, "generated-minified-asset-or-source-map"
        if any(
            part in {"data", "other_data", "polyglot_data", "train", "test"} for part in parts[:-1]
        ) and re.fullmatch(
            r"(?:data_(?:pseudo|val|train|test)|polyglot(?:_[\w+-]+)?)\.[ef]", parts[-1]
        ):
            return None, "parallel-corpus-artifact"
    if any(part in EXCLUDED_PARTS for part in parts):
        return None, "vendored-generated-or-fixture"
    if policy in BROAD_POLICIES and any(
        part in {"third-party", "third-party-software", "third_party_software"} for part in parts
    ):
        return None, "vendored-generated-or-fixture"
    name = PurePosixPath(path).name.lower()
    suffix = PurePosixPath(path).suffix.lower()
    if policy == POLICY_VERSION:
        if re.fullmatch(
            r"(?:jquery(?:[-.]\d+(?:\.\d+)*)?|jquery-ui(?:[-.]\d+(?:\.\d+)*)?)\.js", name
        ):
            return None, "bundled-jquery-dependency"
        if (
            suffix == ".txt"
            and not name.startswith("readme")
            and any(
                part
                in {"data", "datasets", "experimental_data", "test_data", "testdata", "fixtures"}
                for part in parts[:-1]
            )
        ):
            return None, "data-directory-text-artifact"
        if (
            any(part in {"test", "tests", "testing"} for part in parts[:-1])
            or name.startswith("test_")
        ) and (suffix in CODE_SUFFIXES or language_names(path)):
            return None, "software-test-path"
    if name in {"license", "license.txt", "license.md", "copying", "authors.txt"}:
        return None, "administrative"
    if suffix == ".ipynb" and policy in BROAD_POLICIES | {"eligibility-2-notebook-cells"}:
        return "notebook", None
    if (
        policy
        in {
            POLICY_VERSION,
            "eligibility-6-generated-corpus-exclusions",
            "eligibility-5-legacy-text-decoding",
            "eligibility-4-txt-folder-density",
        }
        and suffix == ".txt"
        and txt_counts is not None
        and txt_counts.get(str(PurePosixPath(path).parent), 0) > 5
    ):
        return None, "txt-folder-more-than-5"
    if suffix in DOC_SUFFIXES:
        return "documentation", None
    if suffix in CODE_SUFFIXES:
        return "code", None
    if policy in BROAD_POLICIES and language_names(path):
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

    def __init__(
        self,
        code: str,
        status: int | None = None,
        reset: str | None = None,
        retry_after: str | None = None,
    ):
        self.code = code
        self.status = status
        self.reset = reset
        self.retry_after = retry_after
        super().__init__(code)


def api_get(
    endpoint: str,
    *,
    on_response: Callable[[Any], None] | None = None,
    on_request: Callable[[], None] | None = None,
) -> Any:
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
            if on_request:
                on_request()
            with urlopen(request, timeout=None) as response:
                if on_response:
                    on_response(response.headers)
                return json.loads(response.read())
        except HTTPError as exc:
            if on_response:
                on_response(exc.headers)
            if exc.code in {500, 502, 503, 504} and attempt < 2:
                time.sleep(attempt + 1)
                continue
            secondary = False
            if exc.code == 403:
                # Inspect only to classify the error; never persist its body.
                message = exc.read(65536).lower()
                secondary = b"secondary rate limit" in message or b"abuse detection" in message
            rate_limited = exc.code == 429 or (
                exc.code == 403
                and (
                    exc.headers.get("X-RateLimit-Remaining") == "0"
                    or exc.headers.get("Retry-After") is not None
                    or secondary
                )
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
            raise GitHubAPIError(
                code,
                exc.code,
                exc.headers.get("X-RateLimit-Reset")
                if exc.headers.get("X-RateLimit-Remaining") == "0"
                else None,
                exc.headers.get("Retry-After"),
            ) from None
        except (URLError, TimeoutError):
            raise GitHubAPIError("network-error") from None
    raise GitHubAPIError("retry-exhausted")


def tree_inventory(
    repo: str, tree_sha: str, getter: Callable[[str], Any] | None = None
) -> list[dict[str, Any]]:
    """Explicit tree walking avoids GitHub's truncated recursive-tree response."""
    getter = getter or api_get
    recursive = getter(f"/repos/{repo}/git/trees/{tree_sha}?recursive=1")
    if not recursive.get("truncated"):
        return sorted(
            [item for item in recursive["tree"] if item["type"] != "tree"],
            key=lambda item: item["path"],
        )
    result: list[dict[str, Any]] = []
    cache: dict[str, dict[str, Any]] = {}

    def fetch(tree: str, recursive: bool) -> dict[str, Any]:
        endpoint = f"/repos/{repo}/git/trees/{tree}" + ("?recursive=1" if recursive else "")
        if endpoint not in cache:
            cache[endpoint] = getter(endpoint)
        return cache[endpoint]

    def walk(tree: str, prefix: str, known_truncated: bool = False) -> None:
        if not known_truncated:
            payload = fetch(tree, True)
            if not payload.get("truncated"):
                result.extend(
                    {**entry, "path": prefix + entry["path"]}
                    for entry in payload["tree"]
                    if entry["type"] != "tree"
                )
                return
        payload = fetch(tree, False)
        if payload.get("truncated"):
            raise ValueError("Incomplete GitHub tree: acquisition aborted")
        for entry in sorted(payload["tree"], key=lambda item: item["path"]):
            path = prefix + entry["path"]
            if entry["type"] == "tree":
                walk(entry["sha"], path + "/")
            else:
                result.append({**entry, "path": path})

    walk(tree_sha, "", known_truncated=True)
    return sorted(result, key=lambda item: item["path"])


def raw_get(repo: str, commit: str, path: str, blob_sha: str, max_bytes: int) -> bytes:
    """Public, commit-pinned content; no bearer token is sent to the raw host."""
    repository_id("https://github.com/" + repo)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Raw acquisition requires an immutable commit")
    request = Request(
        f"https://raw.githubusercontent.com/{repo}/{commit}/{quote(path, safe='/')}",
        headers={"User-Agent": "lifecycle-mapper/0.3"},
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=None) as response:
                data = response.read(max_bytes + 1 if max_bytes else None)
            if max_bytes and len(data) > max_bytes:
                raise ValueError("Raw file exceeds acquisition size limit")
            actual = hashlib.sha1(
                b"blob " + str(len(data)).encode() + b"\0" + data, usedforsecurity=False
            ).hexdigest()
            if actual != blob_sha:
                raise ValueError("Raw Git blob checksum mismatch")
            return data
        except HTTPError as exc:
            throttled = exc.code == 429 or (
                exc.code == 403 and exc.headers.get("Retry-After") is not None
            )
            if (throttled or exc.code in {500, 502, 503, 504}) and attempt < 2:
                try:
                    delay = max(1.0, float(exc.headers.get("Retry-After", attempt + 1)))
                except ValueError:
                    delay = 60.0
                while delay > 0:
                    chunk = min(60.0, delay)
                    time.sleep(chunk)
                    delay -= chunk
                continue
            raise GitHubAPIError(
                "rate-limit" if throttled else "raw-http-error",
                exc.code,
                retry_after=exc.headers.get("Retry-After"),
            ) from None
        except (URLError, TimeoutError):
            if attempt < 2:
                time.sleep(attempt + 1)
                continue
            raise GitHubAPIError("raw-network-error") from None
    raise GitHubAPIError("raw-retry-exhausted")


def acquire(
    url: str,
    output: Path,
    ref: str | None = None,
    max_bytes: int = 0,
    *,
    blob_transport: str = "api",
    api_client: Callable[[str], Any] | None = None,
    resolve_head_direct: bool = False,
    sources: tuple[str, ...] = ("documentation", "code"),
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("Snapshot output must not already exist")
    if max_bytes < 0:
        raise ValueError("max_bytes must be nonnegative; 0 means no size cap")
    if blob_transport not in {"api", "raw"}:
        raise ValueError("Blob transport must be api or raw")
    if ref not in {None, "", "main"}:
        raise ValueError("Live acquisition uses main, otherwise master; no other ref is accepted")
    getter = api_client or api_get
    requested = repository_id(url)
    if not sources or any(source not in {"documentation", "code"} for source in sources):
        raise ValueError("Invalid acquisition sources")
    selected_branch = "main"
    try:
        branch = getter(f"/repos/{requested}/branches/main")
    except GitHubAPIError as exc:
        if exc.status != 404:
            raise
        selected_branch = "master"
        try:
            branch = getter(f"/repos/{requested}/branches/master")
        except GitHubAPIError as fallback_exc:
            if fallback_exc.status == 404:
                raise GitHubAPIError("main-and-master-not-found-or-inaccessible", 404) from None
            raise
    commit = branch["commit"]
    link = urlparse(commit["html_url"])
    suffix = "/commit/" + commit["sha"]
    if link.scheme != "https" or link.hostname != "github.com" or not link.path.endswith(suffix):
        raise ValueError("Invalid canonical commit URL")
    repo = repository_id("https://github.com" + link.path[: -len(suffix)])
    commit_sha = commit["sha"]
    emit(phase="tree-inventory")
    inventory = tree_inventory(repo, commit["commit"]["tree"]["sha"], getter)
    txt_counts = txt_folder_counts(
        [item["path"] for item in inventory if item["type"] == "blob" and item["mode"] != "120000"]
    )
    output.mkdir(parents=True)
    files = []
    eligible = [
        item
        for item in inventory
        if item["type"] == "blob"
        and item["mode"] != "120000"
        and source_kind(item["path"], txt_counts=txt_counts)[0] is not None
    ]
    emit(
        phase="acquisition",
        inventory_entries=len(inventory),
        eligible_files=len(eligible),
        total_eligible_bytes=sum(item.get("size", 0) or 0 for item in eligible),
        largest_eligible_file_bytes=max((item.get("size", 0) or 0 for item in eligible), default=0),
    )
    attempted = captured = captured_bytes = 0
    rate_limited = False
    acquisition_order = sorted(
        inventory,
        key=lambda item: (
            not Path(item["path"]).name.lower().startswith("readme"),
            source_kind(item["path"], txt_counts=txt_counts)[0] != "documentation",
            item["path"],
        ),
    )
    for item in acquisition_order:
        path = item["path"]
        source, reason = source_kind(path, txt_counts=txt_counts)
        if source is not None:
            attempted += 1
            emit(
                phase="acquisition",
                current_file=path,
                current_file_bytes=item.get("size"),
                files_attempted=attempted,
            )
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
        elif source is not None and source != "notebook" and source not in sources:
            record.update(status="unavailable", reason="source-not-requested")
        elif source is not None and max_bytes and item.get("size", max_bytes + 1) > max_bytes:
            record.update(status="unavailable", reason="size-limit")
        elif source is not None and rate_limited:
            record.update(status="unavailable", reason="rate-limit")
        elif source is not None:
            try:
                if blob_transport == "raw":
                    data = raw_get(repo, commit_sha, path, item["sha"], max_bytes)
                else:
                    blob = getter(f"/repos/{repo}/git/blobs/{item['sha']}")
                    if blob.get("encoding") != "base64":
                        raise ValueError("Unsupported GitHub blob encoding")
                    data = base64.b64decode(blob["content"].replace("\n", ""), validate=True)
                if max_bytes and len(data) > max_bytes:
                    raise ValueError("Blob exceeds acquisition size limit")
                if len(data) != item["size"]:
                    raise ValueError("Blob size mismatch")
                _, text_encoding = decode_text(data)
                if b"\x00" in data:
                    raise ValueError("Binary content")
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
            except Exception as exc:
                # Stable error class; never persist response bodies/tokens or volatile messages.
                # A raw-host failure must not suppress every subsequent file.
                # REST cooldowns are shared by the paced API client.
                rate_limited = (
                    blob_transport == "api" and getattr(exc, "code", None) == "rate-limit"
                )
                record.update(
                    status="unavailable", reason=str(getattr(exc, "code", type(exc).__name__))
                )
                emit(last_error=record["reason"], last_error_file=path)
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
        "transport": "github-api-raw" if blob_transport == "raw" else "github-api",
        "requested_ref": selected_branch,
        "selected_branch": selected_branch,
        "branch_policy": "main-then-master-v1",
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
    if manifest.get("schema_version") != 1 or manifest.get("policy_version") not in {
        "eligibility-1",
        "eligibility-2-notebook-cells",
        "eligibility-3-programming-catalog",
        "eligibility-4-txt-folder-density",
        "eligibility-5-legacy-text-decoding",
        "eligibility-6-generated-corpus-exclusions",
        POLICY_VERSION,
    }:
        raise ValueError("Unsupported snapshot schema or eligibility policy")
    if not re.fullmatch(r"[0-9a-f]{40}", manifest.get("commit", "")):
        raise ValueError("Snapshot requires an immutable 40-character commit SHA")
    if repository_id(manifest["source_url"]) != manifest["repository"]:
        raise ValueError("Snapshot repository identifier mismatch")
    files = manifest["files"]
    paths = [item["path"] for item in files]
    if paths != sorted(set(paths)):
        raise ValueError("Snapshot inventory must be unique and sorted")
    txt_counts = txt_folder_counts(
        [item["path"] for item in files if item.get("mode") in {"100644", "100755"}]
    )
    contents = {}
    for item in files:
        target = contained(root / "content", item["path"])
        source, _ = source_kind(item["path"], manifest["policy_version"], txt_counts)
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
            if manifest["policy_version"] in DECODING_POLICIES:
                text, encoding = decode_text(data)
                if (
                    item.get("text_encoding", encoding) != encoding
                    or item.get("decoding_policy", DECODING_POLICY) != DECODING_POLICY
                ):
                    raise ValueError("Snapshot decoding provenance mismatch")
            else:
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
