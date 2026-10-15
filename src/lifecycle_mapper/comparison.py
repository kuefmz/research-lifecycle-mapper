"""Observed reference comparisons on pinned snapshots; no publication approval implied.

Complete-case metrics exclude failed/incomplete scans independently per mode.
Captured-evidence metrics also retain incomplete scans but are explicitly exploratory.
Human labels enter only after classification. Partition membership is external/frozen.
"""

from pathlib import Path
from typing import Any

from . import MODES, STAGES
from .analysis import analyze, load_rules
from .benchmark import calculate_metrics, git_state, implementation_hash
from .canonical import contained, read_json, sha256, write_csv, write_json


def compare(
    reference: Path,
    run: Path,
    split: Path,
    output: Path,
    rules: Path | None = None,
    partitions: tuple[str, ...] = ("development",),
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("Comparison output must be a new directory")
    gold_manifest = read_json(reference / "manifest.json")
    provenance = read_json(reference / "provenance.json")
    if provenance["gold_status"] != "approved":
        raise ValueError("Reference must have explicit user approval")
    if sha256((reference / "benchmark.csv").read_bytes()) != provenance["consensus_table_sha256"]:
        raise ValueError("Reference checksum mismatch")
    # Verify manifest labels against the checksummed long table, never trust a second copy.
    import csv

    with (reference / "benchmark.csv").open(newline="", encoding="utf-8") as stream:
        verified = {
            (r["repository"].casefold(), r["stage"]): int(r["label"])
            for r in csv.DictReader(stream)
        }
    gold = {r["repository"].casefold(): r["labels"] for r in gold_manifest["repositories"]}
    if {
        (repo, s): label for repo, labels in gold.items() for s, label in labels.items()
    } != verified:
        raise ValueError("Reference manifest labels differ from approved table")
    split_data = read_json(split)
    dev = {r.casefold() for r in split_data["development"]}
    test = {r.casefold() for r in split_data["held_out"]}
    if dev & test or dev | test != set(gold):
        raise ValueError("Split must partition exactly the reference repositories")
    if any(p not in {"development", "held_out", "full_exploratory"} for p in partitions):
        raise ValueError("Unknown comparison partition")
    inventory = read_json(run / "manifest.json")["repositories"]
    selected_ids = set().union(
        *(dev if p == "development" else test if p == "held_out" else set(gold) for p in partitions)
    )
    output.mkdir(parents=True)
    results = []
    errors = []
    for row in inventory:
        repo = (
            row["repository"].casefold()
            if row.get("repository")
            else row["url"].removeprefix("https://github.com/").casefold()
        )
        if repo not in selected_ids:
            continue
        if row.get("status") != "analyzed":
            errors.append({"repository": repo, "reason": row.get("reason", "acquisition-failed")})
            results.append(
                {
                    "repository": repo,
                    "source_url": "https://github.com/" + repo,
                    "human_labels": gold[repo],
                    "modes": [],
                    "error": "acquisition-failed",
                }
            )
            continue
        try:
            snapshot = contained(run, row["snapshot"])
            analyzed = [analyze(snapshot, mode, rules, row["snapshot_sha256"]) for mode in MODES]
            results.append(
                {
                    "repository": repo,
                    "source_url": analyzed[0]["repository_url"],
                    "commit": analyzed[0]["commit"],
                    "snapshot": row["snapshot"],
                    "snapshot_sha256": row["snapshot_sha256"],
                    "human_labels": gold[repo],
                    "modes": analyzed,
                }
            )
        except (OSError, ValueError) as exc:
            errors.append({"repository": repo, "reason": type(exc).__name__})
            results.append(
                {
                    "repository": repo,
                    "source_url": "https://github.com/" + repo,
                    "human_labels": gold[repo],
                    "modes": [],
                    "error": type(exc).__name__,
                }
            )
    observed = {r["repository"] for r in results}
    for repo in sorted(selected_ids - observed):
        results.append(
            {
                "repository": repo,
                "source_url": "https://github.com/" + repo,
                "human_labels": gold[repo],
                "modes": [],
                "error": "missing-acquisition-record",
            }
        )
    results.sort(key=lambda r: r["repository"])
    metrics: dict[str, Any] = {}
    mismatches = []
    for partition in partitions:
        ids = dev if partition == "development" else test if partition == "held_out" else set(gold)
        metrics[partition] = {}
        for mode in MODES:
            observations = [
                (r, m)
                for r in results
                if r["repository"] in ids
                for m in r["modes"]
                if m["mode"] == mode
            ]
            complete = [(r, m) for r, m in observations if m["scan_complete"]]
            metrics[partition][mode] = {
                "complete_case": calculate_metrics(
                    [r["human_labels"] for r, m in complete], [m["labels"] for r, m in complete]
                ),
                "captured_evidence_exploratory": calculate_metrics(
                    [r["human_labels"] for r, m in observations],
                    [m["labels"] for r, m in observations],
                ),
                "population": len(ids),
                "acquired": len(observations),
                "complete": len(complete),
                "coverage": len(complete) / len(ids),
            }
            for r, m in observations:
                for stage in STAGES:
                    human = r["human_labels"][stage]
                    predicted = int(stage in m["labels"])
                    if human != predicted:
                        evidence = [e for e in m["evidence"] if e["stage"] == stage]
                        mismatches.append(
                            {
                                "partition": partition,
                                "repository": r["repository"],
                                "mode": mode,
                                "stage": stage,
                                "human": human,
                                "prediction": predicted,
                                "scan_complete": m["scan_complete"],
                                "kind": "FP" if predicted else "FN",
                                "rule_ids": ";".join(sorted({e["rule_id"] for e in evidence})),
                            }
                        )
    _, rule_hash = load_rules(rules)
    write_json(output / "metrics.json", metrics)
    write_json(
        output / "results.json",
        {
            "repositories": results,
            "repository_count": len(results),
            "purpose": "reference comparison",
            "imported": True,
        },
    )
    write_json(
        output / "manifest.json",
        {
            "kind": "observed-reference-comparison",
            "partitions": list(partitions),
            "rule_catalog_hash": rule_hash,
            "split": split_data,
            "split_sha256": sha256(split.read_bytes()),
            "reference_provenance": provenance,
            "classifier": git_state(Path.cwd()),
            "classifier_source_sha256": implementation_hash(Path.cwd()),
            "acquisition_manifest_sha256": sha256((run / "manifest.json").read_bytes()),
            "warning": "Held-out is an operational split, not an independently blinded evaluation. Full label table was available in this session. No held-out error inspection used for rule changes.",
        },
    )
    fields = [
        "partition",
        "repository",
        "mode",
        "stage",
        "human",
        "prediction",
        "scan_complete",
        "kind",
        "rule_ids",
    ]
    write_csv(output / "mismatches.csv", fields, mismatches)
    flat = []
    for partition, modes in metrics.items():
        for mode, views in modes.items():
            for view in ["complete_case", "captured_evidence_exploratory"]:
                for stage in views[view]["per_stage"]:
                    flat.append({"partition": partition, "mode": mode, "view": view, **stage})
    write_csv(
        output / "metrics.csv",
        [
            "partition",
            "mode",
            "view",
            "stage",
            "TP",
            "FP",
            "TN",
            "FN",
            "precision",
            "recall",
            "f1",
            "support",
            "accuracy",
        ],
        flat,
    )
    evidence = [
        {"mode": m["mode"], **e} for row in results for m in row["modes"] for e in m["evidence"]
    ]
    import json

    (output / "evidence.jsonl").write_text(
        "".join(json.dumps(e, sort_keys=True, ensure_ascii=False) + "\n" for e in evidence),
        encoding="utf-8",
    )
    excluded = [
        {"mode": m["mode"], **e}
        for row in results
        for m in row["modes"]
        for e in m["excluded_evidence"]
    ]
    (output / "excluded_evidence.jsonl").write_text(
        "".join(json.dumps(e, sort_keys=True, ensure_ascii=False) + "\n" for e in excluded),
        encoding="utf-8",
    )
    predictions = [
        {
            "repository": row["repository"],
            "commit": row["commit"],
            "mode": m["mode"],
            "stage": stage,
            "prediction": int(m["predictions"][stage])
            if m["predictions"][stage] is not None
            else None,
            "scan_complete": m["scan_complete"],
        }
        for row in results
        for m in row["modes"]
        for stage in STAGES
    ]
    write_csv(
        output / "predictions.csv",
        ["repository", "commit", "mode", "stage", "prediction", "scan_complete"],
        predictions,
    )
    write_json(output / "errors.json", errors)
    return metrics
