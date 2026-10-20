"""Audit paper-association evidence embedded in software metadata, offline.

Selections are textual association candidates, not verified graph publication links.
"""

import csv
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .canonical import read_json, write_csv, write_json
from .openaire import description_texts, file_hash, software_records

DOI = re.compile(r"\b10\.\d{4,9}/[^\s<>\"\u201d]+", re.I)
ARXIV = re.compile(
    r"(?:arxiv\.org/(?:abs|pdf)/|\barxiv\s*:\s*)(\d{4}\.\d{4,5}(?:v\d+)?|[a-z.-]+/\d{7}(?:v\d+)?)",
    re.I,
)
PAPER = re.compile(r"\b(?:paper|study|article|publication|preprint)\b", re.I)
TITLE = re.compile(
    r'\b(?:paper|study|article|publication)\s*(?:(?:entitled|titled|called)\s*)?["\u201c]([^"\u201d\n]{8,300})["\u201d]',
    re.I,
)
NEGATIVE = re.compile(r"\b(?:no|not|without|future|forthcoming|planned|upcoming)\b", re.I)


def clean_identifier(value: str) -> str:
    return value.rstrip(".,;:)]}").casefold()


def paper_evidence(record: dict[str, Any]) -> list[dict[str, str]]:
    """Identify external references; never interpret the software's own PID as a paper."""
    own: set[str] = set()
    for pid in record.get("pids") or []:
        if isinstance(pid, dict) and isinstance(pid.get("value"), str):
            own.add(clean_identifier(pid["value"]))
    for instance in record.get("instances") or []:
        if not isinstance(instance, dict):
            continue
        for pid in instance.get("pids") or []:
            if isinstance(pid, dict) and isinstance(pid.get("value"), str):
                own.add(clean_identifier(pid["value"]))
    for original in record.get("originalIds") or []:
        if isinstance(original, str):
            for match in DOI.finditer(original):
                own.add(clean_identifier(match.group()))
    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for field in ("description", "descriptions", "source", "sources", "documentationUrls"):
        for text in description_texts(record.get(field)):
            for pattern, kind in (
                (DOI, "external_doi_near_paper_mention"),
                (ARXIV, "arxiv_reference"),
                (TITLE, "named_paper_or_study"),
            ):
                for match in pattern.finditer(text):
                    value = clean_identifier(match.group() if pattern is DOI else match.group(1))
                    if pattern is DOI and value in own:
                        continue
                    before = text[max(0, match.start() - 100) : match.start()]
                    context = text[max(0, match.start() - 160) : min(len(text), match.end() + 160)]
                    if NEGATIVE.search(before[-60:]):
                        continue
                    if pattern is DOI and not PAPER.search(context):
                        continue
                    key = (field, kind, value)
                    if key not in seen:
                        seen.add(key)
                        evidence.append(
                            {"field": field, "kind": kind, "reference": value, "excerpt": context}
                        )
    return evidence


def select_metadata(
    candidates: Path, software_tar: Path, output: Path, source_record: str
) -> dict[str, Any]:
    summary = read_json(candidates / "summary.json")
    if (
        summary["source_record"] != source_record
        or file_hash(software_tar) != summary["source_tar_sha256"]
    ):
        raise ValueError("Software archive/release must match the candidate extraction")
    if not summary.get("selection"):
        raise ValueError("Use experiment-context-selected candidates")
    for name in ("software_links.csv", "repositories.csv", "repositories.txt"):
        if file_hash(candidates / name) != summary["outputs"][name]:
            raise ValueError("Candidate checksum mismatch")
    with (candidates / "software_links.csv").open(encoding="utf-8", newline="") as stream:
        links = list(csv.DictReader(stream))
    candidate_ids = {row["openaire_id"] for row in links if row["openaire_id"]}
    selected_ids: set[str] = set()
    seen_ids: set[str] = set()
    counts: Counter[str] = Counter()
    evidence_rows = []
    audit_rows = []
    keys: Counter[str] = Counter()
    for member, line, record in software_records(software_tar):
        if record.get("id") not in candidate_ids:
            continue
        identifier = record["id"]
        seen_ids.add(identifier)
        keys.update(record.keys())
        evidence = paper_evidence(record)
        if evidence:
            selected_ids.add(identifier)
            counts["records_with_textual_association_evidence"] += 1
        else:
            counts["records_without_identified_textual_association"] += 1
        audit_rows.append(
            {
                "software_id": identifier,
                "member": member,
                "line": line,
                "status": "association_candidate" if evidence else "unresolved",
                "evidence_count": len(evidence),
            }
        )
        for item in evidence:
            counts[item["kind"]] += 1
            evidence_rows.append(
                {
                    "software_id": identifier,
                    "member": member,
                    "line": line,
                    **item,
                    "review_status": "unreviewed; publication association not verified",
                }
            )
    if seen_ids != candidate_ids:
        raise ValueError("Some candidate software IDs were not found in matching archive")
    selected_links = [row for row in links if row["openaire_id"] in selected_ids]
    repos = Counter(row["github_repository_url"] for row in selected_links)
    output.mkdir(parents=True, exist_ok=False)
    write_csv(
        output / "software_links.csv",
        ["member", "line", "openaire_id", "original_url", "github_repository_url"],
        selected_links,
    )
    write_csv(
        output / "repositories.csv",
        ["github_repository_url", "software_record_count"],
        [
            {"github_repository_url": repo, "software_record_count": n}
            for repo, n in sorted(repos.items())
        ],
    )
    (output / "repositories.txt").write_text(
        "".join(repo + "\n" for repo in sorted(repos)), encoding="utf-8"
    )
    write_csv(
        output / "publication_evidence.csv",
        ["software_id", "member", "line", "field", "kind", "reference", "excerpt", "review_status"],
        evidence_rows,
    )
    write_csv(
        output / "metadata_audit.csv",
        ["software_id", "member", "line", "status", "evidence_count"],
        audit_rows,
    )
    counts.update(
        {
            "candidate_software_ids": len(candidate_ids),
            "software_ids_with_association_candidates": len(selected_ids),
            "software_ids_unresolved": len(candidate_ids - selected_ids),
            "candidate_unique_repositories": summary["counts"]["unique_github_repositories"],
            "unique_github_repositories": len(repos),
            "retained_software_github_links": len(selected_links),
        }
    )
    report = {
        "schema_version": 1,
        "source_record": source_record,
        "source_tar_sha256": summary["source_tar_sha256"],
        "candidate_summary_sha256": file_hash(candidates / "summary.json"),
        "selection": {
            **summary["selection"],
            "publication_evidence_mode": "software-metadata-text-v1",
            "publication_required": False,
        },
        "counts": dict(counts),
        "upstream_counts": summary["counts"],
        "available_candidate_fields": dict(sorted(keys.items())),
        "coverage": "Textual evidence only; unreviewed references and named studies are association candidates. Absence is unresolved, not proof of no publication. DOI targets are not resolved or type-checked.",
        "reproduction_status": "Historical filter unknown; this is not an exact reproduction or verified fourth-criterion filter. No target count is imposed.",
        "outputs": {
            name: file_hash(output / name)
            for name in (
                "software_links.csv",
                "repositories.csv",
                "repositories.txt",
                "publication_evidence.csv",
                "metadata_audit.csv",
            )
        },
    }
    write_json(output / "summary.json", report)
    stages = [
        ("software_records", summary["counts"]["software_records"]),
        ("experiment_context_records", summary["counts"]["records_matching_description"]),
        ("experiment_github_record_links", summary["counts"]["github_record_links"]),
        ("unique_github_candidates", summary["counts"]["unique_github_repositories"]),
        ("software_ids_with_textual_association", len(selected_ids)),
        ("software_ids_unresolved", len(candidate_ids - selected_ids)),
        ("unique_repositories_with_association_candidates", len(repos)),
    ]
    write_csv(
        output / "funnel.csv",
        ["stage", "count"],
        [{"stage": name, "count": count} for name, count in stages],
    )
    (output / "funnel.md").write_text(
        "# Software metadata evidence funnel\n\n| Stage | Count |\n|---|---:|\n"
        + "".join(f"| {name} | {count} |\n" for name, count in stages)
        + "\nStages mix record, link and repository units; unresolved is not a confirmed exclusion.\n\n"
        + report["coverage"]
        + "\n\n"
        + report["reproduction_status"]
        + "\n",
        encoding="utf-8",
    )
    return report
