"""Print saved benchmark metrics and export paper tables without acquisition or replay."""

import argparse
from pathlib import Path
from typing import Any

from . import MODES
from .canonical import read_json, write_json
from .openaire import file_hash


def number(value: float | None, count: int, percent: bool = False) -> str:
    if value is None or count == 0:
        return "n/a"
    return f"{100 * value:.1f}%" if percent else f"{value:.3f}"


def mode_table(metrics: dict[str, Any], expected: int) -> str:
    lines = [
        "| Mode | Evaluated | P | R | Micro F1 | Macro F1 | Label agreement | Exact match |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in MODES:
        item = metrics[mode]
        count = item["repository_count"]
        lines.append(
            "| "
            + " | ".join(
                [
                    mode,
                    f"{count}/{expected}",
                    number(item["micro"]["precision"], count),
                    number(item["micro"]["recall"], count),
                    number(item["micro"]["f1"], count),
                    number(item["macro"]["f1"], count),
                    number(item["label_accuracy"], count, True),
                    number(item["exact_match_accuracy"], count, True),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def build_summary(run: Path, assessment: Path, output: Path) -> str:
    report = read_json(assessment / "all_modes_metrics.json")
    if report.get("replayed_offline"):
        raise ValueError(
            "Paper summary requires saved run predictions, not an offline replay assessment"
        )
    summary = read_json(run / "summary.json")
    manifest = read_json(run / "manifest.json")
    if report["source_run_manifest_sha256"] != file_hash(run / "manifest.json"):
        raise ValueError("Assessment does not match the supplied run manifest")
    expected = report["expected_repositories"]
    if (
        summary["repository_count"] != expected
        or summary["finished"] != expected
        or not summary.get("all_repositories_accounted_for")
    ):
        raise ValueError("Paper summary requires all expected repository attempts to finish")
    if sum(summary[k] for k in ["complete", "partial", "failed"]) != expected:
        raise ValueError("Run status counts do not reconcile")
    own = {m: report["per_mode"][m]["all"] for m in MODES}
    common = report["common_complete_cohort"]
    counts = {item["repository_count"] for item in common.values()}
    if len(counts) != 1:
        raise ValueError("Common-cohort metrics require identical repository denominators")
    config = manifest["configuration"]
    elapsed = summary.get("session_wall_seconds")
    runtime = f"{elapsed / 60:.1f} minutes" if elapsed is not None else "not recorded"
    lines = [
        "# Benchmark results",
        "",
        f"Attempted {summary['finished']}/{expected}; complete {summary['complete']}; partial {summary['partial']}; failed {summary['failed']}; timed out {summary.get('timed_out', 0)}.",
        f"Session wall time: {runtime}. REST calls this invocation: {summary.get('session_api_network_calls', 'not recorded')}.",
        f"Repository deadline: {config.get('repository_timeout_seconds', 'not recorded')} seconds. Per-file cap: {config.get('max_bytes', 'not recorded')} bytes (0 means unlimited).",
        "",
        "## Each mode on its complete scans",
        "",
        mode_table(own, expected),
        "",
        "Unknown/incomplete scans are excluded from these metrics, not counted as negative predictions. Denominators can differ between modes.",
        "",
        "## Same complete repositories across all modes",
        "",
        mode_table(common, expected),
        "",
        "Use this common-cohort table for comparisons between modes. Code-only and combined values measure agreement with the supplied reference; they are not independently verified code accuracy.",
        "",
        "## Always-positive baseline on each matching cohort",
        "",
        "| Mode | Evaluated | Classifier micro F1 | Always-positive micro F1 | Difference |",
        "|---|---:|---:|---:|---:|",
    ]
    for mode in MODES:
        item = own[mode]
        n = item["repository_count"]
        baseline = item["baselines"]["always_positive"]["micro"]["f1"]
        score = item["micro"]["f1"]
        lines.append(
            f"| {mode} | {n}/{expected} | {number(score, n)} | {number(baseline, n)} | {number(score - baseline, n)} |"
        )
    lines += [
        "",
        "## Documentation stage results",
        "",
        "| Stage | TP | FP | FN | Support | P | R | F1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in own["documentation-only"]["per_stage"]:
        n = own["documentation-only"]["repository_count"]
        lines.append(
            "| "
            + " | ".join(
                [
                    row["stage"],
                    str(row["TP"]),
                    str(row["FP"]),
                    str(row["FN"]),
                    str(row["support"]),
                    number(row["precision"], n),
                    number(row["recall"], n),
                    number(row["f1"], n),
                ]
            )
            + " |"
        )
    doc = own["documentation-only"]
    combined = own["combined"]
    lines += [
        "",
        "## Draft results paragraph",
        "",
        f"We attempted to analyse {expected} repositories. Of these, {summary['complete']} completed all requested scans, {summary['partial']} were partial, and {summary['failed']} failed. "
        f"Documentation-based predictions achieved micro-precision {number(doc['micro']['precision'], doc['repository_count'])}, micro-recall {number(doc['micro']['recall'], doc['repository_count'])}, and micro-F1 {number(doc['micro']['f1'], doc['repository_count'])} on {doc['repository_count']} repositories. "
        f"The union of documentation and code evidence achieved reference-agreement micro-F1 {number(combined['micro']['f1'], combined['repository_count'])} on {combined['repository_count']} repositories. "
        f"An always-positive baseline achieved micro-F1 {number(doc['baselines']['always_positive']['micro']['f1'], doc['repository_count'])} on the documentation comparison cohort.",
        "",
        "These are development-set results: the benchmark informed rule development. No untouched-holdout or independent code-ground-truth claim is supported. Report the baselines and coverage alongside F1.",
        "",
        f"Reference SHA-256: `{report['reference_sha256']}`.",
        f"Run manifest SHA-256: `{report['source_run_manifest_sha256']}`.",
        "Rule catalogue hashes: "
        + ", ".join(f"`{value}`" for value in report["rule_catalog_hashes"])
        + ".",
    ]
    markdown = "\n".join(lines) + "\n"
    latex = [
        "% Development reference agreement; incomplete scans excluded.",
        "\\begin{tabular}{lrrrrrr}",
        r"Mode & $N$ & Precision & Recall & Micro-F1 & Macro-F1 & Exact match \\",
        r"\hline",
    ]
    for mode in MODES:
        item = common[mode]
        n = item["repository_count"]
        values = [
            mode,
            str(n),
            number(item["micro"]["precision"], n),
            number(item["micro"]["recall"], n),
            number(item["micro"]["f1"], n),
            number(item["macro"]["f1"], n),
            number(item["exact_match_accuracy"], n),
        ]
        latex.append(" & ".join(values) + r" \\")
    latex += [
        "\\end{tabular}",
        f"% Expected repositories: {expected}. All three modes use the same complete cohort.",
    ]
    output.mkdir(parents=True, exist_ok=True)
    (output / "paper_summary.md").write_text(markdown)
    (output / "paper_modes.tex").write_text("\n".join(latex) + "\n")
    write_json(
        output / "paper_summary.json",
        {
            "source_assessment_sha256": file_hash(assessment / "all_modes_metrics.json"),
            "source_run_manifest_sha256": report["source_run_manifest_sha256"],
            "reference_sha256": report["reference_sha256"],
            "run_summary": summary,
            "per_mode_complete": own,
            "common_complete": common,
            "development_only": True,
        },
    )
    return markdown


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--assessment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(build_summary(args.run, args.assessment, args.output), end="")
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
