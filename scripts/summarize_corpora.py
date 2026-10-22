"""Write identically structured stage-count tables for the three paper corpora."""

import csv
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODES = ("documentation-only", "code-only", "combined")
STAGES = ("Collection", "Processing", "Method", "Experimentation", "Evaluation", "Dissemination")
FIELDS = (
    "mode",
    "stage",
    "positive",
    "negative",
    "unknown",
    "total",
    "positive_percent_all",
    "unknown_percent_all",
)


def normalize(rows, total):
    result = []
    indexed = {(r["mode"], r["stage"]): r for r in rows}
    assert len(indexed) == len(rows) == 18
    for mode in MODES:
        for stage in STAGES:
            row = indexed[mode, stage]
            values = {k: int(row[k]) for k in ("positive", "negative", "unknown")}
            assert sum(values.values()) == total
            result.append(
                dict(
                    mode=mode,
                    stage=stage,
                    **values,
                    total=total,
                    positive_percent_all=round(100 * values["positive"] / total, 4),
                    unknown_percent_all=round(100 * values["unknown"] / total, 4),
                )
            )
    return result


def benchmark_counts():
    path = ROOT / "results/benchmark-100/predictions.csv"
    rows = list(csv.DictReader(path.open(newline="")))
    assert len(rows) == 1800
    assert len({r["repository"].casefold() for r in rows}) == 100
    assert len({(r["repository"].casefold(), r["mode"], r["stage"]) for r in rows}) == 1800
    counts = Counter((r["mode"], r["stage"], r["prediction"]) for r in rows)
    return [
        dict(
            mode=mode,
            stage=stage,
            positive=counts[mode, stage, "1"],
            negative=counts[mode, stage, "0"],
            unknown=counts[mode, stage, "?"],
        )
        for mode in MODES
        for stage in STAGES
    ]


def write_collection(name, total, rows, source, limitations):
    folder = ROOT / "results" / name
    rows = normalize(rows, total)
    with (folder / "stage_counts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (folder / "aggregate_summary.json").write_text(
        json.dumps(
            {
                "repository_count": total,
                "scope": source,
                "stage_counts": rows,
                "interpretation": "Counts describe detected evidence; unknowns are not negative predictions.",
                "limitations": limitations,
            },
            indent=2,
        )
        + "\n"
    )
    indexed = {(r["mode"], r["stage"]): r for r in rows}
    slash = chr(92)
    latex = [
        slash + "begin{table*}[t]",
        slash + "centering",
        slash
        + "caption{Lifecycle evidence detected across "
        + f"{total:,}"
        + " repositories. Each cell gives positive / negative / unknown counts. Unknowns are retained in the population and are not negative predictions.}",
        slash + "label{tab:" + name + "}",
        slash + "begin{tabular}{lrrr}",
        slash + "toprule",
        "Stage & Documentation & Source code & Combined " + slash * 2,
        slash + "midrule",
    ]
    for stage in STAGES:
        latex.append(
            stage
            + " & "
            + " & ".join(
                " / ".join(
                    str(indexed[mode, stage][key]) for key in ("positive", "negative", "unknown")
                )
                for mode in MODES
            )
            + " "
            + slash * 2
        )
    latex += [slash + "bottomrule", slash + "end{tabular}", slash + "end{table*}", ""]
    (folder / "paper_table.tex").write_text("\n".join(latex))
    if total == 3211:
        paragraph = (
            "Table~\\ref{tab:corpus-3211} summarizes lifecycle evidence detected across the 3,211-repository corpus. "
            "Combined documentation and source-code analysis identified Dissemination evidence in 2,024 repositories (63.03\\%) "
            "and Experimentation evidence in 2,007 (62.50\\%), followed by Method in 1,324 (41.23\\%), Evaluation in 1,237 "
            "(38.52\\%), Processing in 1,219 (37.96\\%), and Collection in 408 (12.71\\%). Percentages use all 3,211 "
            "repositories as the denominator; unknown predictions remain separate from negatives. Compared with documentation alone, "
            "combined analysis identified 631 additional Method positives and 455 additional Evaluation positives, indicating "
            "complementary detected evidence. These descriptive counts do not establish the absence of research activities, "
            "full-corpus classification accuracy, or successful reproduction.\n"
        )
    else:
        paragraph = (
            f"Table~\\ref{{tab:{name}}} reports positive, negative and unknown lifecycle-evidence counts "
            f"for all {total:,} repositories across documentation, source-code and combined modes. "
            "The combined mode uses the union of detected documentation and code evidence. "
            "Unknown predictions are retained separately from negatives; these counts describe detected evidence.\n"
        )
    (folder / "paper_paragraph.tex").write_text(paragraph)
    print(name, "18 stage/mode rows; denominator", total)


def main():
    write_collection(
        "benchmark-100",
        100,
        benchmark_counts(),
        "Complete 100-repository heuristic predictions from the original assessment.",
        [
            "All-attempt stage counts differ from complete-scan evaluation cohorts of 96/95/95.",
            "All 100 repositories informed development; no held-out claim.",
        ],
    )
    base = ROOT / "results/corpus-386"
    supplied = list(csv.DictReader((base / "stage_counts.csv").open(newline="")))
    provenance_path = base / "stage_counts_provenance.json"
    provenance = json.loads(provenance_path.read_text())
    original_hash = hashlib.sha256((base / "stage_counts.csv").read_bytes()).hexdigest()
    assert original_hash == provenance["sha256"]
    write_collection(
        "corpus-386",
        386,
        supplied,
        "Author-supplied pooled aggregate counts for the complete 386-repository corpus.",
        [
            "Original row-level export and evidence remain pending; base aggregates are supplied results.",
            "No full-corpus accuracy claim without human labels.",
        ],
    )
    provenance.setdefault("original_export_sha256", original_hash)
    provenance["sha256"] = hashlib.sha256((base / "stage_counts.csv").read_bytes()).hexdigest()
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n")
    path = ROOT / "results/corpus-3211/reproduce_results.py"
    spec = importlib.util.spec_from_file_location("full_corpus", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module.reproduce()
    write_collection(
        "corpus-3211",
        3211,
        rows,
        "Full-population aggregates from supplied 386 counts and final saved log decisions for the disjoint remainder.",
        [
            "Original 386 row-level export is unavailable; base aggregates are author-supplied.",
            "Logs do not establish complete pinned-commit and evidence provenance.",
            "Full-population mode-complete repository totals cannot be recovered from stage aggregates.",
            "No full-population accuracy or F1 without human labels.",
        ],
    )


if __name__ == "__main__":
    main()
