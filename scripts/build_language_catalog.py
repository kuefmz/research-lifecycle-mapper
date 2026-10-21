"""Extract simple Linguist programming-language fields from a pinned YAML input.

Only top-level language names, type and scalar-list extensions/filenames/
interpreters are consumed. Unexpected list syntax fails rather than being guessed.
The generated registry is bundled; runtime does not fetch or parse YAML.
"""

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path


def scalar(text: str) -> str:
    if text.startswith(("'", '"')):
        value = ast.literal_eval(text)
        if not isinstance(value, str):
            raise ValueError("Non-string language field")
        return value
    return text.split(" #", 1)[0].strip()


def build(source: Path, output: Path, commit: str) -> None:
    languages = []
    current = None
    field = None
    for line in source.read_text().splitlines():
        if not line or line.startswith("#") or line == "---":
            continue
        if not line.startswith(" "):
            if not line.endswith(":"):
                raise ValueError("Unexpected top-level syntax")
            current = {
                "name": scalar(line[:-1]),
                "type": "",
                "extensions": [],
                "filenames": [],
                "interpreters": [],
            }
            languages.append(current)
            field = None
        elif current is not None:
            match = re.match(r"  (type|extensions|filenames|interpreters):(?: (.*))?$", line)
            if match:
                field = match[1]
                if field == "type":
                    current[field] = scalar(match[2])
                    field = None
            elif line.startswith("  - "):
                if field:
                    current[field].append(scalar(line[4:]))
            elif re.match(r"  \S", line):
                field = None
    payload = {
        "source": "https://github.com/github-linguist/linguist",
        "commit": commit,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "languages": [
            {k: v for k, v in row.items() if k != "type"}
            for row in languages
            if row["type"] == "programming"
        ],
    }
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    build(args.source, args.output, args.commit)
