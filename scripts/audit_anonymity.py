"""Scan distributed files and XML inside ZIP/XLSX without storing private patterns."""

import argparse
import json
import re
import zipfile
from pathlib import Path

SKIP = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "local"}


def audit(root: Path, patterns: list[str]) -> dict:
    matches = []
    checked = 0
    expressions = [re.compile(re.escape(value), re.I) for value in patterns if value]
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP for part in path.relative_to(root).parts):
            continue
        relative = path.relative_to(root).as_posix()
        if path.suffix.lower() in {".xlsx", ".zip"}:
            with zipfile.ZipFile(path) as archive:
                records = [
                    (name, archive.read(name).decode("utf-8", errors="ignore"))
                    for name in archive.namelist()
                    if name.endswith((".xml", ".rels"))
                ]
        else:
            records = [(relative, path.read_bytes().decode("utf-8", errors="ignore"))]
        for member, text in records:
            checked += 1
            if any(
                expression.search(text) or expression.search(relative) for expression in expressions
            ):
                matches.append({"path": relative, "member": member})
    return {
        "patterns_checked": len(expressions),
        "records_checked": checked,
        "match_count": len(matches),
        "matches": matches,
        "scope": "distributed files only; hosting account and historical Git metadata excluded",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--forbid", action="append", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.root, args.forbid)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result["match_count"] else 0)


if __name__ == "__main__":
    main()
