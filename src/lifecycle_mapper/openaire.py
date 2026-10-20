"""Stream OpenAIRE software metadata; retain syntactically valid GitHub references.

No repository existence check or scientific eligibility claim is made at extraction.
Only codeRepositoryUrl/coderepositoryurl fields are used, never prose or citations.
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import tarfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlsplit

from .canonical import write_json

RESERVED = set(
    "about apps collections contact customer-stories enterprise events explore features "
    "issues join login marketplace new notifications orgs organizations pricing pulls "
    "search security settings site sponsors topics trending users".split()
)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_github(value: str) -> str | None:
    raw = value.strip()
    if raw.lower().startswith("git@github.com:"):
        raw = "https://github.com/" + raw.split(":", 1)[1]
    if raw.lower().startswith("git+"):
        raw = raw[4:]
    try:
        parsed = urlsplit(raw)
        if (
            parsed.scheme.lower() not in {"https", "http", "git", "ssh"}
            or (parsed.hostname or "").lower() not in {"github.com", "www.github.com"}
            or parsed.password is not None
            or (parsed.username is not None and parsed.username != "git")
            or parsed.port is not None
        ):
            return None
    except ValueError:
        return None
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        return None
    owner, repo = parts[:2]
    repo = re.sub(r"\.git$", "", repo, flags=re.I)
    if (
        owner.lower() in RESERVED
        or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", owner)
        or "--" in owner
        or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", repo)
        or repo in {".", ".."}
    ):
        return None
    # Repository deep links are normalized; they do not pin an analysis revision.
    if len(parts) > 2 and parts[2] not in {
        "tree",
        "blob",
        "releases",
        "issues",
        "pull",
        "pulls",
        "wiki",
        "commit",
        "commits",
        "archive",
        "discussions",
        "actions",
        "tags",
        "branches",
    }:
        return None
    return f"https://github.com/{owner.lower()}/{repo.lower()}"


def software_records(path: Path) -> Iterator[tuple[str, int, dict[str, Any]]]:
    # Stream members; never extract archive paths to the filesystem.
    with tarfile.open(path, "r|*") as archive:
        for member in archive:
            if not member.isfile() or not member.name.lower().endswith((".gz", ".json", ".jsonl")):
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            with extracted:
                source = (
                    gzip.GzipFile(fileobj=extracted)
                    if member.name.lower().endswith(".gz")
                    else extracted
                )
                with io.TextIOWrapper(source, encoding="utf-8", errors="strict") as stream:
                    for line_no, line in enumerate(stream, 1):
                        if not line.strip():
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            raise ValueError(f"Invalid JSON at {member.name}:{line_no}") from None
                        if not isinstance(record, dict):
                            raise ValueError(f"Expected JSON object at {member.name}:{line_no}")
                        yield member.name, line_no, record


def extract(source: Path, output: Path, source_record: str) -> dict[str, Any]:
    if not source.is_file():
        raise ValueError("Input software.tar does not exist")
    output.mkdir(parents=True, exist_ok=False)
    counts: Counter[str] = Counter()
    repos: Counter[str] = Counter()
    links_path = output / "software_links.csv"
    with links_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["member", "line", "openaire_id", "original_url", "github_repository_url"])
        for member, line_no, record in software_records(source):
            counts["software_records"] += 1
            raw = record.get("codeRepositoryUrl") or record.get("coderepositoryurl")
            values = [raw] if isinstance(raw, str) else raw if isinstance(raw, list) else []
            values = [v for v in values if isinstance(v, str) and v.strip()]
            counts["records_with_repository_field"] += bool(values)
            seen = set()
            for value in values:
                url = normalize_github(value)
                if url is None:
                    counts["rejected_url_values"] += 1
                elif url not in seen:
                    seen.add(url)
                    writer.writerow([member, line_no, record.get("id", ""), value, url])
                    repos[url] += 1
                    counts["github_record_links"] += 1
    if not counts["software_records"]:
        raise ValueError("No software records found; check archive member formats")
    repo_path = output / "repositories.csv"
    with repo_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["github_repository_url", "software_record_count"])
        writer.writerows(sorted(repos.items()))
    (output / "repositories.txt").write_text(
        "".join(url + "\n" for url in sorted(repos)), encoding="utf-8"
    )
    summary = {
        "schema_version": 1,
        "source_record": source_record,
        "source_tar_sha256": file_hash(source),
        "counts": {**dict(counts), "unique_github_repositories": len(repos)},
        "validation": "URL syntax only; existence/accessibility checked during acquisition",
        "normalization": "lowercase identity, strip .git, normalize known repository deep links",
        "outputs": {
            name: file_hash(output / name)
            for name in ("software_links.csv", "repositories.csv", "repositories.txt")
        },
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--software-tar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--source-record", required=True, help="Exact Zenodo release actually downloaded"
    )
    args = parser.parse_args()
    try:
        print(json.dumps(extract(args.software_tar, args.output, args.source_record), indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
