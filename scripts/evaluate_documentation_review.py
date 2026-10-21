"""Development-only text replay when complete repository snapshots are unavailable.

The review export omits error-free repositories. Counts apply only to supplied
complete development texts, not to all 100 repositories or an independent test.
"""

import argparse
import csv
import json
from pathlib import Path

from lifecycle_mapper import STAGES
from lifecycle_mapper.analysis import load_rules
from lifecycle_mapper.benchmark import calculate_metrics
from lifecycle_mapper.canonical import write_json, write_csv
from lifecycle_mapper.documentation import document_units, workflow_units, documentation_matches
from lifecycle_mapper.openaire import file_hash


def evaluate(review: Path, comparison: Path, rules: Path, output: Path) -> dict:
    references = {}
    with comparison.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if (
                row["partition"] != "development"
                or row["mode"] != "documentation-only"
                or row["scan_complete"].lower() != "true"
            ):
                continue
            references.setdefault(row["repository"], {})[row["stage"]] = row
    catalog, catalog_hash = load_rules(rules)
    grouped = {
        stage: [r for r in catalog if r["source"] == "documentation" and r["stage"] == stage]
        for stage in STAGES
    }
    gold = []
    pred = []
    baseline = []
    rows = []
    provenance = []
    for line in review.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if item.get("partition") != "development":
            raise ValueError("Review must contain development texts only")
        repo = item["repository"]
        if repo not in references or set(references[repo]) != set(STAGES):
            raise ValueError("Development review lacks a complete six-label reference")
        if any(p["repository"] == repo for p in provenance):
            raise ValueError("Duplicate review repository")
        found = set()
        evidence = {}
        for doc in item["documentation"]:
            text = doc["text"]
            standard = document_units(text)
            extended = None
            for stage in STAGES:
                if stage in found:
                    continue
                for rule in grouped[stage]:
                    if rule.get("unit_policy") == "documented-workflow-v5":
                        if extended is None:
                            extended = workflow_units(text)
                        units = extended
                    else:
                        units = standard
                    match = next(
                        (
                            m
                            for m in documentation_matches(text, rule, units, first_only=True)
                            if not m["exclusion_reasons"]
                        ),
                        None,
                    )
                    if match:
                        found.add(stage)
                        evidence[stage] = {"rule_id": rule["id"], "path": doc["path"], **match}
                        break
            if len(found) == len(STAGES):
                break
        labels = {s: int(references[repo][s]["human_documentation"]) for s in STAGES}
        gold.append(labels)
        pred.append(sorted(found))
        baseline.append([s for s in STAGES if references[repo][s]["prediction"] == "1"])
        rows.extend(
            {
                "repository": repo,
                "stage": s,
                "gold": labels[s],
                "baseline": int(s in baseline[-1]),
                "candidate": int(s in found),
                "evidence": json.dumps(evidence.get(s), ensure_ascii=False),
            }
            for s in STAGES
        )
        provenance.append({"repository": repo, "snapshot_sha256": item["snapshot_sha256"]})
        print(f"[{len(gold)}/{len(references)}] development text replay", flush=True)
    report = {
        "scope": "Supplied error-review development texts only; error-free development repositories not exported and are not silently assumed unchanged.",
        "baseline": calculate_metrics(gold, baseline),
        "candidate": calculate_metrics(gold, pred),
        "baselines": {
            "always_negative": calculate_metrics(gold, [[] for _ in gold]),
            "always_positive": calculate_metrics(gold, [list(STAGES) for _ in gold]),
        },
        "rules_sha256": catalog_hash,
        "review_sha256": file_hash(review),
        "comparison_sha256": file_hash(comparison),
        "provenance": provenance,
    }
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "metrics.json", report)
    write_csv(
        output / "predictions.csv",
        ["repository", "stage", "gold", "baseline", "candidate", "evidence"],
        rows,
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--rules-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.review, args.comparison, args.rules_dir, args.output)
    print(
        json.dumps(
            {name: report[name] for name in ["scope", "baseline", "candidate", "baselines"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
