"""Offline, separate-mode evaluation and documentation error review.

The final agreement contains mixed-source evidence hyperlinks. Each mode measures
agreement with those labels, not independently validated source-specific accuracy.
"""

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from . import MODES, STAGES
from .acquisition import replay
from .analysis import analyze_modes
from .benchmark import calculate_metrics, implementation_hash
from .canonical import contained, read_json, sha256, write_csv, write_json
from .dataset import dataset_reference
from .openaire import file_hash
from .reference import final_reference
from .notebooks import expand_notebooks


def mode_metrics(rows: list[dict[str, Any]], expected: int) -> dict[str, Any]:
    gold = [row["gold"] for row in rows]
    predictions = [[stage for stage in STAGES if row["prediction"][stage]] for row in rows]
    result = calculate_metrics(gold, predictions)
    result["label_accuracy"] = (
        (sum(item["TP"] + item["TN"] for item in result["per_stage"]) / (len(rows) * 6))
        if rows
        else None
    )
    result["coverage"] = len(rows) / expected if expected else 0.0
    result["expected_repositories"] = expected
    result["baselines"] = {
        "always_negative": calculate_metrics(gold, [[] for _ in rows]),
        "always_positive": calculate_metrics(gold, [list(STAGES) for _ in rows]),
    }
    if not rows:
        result["warning"] = "No complete scans; accuracy is not estimable"
    return result


def assess(
    run: Path,
    reference: Path,
    output: Path,
    reanalyze: bool = False,
    rules_dir: Path | None = None,
    review_documents: bool = False,
) -> dict[str, Any]:
    if rules_dir and not reanalyze:
        raise ValueError("--rules-dir requires --replay")
    gold = (
        final_reference(reference)
        if reference.suffix.lower() == ".xlsx"
        else dataset_reference(read_json(reference))
    )
    if output.exists():
        raise ValueError("Use a new assessment output directory to preserve earlier results")
    ordered = sorted(
        gold, key=lambda repo: sha256(("documentation-development-v1:" + repo).encode())
    )
    n_development = math.floor(len(ordered) * 0.8)
    development = set(ordered[:n_development])
    partition = {
        repo: "development" if repo in development else "operational_holdout" for repo in gold
    }
    collected: dict[str, dict[str, dict[str, Any]]] = {mode: {} for mode in MODES}
    review_rows = []
    predictions = []
    errors = []
    diagnostics = []
    provenance = []
    seen = set()
    catalogs = set()
    for path in sorted((run / "repositories").glob("*/result.json")):
        if file_hash(path) != path.with_name("result.sha256").read_text().strip():
            raise ValueError("Checkpoint checksum mismatch")
        result = read_json(path)
        repo = result["requested_url"].removeprefix("https://github.com/").casefold()
        if repo not in gold:
            continue
        if repo in seen:
            raise ValueError("Duplicate reference repository checkpoint")
        seen.add(repo)
        modes = result.get("modes", [])
        snapshot = contained(run, result["snapshot"]) if result.get("snapshot") else None
        manifest = None
        if reanalyze and snapshot:
            manifest, _ = replay(snapshot, result["snapshot_sha256"])
            modes = analyze_modes(
                snapshot, MODES, expected_hash=result["snapshot_sha256"], rules_dir=rules_dir
            )
        provenance.append(
            {
                "repository": repo,
                "checkpoint_sha256": file_hash(path),
                "snapshot_sha256": result.get("snapshot_sha256"),
                "commit": result.get("commit"),
            }
        )
        for payload in modes:
            mode = payload["mode"]
            if mode not in MODES:
                raise ValueError("Unexpected prediction mode")
            if repo in collected[mode]:
                raise ValueError("Duplicate repository mode")
            catalogs.add(payload.get("rule_catalog_hash", "unknown"))
            complete = bool(payload["scan_complete"])
            if complete:
                if any(not isinstance(payload["predictions"].get(stage), bool) for stage in STAGES):
                    raise ValueError("Complete scans need six boolean predictions")
                collected[mode][repo] = {"gold": gold[repo], "prediction": payload["predictions"]}
            for stage in STAGES:
                value = payload["predictions"].get(stage)
                prediction = "" if value is None else int(value)
                row = {
                    "repository": repo,
                    "commit": result.get("commit", ""),
                    "partition": partition[repo],
                    "mode": mode,
                    "stage": stage,
                    "human_documentation": gold[repo][stage],
                    "prediction": prediction,
                    "scan_complete": complete,
                }
                predictions.append(row)
                if (
                    mode == "documentation-only"
                    and complete
                    and bool(value) != bool(gold[repo][stage])
                ):
                    accepted = [e for e in payload["evidence"] if e["stage"] == stage]
                    excluded = [e for e in payload["excluded_evidence"] if e["stage"] == stage]
                    error = {
                        **row,
                        "outcome": "false-positive" if value else "false-negative",
                        "accepted_evidence": json.dumps(accepted, ensure_ascii=False),
                        "excluded_evidence": json.dumps(excluded, ensure_ascii=False),
                    }
                    errors.append(error)
        if review_documents and partition[repo] == "development" and snapshot:
            mismatches = [e["stage"] for e in errors if e["repository"] == repo]
            if mismatches:
                review_manifest, contents = replay(snapshot, result["snapshot_sha256"])
                review_manifest, contents = expand_notebooks(review_manifest, contents)
                review_rows.append(
                    {
                        "repository": repo,
                        "partition": "development",
                        "mismatch_stages": mismatches,
                        "snapshot_sha256": result["snapshot_sha256"],
                        "documentation": [
                            {
                                "path": item["path"],
                                "sha256": item["sha256"],
                                "text": contents[item["path"]],
                                **{
                                    key: item[key]
                                    for key in ("notebook_path", "notebook_cell")
                                    if key in item
                                },
                            }
                            for item in review_manifest["files"]
                            if item["source"] == "documentation" and item["status"] == "captured"
                        ],
                    }
                )
        if snapshot and manifest is None:
            manifest = read_json(snapshot / "manifest.json")
            if file_hash(snapshot / "manifest.json") != result["snapshot_sha256"]:
                raise ValueError("Snapshot manifest checksum mismatch")
        if snapshot and manifest and any(f["source"] == "notebook" for f in manifest["files"]):
            manifest, contents = replay(snapshot, result["snapshot_sha256"])
            manifest, _ = expand_notebooks(manifest, contents)
        doc = next((m for m in modes if m["mode"] == "documentation-only"), None)
        if doc:
            diagnostics.append(
                {
                    "repository": repo,
                    "partition": partition[repo],
                    "documentation_scan_complete": doc["scan_complete"],
                    "analysis_errors": doc.get("analysis_errors", []),
                    "captured_documentation_files": sum(
                        f["source"] == "documentation" and f["status"] == "captured"
                        for f in manifest["files"]
                    )
                    if manifest
                    else None,
                    "unavailable_documentation_files": [
                        {"path": f["path"], "reason": f.get("reason")}
                        for f in manifest["files"]
                        if f["source"] == "documentation" and f["status"] == "unavailable"
                    ]
                    if manifest
                    else [],
                    "excluded_reason_counts": dict(
                        Counter(
                            reason
                            for e in doc["excluded_evidence"]
                            for reason in e.get("exclusion_reasons", [])
                        )
                    ),
                }
            )
    observed = {(row["repository"], row["mode"], row["stage"]) for row in predictions}
    for repo in sorted(gold):
        for mode in MODES:
            for stage in STAGES:
                if (repo, mode, stage) not in observed:
                    predictions.append(
                        {
                            "repository": repo,
                            "commit": "",
                            "partition": partition[repo],
                            "mode": mode,
                            "stage": stage,
                            "human_documentation": gold[repo][stage],
                            "prediction": "",
                            "scan_complete": False,
                        }
                    )
    common = set.intersection(*(set(collected[m]) for m in MODES))
    report: dict[str, Any] = {
        "schema_version": 1,
        "reference_sha256": file_hash(reference),
        "reference_scope": "joint final_agreement; mixed-source evidence links verified in live-sheet audit",
        "legacy_field_note": "human_documentation is a legacy column name for final_agreement, not a source-scope guarantee",
        "expected_repositories": len(gold),
        "reference_repositories_with_checkpoints": len(seen),
        "replayed_offline": reanalyze,
        "source_run_manifest_sha256": file_hash(run / "manifest.json"),
        "assessment_implementation_sha256": implementation_hash(
            Path(__file__).resolve().parents[2]
        ),
        "rule_catalog_hashes": sorted(catalogs),
        "partition_policy": "Legacy operational 80/20 grouping retained for compatibility; all 100 final-agreement evidence rows have now been inspected. No untouched holdout claim.",
        "mode_scope": {
            "documentation-only": "documentation evidence agreement with mixed-source final agreement; no documentation-only ground-truth claim",
            "code-only": "cross-scope code evidence agreement with mixed-source final agreement; no code-ground-truth accuracy claim",
            "combined": "union of documentation/code evidence, not an average; mixed-source reference agreement",
        },
        "per_mode": {},
        "common_complete_cohort": {},
        "provenance": provenance,
    }
    for mode in MODES:
        report["per_mode"][mode] = {
            name: mode_metrics(
                [
                    row
                    for repo, row in sorted(collected[mode].items())
                    if name == "all" or partition[repo] == name
                ],
                len(gold) if name == "all" else sum(p == name for p in partition.values()),
            )
            for name in ("all", "development", "operational_holdout")
        }
        report["common_complete_cohort"][mode] = mode_metrics(
            [collected[mode][repo] for repo in sorted(common)], len(gold)
        )
    report["accuracy_target_status"] = (
        "No >=90% claim is made. Report label accuracy, exact six-stage match, precision/recall/F1 and coverage separately. Rule changes require development evidence and independent validation."
    )
    output.mkdir(parents=True)
    write_json(output / "all_modes_metrics.json", report)
    fields = [
        "repository",
        "commit",
        "partition",
        "mode",
        "stage",
        "human_documentation",
        "prediction",
        "scan_complete",
    ]
    write_csv(output / "all_modes_comparison.csv", fields, predictions)
    for part in ("development", "operational_holdout"):
        write_csv(
            output / f"documentation_errors_{part}.csv",
            fields + ["outcome", "accepted_evidence", "excluded_evidence"],
            [r for r in errors if r["partition"] == part],
        )
    write_json(output / "documentation_diagnostics.json", diagnostics)
    repository_rows = []
    by_repo_mode: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in predictions:
        by_repo_mode.setdefault((row["repository"], row["mode"]), []).append(row)
    for (repo, mode), stage_rows in sorted(by_repo_mode.items()):
        repository_rows.append(
            {
                "repository": repo,
                "mode": mode,
                "partition": partition[repo],
                "checkpoint_present": repo in seen,
                "scan_complete": all(row["scan_complete"] for row in stage_rows),
                "positive_stages": json.dumps(
                    [row["stage"] for row in stage_rows if row["prediction"] == 1]
                ),
                "negative_stages": json.dumps(
                    [row["stage"] for row in stage_rows if row["prediction"] == 0]
                ),
                "unknown_stages": json.dumps(
                    [row["stage"] for row in stage_rows if row["prediction"] == ""]
                ),
            }
        )
    write_csv(output / "repository_summary.csv", list(repository_rows[0]), repository_rows)
    summary: list[dict[str, Any]] = []
    per_stage: list[dict[str, Any]] = []
    for mode in MODES:
        metrics = report["per_mode"][mode]["all"]
        summary.append(
            {
                "mode": mode,
                "evaluated_repositories": metrics["repository_count"],
                "coverage": metrics["coverage"],
                "label_accuracy": metrics["label_accuracy"],
                "exact_match_accuracy": metrics["exact_match_accuracy"],
                "macro_f1": metrics["macro"]["f1"],
                "micro_precision": metrics["micro"]["precision"],
                "micro_recall": metrics["micro"]["recall"],
                "micro_f1": metrics["micro"]["f1"],
                "interpretation": report["mode_scope"][mode],
            }
        )
        per_stage.extend({"mode": mode, **row} for row in metrics["per_stage"])
    write_csv(output / "mode_summary.csv", list(summary[0]), summary)
    write_csv(output / "per_stage_metrics.csv", list(per_stage[0]), per_stage)
    write_json(output / "review_partition.json", partition)
    if review_documents:
        (output / "documentation_review_development.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in review_rows),
            encoding="utf-8",
        )
    return {"modes": summary, "common_complete_repositories": len(common), "output": str(output)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--replay",
        action="store_true",
        help="Recompute all three modes from saved snapshots; no GitHub requests",
    )
    parser.add_argument("--rules-dir", type=Path)
    parser.add_argument(
        "--review-documents",
        action="store_true",
        help="Export captured documentation for development mismatches only",
    )
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                assess(
                    args.run,
                    args.reference,
                    args.output,
                    args.replay,
                    args.rules_dir,
                    args.review_documents,
                ),
                indent=2,
            )
        )
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
