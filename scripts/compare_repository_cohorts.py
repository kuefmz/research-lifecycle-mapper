"""Compare supplied historical JSON and a current repository list, without network calls."""

import argparse
import json
from pathlib import Path

from lifecycle_mapper.canonical import write_csv, write_json
from lifecycle_mapper.openaire import file_hash, normalize_github


def compare(legacy: Path, current: Path, output: Path) -> dict:
    rows = json.loads(legacy.read_text(encoding="utf-8"))["results"]
    raw_legacy = [row["github_url"] for row in rows]
    raw_current = [
        line.strip()
        for line in current.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    cohorts = []
    for values in (raw_legacy, raw_current):
        normalized = [normalize_github(value) for value in values]
        if any(value is None for value in normalized):
            raise ValueError("Invalid repository URL; no input silently excluded")
        cohorts.append(set(normalized))
    old, new = cohorts
    shared, union = old & new, old | new
    output.mkdir(parents=True, exist_ok=True)
    for name, cohort in (
        ("shared", shared),
        ("legacy_only", old - new),
        ("current_only", new - old),
        ("union", union),
    ):
        (output / (name + ".txt")).write_text(
            "".join(url + "\n" for url in sorted(cohort)), encoding="utf-8"
        )
    write_csv(
        output / "membership.csv",
        ["github_repository_url", "in_legacy", "in_current"],
        [
            {
                "github_repository_url": url,
                "in_legacy": int(url in old),
                "in_current": int(url in new),
            }
            for url in sorted(union)
        ],
    )
    report = {
        "schema_version": 1,
        "legacy_source_sha256": file_hash(legacy),
        "current_source_sha256": file_hash(current),
        "legacy_records": len(rows),
        "legacy_unique_repositories": len(old),
        "legacy_duplicate_rows": len(rows) - len(old),
        "current_rows": len(raw_current),
        "current_unique_repositories": len(new),
        "current_duplicate_rows": len(raw_current) - len(new),
        "shared": len(shared),
        "legacy_only": len(old - new),
        "current_only": len(new - old),
        "union": len(union),
        "legacy_overlap_percent": round(100 * len(shared) / len(old), 4) if old else None,
        "current_overlap_percent": round(100 * len(shared) / len(new), 4) if new else None,
        "jaccard": round(len(shared) / len(union), 6) if union else None,
        "legacy_records_with_related_to": sum(bool(row.get("related_to")) for row in rows),
        "supplied_related_to_links": sum(len(row.get("related_to") or []) for row in rows),
        "identity_policy": "Case-insensitive owner/repository; strip .git and known GitHub deep links; no live alias/rename resolution.",
        "interpretation": "Historical JSON contains supplied related_to publication metadata; current list is unreviewed textual association candidates. Shared membership does not validate all references. Differences cannot be attributed to one cause without intermediate extraction data and historical query provenance.",
    }
    write_json(output / "summary.json", report)
    (output / "report.md").write_text(
        "# Repository overlap\n\n| Measure | Count |\n|---|---:|\n"
        + "".join(
            f"| {key} | {report[key]} |\n"
            for key in [
                "legacy_unique_repositories",
                "current_unique_repositories",
                "shared",
                "legacy_only",
                "current_only",
                "union",
            ]
        )
        + "\n"
        + report["interpretation"]
        + "\n\n"
        + report["identity_policy"]
        + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(compare(args.legacy, args.current, args.output), indent=2))


if __name__ == "__main__":
    main()
