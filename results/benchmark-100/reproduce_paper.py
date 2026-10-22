"""Offline reproduction of workbook-derived paper tables, with explicit discrepancy checks.

Usage: uv run --frozen python results/benchmark-100/reproduce_paper.py
Optional original-run inputs: --run PATH and --corpus-predictions PATH.
"""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from lifecycle_mapper import MODES, STAGES  # noqa: E402
from lifecycle_mapper.acquisition import repository_id  # noqa: E402
from lifecycle_mapper.metrics import calculate_metrics  # noqa: E402

HERE = Path(__file__).resolve().parent


def identity(url):
    return repository_id(url.rstrip("/")).casefold()


def binary(value):
    if value in ("0", "0.0"):
        return 0
    if value in ("1", "1.0"):
        return 1
    if value in ("", "Unverified"):
        return None
    raise ValueError(f"Unrecognized source label: {value!r}")


def load_tables(folder=HERE / "workbook"):
    manifest = json.loads((folder / "manifest.json").read_text())
    tables = {}
    for entry in manifest["sheets"]:
        path = folder / entry["csv"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], path
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        assert len(rows) == 101 and all(len(row) == 7 for row in rows), path
        assert rows[0][1:] == list(STAGES), path
        table = {}
        for row in rows[1:]:
            key = identity(row[0])
            assert key not in table, key
            table[key] = dict(zip(STAGES, map(binary, row[1:]), strict=True))
        tables[entry["role"]] = table
    population = set(tables["final_agreement"])
    assert len(population) == 100
    assert all(set(table) == population for table in tables.values())
    return tables, manifest


def evaluate(predictions, reference, cohort=None):
    ids = sorted(reference if cohort is None else cohort)
    eligible = [
        repo for repo in ids if all(predictions[repo][stage] is not None for stage in STAGES)
    ]
    metrics = calculate_metrics(
        [reference[repo] for repo in eligible],
        [[stage for stage in STAGES if predictions[repo][stage] == 1] for repo in eligible],
    )
    metrics["label_accuracy"] = (
        sum(row["TP"] + row["TN"] for row in metrics["per_stage"]) / (6 * len(eligible))
        if eligible
        else None
    )
    metrics["coverage"] = len(eligible) / len(reference)
    metrics["evaluated_repository_ids"] = eligible
    metrics["excluded_repository_ids"] = sorted(set(reference) - set(eligible))
    metrics["unknown_decisions"] = sum(
        value is None for row in predictions.values() for value in row.values()
    )
    metrics["baselines"] = {
        "always_positive": calculate_metrics(
            [reference[repo] for repo in eligible], [list(STAGES) for _ in eligible]
        ),
        "always_negative": calculate_metrics(
            [reference[repo] for repo in eligible], [[] for _ in eligible]
        ),
    }
    return metrics


def annotation_statistics(tables):
    first, second, reference = (
        tables[name] for name in ("reviewer1", "reviewer2", "final_agreement")
    )
    counts = []
    for stage in STAGES:
        agree = sum(first[repo][stage] == second[repo][stage] for repo in reference)
        assert all(
            tables["agreement"][repo][stage] == int(first[repo][stage] == second[repo][stage])
            for repo in reference
        )
        counts.append(
            {
                "stage": stage,
                "agreement": agree,
                "disagreement": 100 - agree,
                "final_positive": sum(reference[repo][stage] for repo in reference),
            }
        )
    return {
        "per_stage": counts,
        "agreement": sum(row["agreement"] for row in counts),
        "disagreement": sum(row["disagreement"] for row in counts),
        "final_positive_labels": sum(row["final_positive"] for row in counts),
        "final_negative_labels": 600 - sum(row["final_positive"] for row in counts),
        "all_six_positive_repositories": sum(all(row.values()) for row in reference.values()),
    }


def compact(metrics):
    return {
        "repositories": metrics["repository_count"],
        "coverage": metrics["coverage"],
        "micro_precision": metrics["micro"]["precision"],
        "micro_recall": metrics["micro"]["recall"],
        "micro_f1": metrics["micro"]["f1"],
        "macro_f1": metrics["macro"]["f1"],
        "label_accuracy": metrics["label_accuracy"],
        "exact_match": metrics["exact_match_accuracy"],
    }


def compare_claims(classifications, claims, table):
    rows = []
    for role, expected in claims[table].items():
        observed = compact(classifications[role])
        for metric, claim in expected.items():
            value = observed[metric]
            rendered = value if metric == "repositories" else round(value, 3)
            status = "matches" if rendered == claim else "differs"
            if (
                status == "differs"
                and metric != "repositories"
                and int(value * 1000) / 1000 == claim
            ):
                status = "rounding_difference"
            rows.append(
                {
                    "table": table,
                    "role": role,
                    "metric": metric,
                    "paper": claim,
                    "computed": value,
                    "rounded_3dp": rendered,
                    "status": status,
                }
            )
    return rows


def evaluate_original_run(run, reference):
    """Recompute from original saved predictions and scan-completeness, never acquire/replay."""
    payloads = {}
    for path in (run / "repositories").glob("*/result.json"):
        digest = path.with_name("result.sha256")
        assert (
            digest.exists()
            and hashlib.sha256(path.read_bytes()).hexdigest() == digest.read_text().strip()
        ), path
        value = json.loads(path.read_bytes())
        key = identity(value["requested_url"])
        assert key not in payloads
        payloads[key] = value
    assert set(payloads) == set(reference), (
        "Original run must cover exactly the 100 reference identities"
    )
    manifest_path = run / "manifest.json"
    configuration = (
        json.loads(manifest_path.read_text()).get("configuration", {})
        if manifest_path.exists()
        else {}
    )
    if configuration.get("repository_count") is not None:
        assert configuration["repository_count"] == len(reference)
    expected_catalog = configuration.get("catalog_sha256")
    if expected_catalog:
        assert all(
            mode.get("rule_catalog_hash") == expected_catalog
            for result in payloads.values()
            for mode in result.get("modes", [])
        ), "Mixed saved catalogs in original run"
    by_mode = {}
    for mode in MODES:
        predictions = {}
        for repo, result in payloads.items():
            found = next((p for p in result.get("modes", []) if p["mode"] == mode), None)
            predictions[repo] = (
                found["predictions"] if found and found["scan_complete"] else dict.fromkeys(STAGES)
            )
        metrics = evaluate(predictions, reference)
        metrics["excluded_decisions_for_evaluation"] = metrics.pop("unknown_decisions")
        metrics["cohort_policy"] = (
            "Original scan_complete flag; incomplete vectors excluded wholesale, not relabeled as observed negatives"
        )
        by_mode[
            "heuristics_"
            + {"documentation-only": "documentation", "code-only": "code", "combined": "combined"}[
                mode
            ]
        ] = metrics
    return by_mode


def summarize_corpus(path):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    identities, keys = set(), set()
    counts = {
        (mode, stage): {"positive": 0, "negative": 0, "unknown": 0}
        for mode in MODES
        for stage in STAGES
    }
    for row in rows:
        repo = row["repository"].removeprefix("https://github.com/").casefold().rstrip("/")
        key = (repo, row["mode"], row["stage"])
        assert key not in keys, f"Duplicate decision: {key}"
        keys.add(key)
        identities.add(repo)
        status = {
            "1": "positive",
            "0": "negative",
            "": "unknown",
            "?": "unknown",
            "null": "unknown",
        }[row["prediction"]]
        counts[(row["mode"], row["stage"])][status] += 1
    assert len(identities) == 386 and len(keys) == 386 * 18, (
        "Expected complete exported rows for 386 attempts"
    )
    return [{"mode": mode, "stage": stage, **values} for (mode, stage), values in counts.items()]


def analyze(run=None, corpus_predictions=None):
    tables, manifest = load_tables()
    claims = json.loads((HERE / "paper_claims.json").read_text())
    annotations = annotation_statistics(tables)
    reference = tables["final_agreement"]
    classifications = {
        name: evaluate(table, reference)
        for name, table in tables.items()
        if name.startswith(("llm_", "heuristics_"))
    }
    common = {}
    for family in ("llm", "heuristics"):
        roles = [f"{family}_{mode}" for mode in ("documentation", "code", "combined")]
        cohort = [
            repo
            for repo in reference
            if all(
                all(value is not None for value in tables[role][repo].values()) for role in roles
            )
        ]
        common[family] = {role: evaluate(tables[role], reference, cohort) for role in roles}
    comparisons = compare_claims(classifications, claims, "table_4") + compare_claims(
        classifications, claims, "table_6"
    )
    original = evaluate_original_run(run, reference) if run else None
    corpus = summarize_corpus(corpus_predictions) if corpus_predictions else None
    corpus_comparison = (
        [
            dict(
                row,
                paper_positive=claims["table_5"][row["stage"]][row["mode"]],
                matches=row["positive"] == claims["table_5"][row["stage"]][row["mode"]],
            )
            for row in corpus
        ]
        if corpus
        else None
    )
    return {
        "inputs": manifest,
        "annotations": annotations,
        "workbook_metrics": classifications,
        "common_binary_complete_cohorts": common,
        "paper_comparison": comparisons,
        "original_run_metrics": original,
        "original_run_paper_comparison": compare_claims(original, claims, "table_4")
        if original
        else None,
        "corpus_stage_counts": corpus,
        "corpus_paper_comparison": corpus_comparison,
        "limitations": [
            "Workbook CSV binary completeness does not establish runtime scan completeness.",
            "Paper Table 4 requires original result.json files to reconstruct the 96/95/95 scan-complete cohorts.",
            "Paper Table 5 requires the original 386-repository predictions export.",
            "Paper Table 7 retains superseded heuristic values and is inconsistent with Table 4.",
            "The combined LLM micro-F1 rounds to 0.795; the paper prints 0.794.",
            "All 100 repositories informed heuristic development; no held-out claim.",
        ],
    }


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(report, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / "reproduction.json").write_text(json.dumps(report, indent=2) + "\n")
    write_csv(output / "annotation_counts.csv", report["annotations"]["per_stage"])
    write_csv(
        output / "workbook_metrics.csv",
        [{"role": role, **compact(values)} for role, values in report["workbook_metrics"].items()],
    )
    write_csv(
        output / "per_stage_metrics.csv",
        [
            {"role": role, **stage}
            for role, values in report["workbook_metrics"].items()
            for stage in values["per_stage"]
        ],
    )
    write_csv(output / "paper_comparison.csv", report["paper_comparison"])
    if report["corpus_stage_counts"]:
        write_csv(output / "corpus_stage_counts.csv", report["corpus_stage_counts"])
    if report["original_run_metrics"]:
        write_csv(
            output / "original_run_metrics.csv",
            [
                {"role": role, **compact(values)}
                for role, values in report["original_run_metrics"].items()
            ],
        )
    status = [
        "# Reproduction status",
        "",
        "Computed from the selected workbook CSVs:",
        "",
        f"- Independent agreement: {report['annotations']['agreement']}/600.",
        f"- Final positive labels: {report['annotations']['final_positive_labels']}/600.",
        "- Full per-stage metrics, own-cohort and common-cohort baselines are in reproduction.json.",
        "",
        "## Material differences from the draft",
        "",
    ]
    status += ["- " + text for text in report["limitations"]]
    status += [
        "",
        "Original 100-run data: "
        + ("supplied and recalculated" if report["original_run_metrics"] else "not supplied"),
        "Original 386 predictions: "
        + ("supplied and recalculated" if report["corpus_stage_counts"] else "not supplied"),
        "",
    ]
    (output / "README.md").write_text("\n".join(status))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        type=Path,
        help="Original completed 100-repository run with checksum-bound result.json files",
    )
    parser.add_argument(
        "--corpus-predictions", type=Path, help="Original pooled 386 predictions.csv"
    )
    parser.add_argument("--output", type=Path, default=HERE / "analysis")
    args = parser.parse_args()
    report = analyze(args.run, args.corpus_predictions)
    write_outputs(report, args.output)
    print(
        json.dumps(
            {
                "annotations": report["annotations"],
                "workbook_metrics": {k: compact(v) for k, v in report["workbook_metrics"].items()},
                "limitations": report["limitations"],
            },
            indent=2,
        )
    )
    print(f"Saved analysis: {args.output}")


if __name__ == "__main__":
    main()
