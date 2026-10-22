"""Subtract normalized GitHub identities, preserving first-occurrence input order."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from lifecycle_mapper.openaire import normalize_github


def select(source: Path, exclude: Path, output: Path) -> dict:
    changes = []

    def load(path: Path) -> dict[str, str]:
        records = {}
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            raw = line.strip()
            if not raw:
                continue
            url = normalize_github(raw)
            if url is None:
                raise ValueError(f"{path}:{number}: invalid GitHub repository link: {raw}")
            records.setdefault(url.casefold(), url)
            if url != raw:
                changes.append([str(path), number, raw, url])
        return records

    candidates, previous = load(source), load(exclude)
    remaining = [url for key, url in candidates.items() if key not in previous]
    if output.exists():
        raise ValueError("Choose a new output path; existing cohort lists are preserved")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(url + "\n" for url in remaining), encoding="utf-8")
    report = {
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "exclude_sha256": hashlib.sha256(exclude.read_bytes()).hexdigest(),
        "candidate_unique": len(candidates),
        "exclude_unique": len(previous),
        "overlap_excluded": len(candidates) - len(remaining),
        "remaining": len(remaining),
        "identity_policy": "Normalized GitHub roots; no live rename resolution",
    }
    output.with_suffix(".summary.json").write_text(json.dumps(report, indent=2) + "\n")
    with output.with_suffix(".normalization.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["input", "line", "original_url", "repository_url"])
        writer.writerows(changes)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--exclude", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(select(args.input, args.exclude, args.output), indent=2))


if __name__ == "__main__":
    main()
