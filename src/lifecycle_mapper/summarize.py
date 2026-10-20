"""Documentation-only reference metrics; source discoveries remain a separate review."""

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from . import STAGES
from .benchmark import calculate_metrics
from .canonical import write_json


def summarize(path: Path, expected: int = 100, bootstrap: int = 1000) -> dict[str, Any]:
    if expected < 1 or bootstrap < 1:
        raise ValueError("Expected population and bootstrap iterations must be positive")
    rows: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["stage"] not in STAGES or row["stage"] in rows[row["repository"]]:
                raise ValueError("Unexpected or duplicate repository-stage decision")
            rows[row["repository"]][row["stage"]] = row
    gold, predictions = [], []
    for repo in sorted(rows):
        values = rows[repo]
        if set(values) != set(STAGES):
            raise ValueError("Incomplete reference stage table")
        if not all(v["scan_complete"].lower() == "true" for v in values.values()):
            continue
        if any(
            v["prediction"] not in {"0", "1"} or v["human_documentation"] not in {"0", "1"}
            for v in values.values()
        ):
            raise ValueError("Complete scans require literal binary reference and prediction")
        gold.append({s: int(values[s]["human_documentation"]) for s in STAGES})
        predictions.append([s for s in STAGES if values[s]["prediction"] == "1"])
    if len(rows) > expected:
        raise ValueError("Observed reference population exceeds the declared population")
    metrics = calculate_metrics(gold, predictions)
    metrics.update(
        reference_scope="documentation-only jointly adjudicated labels",
        interpretation="exploratory reference comparison; bootstrap does not remove development bias",
        expected_repositories=expected,
        coverage=len(gold) / expected,
        reference_repositories_with_predictions=len(rows),
        excluded_partial_or_unavailable=expected - len(gold),
        undefined_ratio_policy="zero",
    )
    metrics["baselines"] = {
        "always_negative": calculate_metrics(gold, [[] for _ in gold]),
        "always_positive": calculate_metrics(gold, [list(STAGES) for _ in gold]),
    }
    if gold:
        rng = random.Random("documentation-bootstrap-v1")
        distributions: dict[str, list[float]] = {"macro_f1": [], "micro_f1": []}
        for _ in range(bootstrap):
            ids = [rng.randrange(len(gold)) for _ in gold]
            value = calculate_metrics([gold[i] for i in ids], [predictions[i] for i in ids])
            distributions["macro_f1"].append(value["macro"]["f1"])
            distributions["micro_f1"].append(value["micro"]["f1"])
        metrics["bootstrap"] = {
            "unit": "repository with all six labels",
            "iterations": bootstrap,
            "seed": "documentation-bootstrap-v1",
            "percentile_95_intervals": {
                key: [
                    sorted(vals)[int((bootstrap - 1) * 0.025)],
                    sorted(vals)[int((bootstrap - 1) * 0.975)],
                ]
                for key, vals in distributions.items()
            },
        }
    else:
        metrics["bootstrap"] = None
        metrics["warning"] = "No complete documentation scans; accuracy is not estimable"
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--expected-repositories", type=int, default=100)
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    result = summarize(
        args.run / "documentation_comparison.csv", args.expected_repositories, args.bootstrap
    )
    write_json(args.run / "documentation_metrics.json", result)
    with (args.run / "documentation_metrics.csv").open("w", newline="") as stream:
        fields = [
            "stage",
            "support",
            "TP",
            "FP",
            "TN",
            "FN",
            "precision",
            "recall",
            "f1",
            "accuracy",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["per_stage"])
    print(
        json.dumps(
            {key: result[key] for key in ["repository_count", "coverage", "macro", "micro"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
