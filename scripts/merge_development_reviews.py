"""Reconstruct complete development text inputs from preserved review exports."""

import argparse
import gzip
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-gzip", type=Path, required=True)
    parser.add_argument("--additional", type=Path, required=True)
    parser.add_argument("--updated-mismatches", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Use a new merged output path")
    original = gzip.decompress(args.original_gzip.read_bytes()).decode("utf-8")
    rows = {r["repository"]: r for r in map(json.loads, original.splitlines())}
    for row in map(json.loads, args.additional.read_text().splitlines()):
        if row["repository"] in rows:
            raise ValueError("Additional review duplicates original repository")
        rows[row["repository"]] = row
    updated = json.loads(args.updated_mismatches.read_text())
    for key in updated:
        if key not in rows:
            raise ValueError("Missing documentation for updated mismatch repository")
        rows[key]["mismatch_stages"] = updated[key]
    # Historical fields in rows absent from the newer export are preserved for
    # byte-for-byte reconstruction. The evaluator ignores mismatch_stages and
    # recomputes predictions from text; these fields are not reference labels.
    if any(r.get("partition") != "development" for r in rows.values()):
        raise ValueError("Development reviews only")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(rows[k], ensure_ascii=False) + "\n" for k in sorted(rows)),
        encoding="utf-8",
    )
    print(json.dumps({"repositories": len(rows), "output": str(args.output)}))


if __name__ == "__main__":
    main()
