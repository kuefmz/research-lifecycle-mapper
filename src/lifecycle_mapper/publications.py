"""Join candidate software-record IDs to explicit OpenAIRE publication relations."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .canonical import read_json, write_csv, write_json
from .openaire import file_hash, software_records


def endpoint(record: dict[str, Any], name: str) -> tuple[str, str]:
    value = record.get(name)
    if isinstance(value, dict):
        return str(value.get("id", "")), str(value.get("type", "")).casefold()
    return str(value or ""), str(record.get(name + "Type", "")).casefold()


def select_publications(
    candidates: Path,
    output: Path,
    relations: tuple[Path, ...],
    source_record: str,
    relation_names: tuple[str, ...] = (),
    publication_archives: tuple[Path, ...] = (),
) -> dict[str, Any]:
    if not relations or len(set(p.resolve() for p in relations)) != len(relations):
        raise ValueError("Supply one or more distinct relation archives")
    if any(not p.is_file() for p in (*relations, *publication_archives)):
        raise ValueError("A relation/publication archive does not exist")
    summary = read_json(candidates / "summary.json")
    if summary["source_record"] != source_record:
        raise ValueError("Relation and software source-record declarations must agree")
    if not summary.get("selection"):
        raise ValueError("Use experiment-context-selected software candidates")
    for name in ("software_links.csv", "repositories.csv", "repositories.txt"):
        if file_hash(candidates / name) != summary["outputs"][name]:
            raise ValueError(f"Candidate checksum mismatch: {name}")
    links: dict[str, list[dict[str, str]]] = defaultdict(list)
    missing_id_links = 0
    with (candidates / "software_links.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["openaire_id"].strip():
                links[row["openaire_id"]].append(row)
            else:
                missing_id_links += 1
    # Publication entity archives disambiguate endpoints typed only product/result.
    publication_ids: set[str] = set()
    needed_ids: set[str] = set()
    if publication_archives:
        # Keep only candidate-adjacent IDs, not the entire publication population.
        for path in relations:
            for _, _, record in software_records(path):
                source_id, _ = endpoint(record, "source")
                target_id, _ = endpoint(record, "target")
                if source_id in links and target_id:
                    needed_ids.add(target_id)
                if target_id in links and source_id:
                    needed_ids.add(source_id)
    for path in publication_archives:
        for _, _, record in software_records(path):
            if isinstance(record.get("id"), str) and record["id"] in needed_ids:
                publication_ids.add(record["id"])
    allowed = {name.casefold() for name in relation_names}
    counts: Counter[str] = Counter()
    found: set[tuple[str, str, str, str]] = set()
    matched: set[str] = set()
    output.mkdir(parents=True, exist_ok=False)
    evidence_path = output / "publication_links.csv"
    with evidence_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "software_id",
                "publication_id",
                "relation_name",
                "direction",
                "archive",
                "member",
                "line",
            ]
        )
        for archive in relations:
            for member, line, record in software_records(archive):
                counts["relation_records_scanned"] += 1
                rel = record.get("relType", record.get("reltype", {}))
                name = rel.get("name", "") if isinstance(rel, dict) else ""
                if not isinstance(name, str) or not name:
                    counts["relations_without_name"] += 1
                    continue
                if allowed and name.casefold() not in allowed:
                    continue
                source_id, source_type = endpoint(record, "source")
                target_id, target_type = endpoint(record, "target")
                for software_id, paper_id, paper_type, direction in (
                    (source_id, target_id, target_type, "software-to-publication"),
                    (target_id, source_id, source_type, "publication-to-software"),
                ):
                    if software_id not in links:
                        continue
                    counts["candidate_incident_relations"] += 1
                    # A software identifier/DOI alone is not a publication link.
                    if not paper_id or paper_id in links or paper_type == "software":
                        counts["nonpublication_or_self_endpoints"] += 1
                        continue
                    if paper_type != "publication" and paper_id not in publication_ids:
                        counts["endpoints_not_confirmed_as_publications"] += 1
                        continue
                    key = (software_id, paper_id, name, direction)
                    if key in found:
                        continue
                    found.add(key)
                    matched.add(software_id)
                    counts["publication_relations_retained"] += 1
                    writer.writerow(
                        [software_id, paper_id, name, direction, archive.name, member, line]
                    )
    selected_links = [row for key in sorted(matched) for row in links[key]]
    repos = Counter(row["github_repository_url"] for row in selected_links)
    fields = ["member", "line", "openaire_id", "original_url", "github_repository_url"]
    write_csv(output / "software_links.csv", fields, selected_links)
    write_csv(
        output / "repositories.csv",
        ["github_repository_url", "software_record_count"],
        [
            {"github_repository_url": repo, "software_record_count": count}
            for repo, count in sorted(repos.items())
        ],
    )
    (output / "repositories.txt").write_text(
        "".join(repo + "\n" for repo in sorted(repos)), encoding="utf-8"
    )
    counts.update(
        {
            "candidate_unique_repositories": summary["counts"]["unique_github_repositories"],
            "candidate_software_ids_with_github": len(links),
            "candidate_links_missing_software_id": missing_id_links,
            "software_ids_with_publication": len(matched),
            "software_ids_without_confirmed_publication_in_supplied_archives": len(links)
            - len(matched),
            "retained_software_github_links": len(selected_links),
            "unique_github_repositories": len(repos),
        }
    )
    result = {
        "schema_version": 1,
        "source_record": source_record,
        "source_tar_sha256": summary["source_tar_sha256"],
        "candidate_summary_sha256": file_hash(candidates / "summary.json"),
        "selection": {
            **summary["selection"],
            "publication_required": True,
            "relation_names": sorted(relation_names) or "any named relation in supplied archives",
            "direction": "either; original direction preserved in evidence",
            "endpoint_policy": "Candidate software ID joined to endpoint explicitly typed publication, or present in supplied publication entity archives",
        },
        "counts": dict(counts),
        "upstream_counts": summary["counts"],
        "relation_archives": [{"file": p.name, "sha256": file_hash(p)} for p in relations],
        "publication_archives": [
            {"file": p.name, "sha256": file_hash(p)} for p in publication_archives
        ],
        "coverage": "Only supplied relation archives are searched. No confirmed link means not found in those inputs, not proof that no link exists. Source release is caller-declared.",
        "reproduction_status": "Operationalizes four stated criteria; historical query/metadata fields/relation types and release equivalence remain unverified. Count is never forced to 386.",
        "outputs": {
            name: file_hash(output / name)
            for name in (
                "publication_links.csv",
                "software_links.csv",
                "repositories.csv",
                "repositories.txt",
            )
        },
    }
    write_json(output / "summary.json", result)
    stages = [
        ("software_records", summary["counts"]["software_records"]),
        ("experimental_context_records", summary["counts"]["records_matching_description"]),
        ("candidate_unique_github_repositories", counts["candidate_unique_repositories"]),
        ("software_ids_with_publication", len(matched)),
        ("final_unique_github_repositories", len(repos)),
    ]
    write_csv(
        output / "funnel.csv",
        ["stage", "count"],
        [{"stage": name, "count": n} for name, n in stages],
    )
    (output / "funnel.md").write_text(
        "# Four-criterion selection\n\n| Stage | Count |\n|---|---:|\n"
        + "".join(f"| {name} | {n} |\n" for name, n in stages)
        + "\nRecord and repository stages use different units; repository counts are deduplicated.\n\n"
        + result["coverage"]
        + "\n\n"
        + result["reproduction_status"]
        + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--relations-dir", type=Path)
    parser.add_argument("--relations-tar", type=Path, action="append", default=[])
    parser.add_argument("--publication-tar", type=Path, action="append", default=[])
    parser.add_argument("--relation-name", action="append", default=[])
    parser.add_argument("--source-record", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    relations = args.relations_tar + (
        sorted(args.relations_dir.glob("*.tar")) if args.relations_dir else []
    )
    try:
        print(
            json.dumps(
                select_publications(
                    args.candidates,
                    args.output,
                    tuple(relations),
                    args.source_record,
                    tuple(args.relation_name),
                    tuple(args.publication_tar),
                ),
                indent=2,
            )
        )
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
