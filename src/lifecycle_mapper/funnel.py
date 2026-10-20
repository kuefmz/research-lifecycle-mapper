"""Reconcile extraction stages, legacy candidates, annotation and run coverage."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .batch import read_inputs
from .canonical import read_json, write_csv, write_json
from .openaire import file_hash, normalize_github


def identities(path: Path, worksheet: str = "Agreement Final", column: str = "B") -> set[str]:
    result = set()
    for row in read_inputs(path, repository_column=column, worksheet=worksheet):
        url = normalize_github(row["url"])
        if url is None:
            raise ValueError("Invalid GitHub repository identity in cohort")
        result.add(url)
    return result


def extraction(directory: Path) -> tuple[dict[str, Any], set[str]]:
    summary = read_json(directory / "summary.json")
    for name in ("repositories.csv", "software_links.csv", "repositories.txt"):
        if file_hash(directory / name) != summary["outputs"][name]:
            raise ValueError(f"Extraction checksum mismatch: {name}")
    repos = identities(directory / "repositories.csv")
    if len(repos) != summary["counts"]["unique_github_repositories"]:
        raise ValueError("Extraction count mismatch")
    return summary, repos


def build_funnel(
    full: Path,
    filtered: Path,
    legacy: Path,
    benchmark: Path,
    output: Path,
    worksheet: str = "Agreement Final",
    column: str = "B",
    runs: tuple[Path, ...] = (),
    paper_links: Path | None = None,
    publication_extraction: Path | None = None,
) -> dict[str, Any]:
    full_summary, all_repos = extraction(full)
    selected_summary, selected = extraction(filtered)
    for key in ("source_record", "source_tar_sha256"):
        if full_summary[key] != selected_summary[key]:
            raise ValueError("Extractions must use the same source release and archive")
    if full_summary.get("selection") or not selected_summary.get("selection"):
        raise ValueError("Require full unfiltered and description-filtered extractions")
    if not selected <= all_repos:
        raise ValueError("Description-selected repositories are not a subset of full extraction")
    old = identities(legacy, worksheet, column)
    annotated = identities(benchmark)
    union = selected | old
    evidence: dict[str, set[str]] = {}
    if paper_links:
        with paper_links.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not {"repository_url", "paper_identifier"} <= set(reader.fieldnames or []):
                raise ValueError("Paper links need repository_url,paper_identifier columns")
            for row in reader:
                url = normalize_github(row["repository_url"])
                paper = row["paper_identifier"].strip()
                if url is None or not paper:
                    raise ValueError("Paper-link rows need valid repository URLs and identifiers")
                evidence.setdefault(url, set()).add(paper)
    stages: list[dict[str, Any]] = []

    def stage(name: str, count: int, unit: str, scope: str) -> None:
        stages.append(dict(stage=name, count=count, unit=unit, scope=scope))

    fc, sc = full_summary["counts"], selected_summary["counts"]
    for key in ("software_records", "records_with_repository_field", "github_record_links"):
        stage(
            "full_" + key,
            fc.get(key, 0),
            "records" if key != "github_record_links" else "links",
            "full dump",
        )
    stage("full_unique_github_candidates", len(all_repos), "repositories", "full dump")
    for key in (
        "records_with_description_text",
        "records_matching_description",
        "records_excluded_by_description",
        "selected_records_with_repository_field",
    ):
        stage(key, sc.get(key, 0), "records", "description selection")
    stage(
        "records_missing_description",
        sc["software_records"] - sc["records_with_description_text"],
        "records",
        "description selection",
    )
    stage(
        "descriptions_present_nonmatching",
        sc["records_with_description_text"] - sc["records_matching_description"],
        "records",
        "description selection",
    )
    stage(
        "selected_github_record_links",
        sc.get("github_record_links", 0),
        "links",
        "description selection",
    )
    cohorts = {
        "description_candidates": selected,
        "legacy_candidates": old,
        "intersection": selected & old,
        "description_only": selected - old,
        "legacy_only": old - selected,
        "union": union,
        "legacy_in_current_dump": old & all_repos,
        "legacy_absent_current_dump": old - all_repos,
        "annotated": annotated,
        "annotated_in_description": annotated & selected,
        "annotated_in_legacy": annotated & old,
        "annotated_in_union": annotated & union,
    }
    for name, cohort in cohorts.items():
        stage(name, len(cohort), "repositories", "set reconciliation; not sequential exclusions")
    evidenced = set(evidence)
    graph_publication_count = None
    if publication_extraction:
        graph_summary, graph_selected = extraction(publication_extraction)
        if graph_summary.get("candidate_summary_sha256") != file_hash(filtered / "summary.json"):
            raise ValueError("Publication selection must derive from this filtered extraction")
        if not graph_selected <= selected:
            raise ValueError("Publication selection is not a subset of description candidates")
        graph_publication_count = len(graph_selected)
        stage(
            "publication_linked_description",
            len(graph_selected),
            "repositories",
            "explicit graph publication endpoints in supplied archives",
        )
        stage(
            "publication_linked_description_in_legacy",
            len(graph_selected & old),
            "repositories",
            "graph-selected overlap with historical cohort",
        )
        stage(
            "publication_linked_description_in_benchmark",
            len(graph_selected & annotated),
            "repositories",
            "graph-selected overlap with annotated cohort",
        )
        if paper_links:
            raise ValueError("Use either graph publication extraction or supplied paper links")
    if paper_links:
        cohorts["paper_linked_description"] = selected & evidenced
        cohorts["paper_linked_description_in_legacy"] = selected & evidenced & old
        for name in ("paper_linked_description", "paper_linked_description_in_legacy"):
            stage(
                name,
                len(cohorts[name]),
                "repositories",
                "description candidates with supplied publication-link evidence",
            )
        stage(
            "union_with_supplied_paper_evidence",
            len(union & evidenced),
            "repositories",
            "supplied evidence; not bibliographically verified",
        )
    run_reports = []
    for number, run in enumerate(runs, 1):
        manifest = read_json(run / "manifest.json")
        counts: Counter[str] = Counter()
        seen: set[str] = set()
        for path in sorted((run / "repositories").glob("*/result.json")):
            if file_hash(path) != path.with_name("result.sha256").read_text().strip():
                raise ValueError("Checkpoint checksum mismatch; refresh after checkpoint completes")
            result = read_json(path)
            url = normalize_github(result["requested_url"])
            if url is None or url in seen:
                raise ValueError("Invalid or duplicate requested repository in run")
            seen.add(url)
            counts["checkpointed"] += 1
            counts["in_union"] += url in union
            counts["outside_union"] += url not in union
            counts["acquired"] += bool(result.get("commit"))
            counts["complete"] += bool(result.get("complete"))
            counts["failed"] += bool(result.get("error"))
            counts["partial"] += not result.get("complete") and not result.get("error")
            if result.get("selected_branch") in {"main", "master"}:
                counts[result["selected_branch"]] += 1
        expected = manifest["configuration"]["repository_count"]
        for key in ("checkpointed", "acquired", "complete", "failed", "partial", "main", "master"):
            stage(
                f"run_{number}_{key}",
                counts[key],
                "repositories",
                f"run {number}; separate denominator",
            )
        stage(
            f"run_{number}_pending",
            expected - counts["checkpointed"],
            "repositories",
            f"run {number}",
        )
        run_reports.append(
            {
                "run_number": number,
                "manifest_sha256": file_hash(run / "manifest.json"),
                "requested": expected,
                "counts": dict(counts),
            }
        )
    output.mkdir(parents=True, exist_ok=True)
    for name in ("union", "intersection", "description_only", "legacy_only"):
        write_csv(
            output / (name + "_repositories.csv"),
            ["github_repository_url"],
            [{"github_repository_url": url} for url in sorted(cohorts[name])],
        )
    eligible_path = output / "paper_linked_description_repositories.csv"
    if paper_links:
        write_csv(
            eligible_path,
            ["github_repository_url"],
            [{"github_repository_url": url} for url in sorted(cohorts["paper_linked_description"])],
        )
    else:
        eligible_path.unlink(missing_ok=True)
    write_csv(
        output / "membership.csv",
        [
            "github_repository_url",
            "description_selected",
            "legacy_candidate",
            "annotated",
            "in_current_dump",
            "supplied_paper_identifiers",
        ],
        [
            {
                "github_repository_url": url,
                "description_selected": int(url in selected),
                "legacy_candidate": int(url in old),
                "annotated": int(url in annotated),
                "in_current_dump": int(url in all_repos),
                "supplied_paper_identifiers": json.dumps(sorted(evidence.get(url, set()))),
            }
            for url in sorted(union | annotated)
        ],
    )
    write_csv(output / "funnel.csv", ["stage", "count", "unit", "scope"], stages)
    report = {
        "schema_version": 1,
        "source_record": full_summary["source_record"],
        "source_tar_sha256": full_summary["source_tar_sha256"],
        "input_hashes": {
            "full_summary": file_hash(full / "summary.json"),
            "filtered_summary": file_hash(filtered / "summary.json"),
            "legacy": file_hash(legacy),
            "benchmark": file_hash(benchmark),
            "paper_links": file_hash(paper_links) if paper_links else None,
            "publication_selection": file_hash(publication_extraction / "summary.json")
            if publication_extraction
            else None,
        },
        "legacy_claim": "Historical cohort reported by its collector to meet four criteria: OpenAIRE software, experimental metadata context, GitHub repository and at least one linked research publication. Exact historical query, metadata fields and relation evidence are not reconstructed from membership.",
        "eligibility": {
            "criteria": [
                "OpenAIRE software",
                "experimental metadata context",
                "GitHub repository",
                "linked research publication",
            ],
            "current_context_rule": "Whole-word experiment/experiments in description(s) only; narrower than description or associated metadata.",
            "description_candidate_count": len(selected),
            "publication_linked_description_count": graph_publication_count
            if publication_extraction
            else len(selected & evidenced)
            if paper_links
            else None,
            "publication_linkage_status": "Explicit graph publication endpoints in supplied archives; archive coverage must be reported"
            if publication_extraction
            else "Supplied evidence; verify publication identifiers and relation semantics"
            if paper_links
            else "Pending; candidate count is not final eligible count",
            "union_role": "Exploratory reconciliation only; union does not establish all four eligibility criteria.",
        },
        "paper_evidence_status": "Explicit graph publication endpoints in supplied archives"
        if publication_extraction
        else "Supplied identifiers; not independently verified"
        if paper_links
        else "Not supplied; paper-linked counts unknown",
        "identity_policy": "Normalized requested GitHub URLs; no live rename/alias resolution",
        "selection": selected_summary["selection"],
        "stages": stages,
        "runs": run_reports,
    }
    write_json(output / "funnel.json", report)
    lines = [
        "# Corpus funnel",
        "",
        "Overlapping cohorts are sets, not consecutive filters. Counts use the units shown.",
        "",
        "| Stage | Count | Unit |",
        "|---|---:|---|",
    ]
    lines += [f"| {row['stage']} | {row['count']} | {row['unit']} |" for row in stages]
    lines += [
        "",
        report["legacy_claim"],
        "",
        "Paper evidence: " + report["paper_evidence_status"],
        "",
        "Final eligibility requires all four criteria. "
        + report["eligibility"]["publication_linkage_status"],
        "",
        report["eligibility"]["current_context_rule"],
        "",
        "Union includes all supplied legacy candidates, whether or not they match the description filter. Run sections have separate denominators and must not be summed across overlapping runs.",
        "",
    ]
    (output / "funnel.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-extraction", type=Path, required=True)
    parser.add_argument("--filtered-extraction", type=Path, required=True)
    parser.add_argument("--legacy-repositories", type=Path, required=True)
    parser.add_argument(
        "--benchmark", type=Path, default=Path("data/research_lifecycle_benchmark_100_msr27.json")
    )
    parser.add_argument("--legacy-worksheet", default="Agreement Final")
    parser.add_argument("--legacy-column", default="B")
    parser.add_argument("--paper-links", type=Path)
    parser.add_argument("--publication-extraction", type=Path)
    parser.add_argument("--run", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_funnel(
            args.full_extraction,
            args.filtered_extraction,
            args.legacy_repositories,
            args.benchmark,
            args.output,
            args.legacy_worksheet,
            args.legacy_column,
            tuple(args.run),
            args.paper_links,
            args.publication_extraction,
        )
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
