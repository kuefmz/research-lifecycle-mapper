"""Reproduce full-corpus aggregate counts from supplied counts and a saved execution log."""

import csv
import gzip
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODES = ("documentation-only", "code-only", "combined")
STAGES = ("Collection", "Processing", "Method", "Experimentation", "Evaluation", "Dissemination")


def identities(path):
    rows = [
        s.strip().casefold().removeprefix("https://github.com/").rstrip("/")
        for s in path.read_text().splitlines()
        if s.strip()
    ]
    assert len(rows) == len(set(rows)), path
    return set(rows)


def reproduce(folder=HERE):
    source = folder / "source"
    provenance = json.loads((source / "provenance.json").read_text())
    compressed = (source / "execution.log.gz").read_bytes()
    assert hashlib.sha256(compressed).hexdigest() == provenance["compressed_log_sha256"]
    raw = gzip.decompress(compressed)
    assert hashlib.sha256(raw).hexdigest() == provenance["execution_log_sha256"]
    text = raw.decode("utf-8")
    headers = list(
        re.finditer(
            r"^\[(\d+)/(\d+)\] (https://github.com/\S+) \| (complete|partial|failed)([^\n]*)",
            text,
            re.M,
        )
    )
    latest = {}
    for i, match in enumerate(headers):
        key = match[3].casefold().removeprefix("https://github.com/").rstrip("/")
        latest[key] = text[
            match.end() : headers[i + 1].start() if i + 1 < len(headers) else len(text)
        ]
    base = folder.parent / "corpus-386"
    corpus = identities(folder / "repositories.txt")
    previous = identities(base / "repositories.txt")
    assert len(corpus) == 3211 and len(previous) == 386
    assert not previous.intersection(latest)
    assert previous | latest.keys() == corpus
    assert len(latest) == 2825
    counts = Counter()
    for body in latest.values():
        for mode in MODES:
            matches = re.findall(
                r"^  "
                + re.escape(mode)
                + r": ([01?](?: \| [01?]){5})  \(scan (complete|incomplete)\)",
                body,
                re.M,
            )
            assert len(matches) == 1, mode
            vector, scan = matches[0]
            for stage, value in zip(STAGES, vector.split(" | "), strict=True):
                counts[mode, stage, value] += 1
    supplied = list(csv.DictReader((base / "stage_counts.csv").open(newline="")))
    expected_hash = json.loads((base / "stage_counts_provenance.json").read_text())["sha256"]
    assert hashlib.sha256((base / "stage_counts.csv").read_bytes()).hexdigest() == expected_hash
    assert len(supplied) == 18
    seen = set()
    for row in supplied:
        key = (row["mode"], row["stage"])
        assert key not in seen
        seen.add(key)
        assert sum(int(row[k]) for k in ("positive", "negative", "unknown")) == 386
        for field, value in (("positive", "1"), ("negative", "0"), ("unknown", "?")):
            counts[*key, value] += int(row[field])
    assert seen == {(mode, stage) for mode in MODES for stage in STAGES}
    results = []
    for mode in MODES:
        for stage in STAGES:
            pos, neg, unknown = [counts[mode, stage, value] for value in ("1", "0", "?")]
            assert pos + neg + unknown == 3211
            results.append(
                dict(
                    mode=mode,
                    stage=stage,
                    positive=pos,
                    negative=neg,
                    unknown=unknown,
                    total=3211,
                    positive_percent_all=round(100 * pos / 3211, 4),
                    unknown_percent_all=round(100 * unknown / 3211, 4),
                )
            )
    return results


def write_outputs(rows, folder=HERE):
    with (folder / "stage_counts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (folder / "aggregate_summary.json").write_text(
        json.dumps(
            {
                "repository_count": 3211,
                "scope": "Full-population stage aggregates from supplied 386 counts and final log decisions for the disjoint execution remainder.",
                "stage_counts": rows,
                "interpretation": "Detected evidence counts, not ground-truth prevalence or full-corpus accuracy.",
                "limitations": [
                    "Original 386 row-level export not supplied; base aggregates are author-reported.",
                    "Log-derived decisions do not provide full pinned-commit and evidence provenance.",
                    "Full-population mode-complete repository totals cannot be recovered from per-stage base aggregates.",
                    "No full-population precision, recall or F1 without human labels.",
                ],
            },
            indent=2,
        )
        + "\n"
    )
    print("Full corpus: 3211 repositories. Combined counts: positive / negative / unknown")
    for row in rows:
        if row["mode"] == "combined":
            print(
                f"{row['stage']:18} {row['positive']:4} / {row['negative']:4} / {row['unknown']:4} ({row['positive_percent_all']:.2f}% positive of all repositories)"
            )


if __name__ == "__main__":
    write_outputs(reproduce())
