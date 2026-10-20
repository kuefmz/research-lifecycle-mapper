"""Validated benchmark evaluation and deterministic reports for all three modes."""

import csv
import json
import platform
import re
import subprocess
from pathlib import Path
from typing import Any

from . import MODES, STAGES, __version__
from .analysis import analyze, load_rules
from .canonical import contained, json_bytes, ratio, read_json, sha256, write_csv, write_json
from .protocol import frozen_guard, partition

CANONICAL_OUTPUTS = (
    "manifest.json",
    "predictions.csv",
    "evidence.jsonl",
    "metrics.json",
    "metrics.csv",
    "confusion_matrices.csv",
    "errors.csv",
    "coverage.csv",
    "report.md",
    "confusion_matrices.svg",
    "excluded_evidence.jsonl",
    "documentation_errors.csv",
    "mode_comparison.csv",
    "selection.json",
)


def git_state(root: Path) -> dict[str, Any]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, stderr=subprocess.DEVNULL, text=True
        ).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True))
        return {"commit": commit, "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": True}


def implementation_hash(root: Path) -> str:
    records = []
    for directory in ["src", "rules"]:
        for path in sorted((root / directory).rglob("*")):
            if path.is_file() and path.suffix in {".py", ".yaml"}:
                records.append(
                    {"path": path.relative_to(root).as_posix(), "sha256": sha256(path.read_bytes())}
                )
    return sha256(json_bytes(records))


def validate_manifest(path: Path, role: str, development_repositories: list[str]) -> dict[str, Any]:
    manifest = read_json(path)
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported benchmark manifest schema")
    if manifest.get("status") != "approved":
        raise ValueError("Benchmark is pending: approved human consensus and snapshots required")
    if manifest.get("kind") not in {"research", "synthetic"}:
        raise ValueError("Benchmark kind must be research or synthetic")
    if manifest.get("stages") != list(STAGES):
        raise ValueError("Benchmark stage order/codebook differs from classifier")
    if not manifest.get("version") or not manifest.get("codebook_version"):
        raise ValueError("Benchmark and codebook versions are required")
    repos = manifest.get("repositories", [])
    ids = [item["repository"] for item in repos]
    if not repos or len({repo.lower() for repo in ids}) != len(ids):
        raise ValueError("Empty benchmark or duplicate repositories")
    if role not in {"exploratory", "held-out", "synthetic"}:
        raise ValueError("Unknown evaluation role")
    if manifest["kind"] == "synthetic" and role != "synthetic":
        raise ValueError("Synthetic metrics cannot be presented as research results")
    if manifest["kind"] == "research" and role == "synthetic":
        raise ValueError("Research benchmark cannot use synthetic role")
    if role == "held-out":
        if not manifest.get("held_out_approval_reference"):
            raise ValueError("Held-out evaluation requires documented split approval")
        if (
            manifest.get(
                "test_used_for_rule_development", manifest.get("used_for_rule_development")
            )
            is not False
        ):
            raise ValueError("Benchmark leakage: held-out repositories used for rule development")
        if manifest.get("test_labels_inspected_during_tuning") is not False:
            raise ValueError("Held-out label isolation must be explicitly attested")
    for item in repos:
        if not re.fullmatch(r"[0-9a-f]{40}", item.get("commit", "")):
            raise ValueError("Pinned repository revision missing")
        if not re.fullmatch(r"[0-9a-f]{64}", item.get("snapshot_sha256", "")):
            raise ValueError("Snapshot checksum missing")
        if set(item["labels"]) != set(STAGES) or any(
            type(value) is not int or value not in (0, 1) for value in item["labels"].values()
        ):
            raise ValueError("Gold labels require exactly six literal binary values")
        contained(path.parent, item["snapshot"])
    if manifest["kind"] == "research":
        if len(repos) != 100:
            raise ValueError("The research benchmark must contain exactly 100 repositories")
        provenance_path = contained(path.parent, manifest["annotation_provenance"])
        provenance = read_json(provenance_path)
        if sha256(provenance_path.read_bytes()) != manifest["annotation_provenance_sha256"]:
            raise ValueError("Annotation provenance integrity failure")
        if (
            provenance.get("gold_status") != "approved"
            or provenance.get("repository_count") != 100
            or provenance.get("pair_count") != 600
            or type(provenance.get("initial_disagreements")) is not int
            or not 0 <= provenance["initial_disagreements"] <= 600
        ):
            raise ValueError(
                "Human annotation provenance is not approved or does not match declared benchmark"
            )
        for key in ["sampling_documentation", "codebook"]:
            document = contained(path.parent, manifest[key])
            if sha256(document.read_bytes()) != manifest[key + "_sha256"]:
                raise ValueError(f"{key} integrity failure")
        if not manifest.get("sampling_verified") or not manifest.get("codebook_approval_reference"):
            raise ValueError("Sampling documentation and human codebook approval required")
        annotations_path = contained(path.parent, manifest["annotations"])
        if sha256(annotations_path.read_bytes()) != provenance["annotations_sha256"]:
            raise ValueError("Annotation table integrity failure")
        with annotations_path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        gold = {
            (item["repository"].lower(), stage): label
            for item in repos
            for stage, label in item["labels"].items()
        }
        seen = set()
        disagreements = 0
        for row in rows:
            pair = (row["repository"].lower(), row["stage"])
            if (
                pair in seen
                or pair not in gold
                or not row["approval_reference"]
                or row["approved_consensus"] != str(gold[pair])
            ):
                raise ValueError("Manifest labels differ from approved annotation table")
            if row["reviewer2"] not in {"0", "1"} or row["reviewer1"] not in {"0", "1"}:
                raise ValueError("Invalid independent annotation")
            disagreements += row["reviewer2"] != row["reviewer1"]
            seen.add(pair)
        if seen != set(gold) or disagreements != provenance["initial_disagreements"]:
            raise ValueError("Incomplete gold table or disagreement provenance mismatch")
        consensus_path = contained(path.parent, manifest["consensus_provenance"])
        consensus = read_json(consensus_path)
        if (
            sha256(consensus_path.read_bytes()) != manifest["consensus_provenance_sha256"]
            or consensus.get("gold_status") != "approved"
            or consensus.get("source_worksheet") not in {"Agreement Final", "final_agreement"}
            or consensus.get("synthetic")
            or not consensus.get("approval_reference")
        ):
            raise ValueError(
                "Gold must come from approved, non-synthetic Agreement Final consensus"
            )
        table_path = contained(path.parent, manifest["consensus_table"])
        if sha256(table_path.read_bytes()) != consensus["consensus_table_sha256"]:
            raise ValueError("Agreement Final table integrity failure")
        with table_path.open(newline="", encoding="utf-8") as stream:
            final_rows = list(csv.DictReader(stream))
        final_seen = set()
        for row in final_rows:
            pair = (row["repository"].lower(), row["stage"])
            if (
                pair in final_seen
                or pair not in gold
                or row["label"] != str(gold[pair])
                or row["consensus_status"] != "approved"
                or not row["approval_reference"]
            ):
                raise ValueError("Gold differs from approved Agreement Final worksheet")
            final_seen.add(pair)
        if final_seen != set(gold):
            raise ValueError("Agreement Final labels are incomplete")
    return manifest


def calculate_metrics(gold: list[dict[str, int]], predictions: list[list[str]]) -> dict[str, Any]:
    if len(gold) != len(predictions):
        raise ValueError("Gold/prediction row mismatch")
    stage_metrics: list[dict[str, Any]] = []
    for stage in STAGES:
        tp = sum(
            labels[stage] == 1 and stage in predicted
            for labels, predicted in zip(gold, predictions, strict=True)
        )
        fp = sum(
            labels[stage] == 0 and stage in predicted
            for labels, predicted in zip(gold, predictions, strict=True)
        )
        tn = sum(
            labels[stage] == 0 and stage not in predicted
            for labels, predicted in zip(gold, predictions, strict=True)
        )
        fn = sum(
            labels[stage] == 1 and stage not in predicted
            for labels, predicted in zip(gold, predictions, strict=True)
        )
        stage_metrics.append(
            {
                "stage": stage,
                "TP": tp,
                "FP": fp,
                "TN": tn,
                "FN": fn,
                "precision": ratio(tp, tp + fp),
                "recall": ratio(tp, tp + fn),
                "f1": ratio(2 * tp, 2 * tp + fp + fn),
                "support": tp + fn,
                "accuracy": ratio(tp + tn, len(gold)),
            }
        )
    tp = sum(row["TP"] for row in stage_metrics)
    fp = sum(row["FP"] for row in stage_metrics)
    fn = sum(row["FN"] for row in stage_metrics)
    exact = sum(
        all(bool(labels[stage]) == (stage in predicted) for stage in STAGES)
        for labels, predicted in zip(gold, predictions, strict=True)
    )
    return {
        "repository_count": len(gold),
        "per_stage": stage_metrics,
        "micro": {
            "precision": ratio(tp, tp + fp),
            "recall": ratio(tp, tp + fn),
            "f1": ratio(2 * tp, 2 * tp + fp + fn),
        },
        "macro": {
            key: round(sum(row[key] for row in stage_metrics) / 6, 8)
            for key in ["precision", "recall", "f1"]
        },
        "exact_match_accuracy": ratio(exact, len(gold)),
        "hamming_loss": ratio(fp + fn, len(gold) * 6),
        "undefined_metric_convention": "zero; empty evaluation flagged by repository_count=0",
        "rounding": "round to 8 decimal places; JSON numbers and CSV decimal representations",
    }


def matrices_svg(metrics: dict[str, Any]) -> str:
    """Exact static research figure, independent of plotting-library/font versions."""
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1140" height="500" viewBox="0 0 1140 500">',
        '<rect width="1140" height="500" fill="white"/>',
        '<text x="20" y="25" font-family="sans-serif" font-size="16">Confusion matrices: rows=gold (0,1), columns=prediction (0,1)</text>',
    ]
    for mode_index, mode in enumerate(MODES):
        y = 50 + mode_index * 145
        parts.append(
            f'<text x="10" y="{y + 15}" font-family="sans-serif" font-size="12">{mode}</text>'
        )
        for stage_index, row in enumerate(metrics[mode]["per_stage"]):
            x = 145 + stage_index * 165
            parts.append(
                f'<text x="{x}" y="{y + 15}" font-family="sans-serif" font-size="12">{row["stage"]}</text>'
            )
            for index, key in enumerate(["TN", "FP", "FN", "TP"]):
                cell_x = x + (index % 2) * 64
                cell_y = y + 25 + (index // 2) * 40
                fill = "#d9e8ef" if key in {"TN", "TP"} else "#f7dfd1"
                parts.append(
                    f'<rect x="{cell_x}" y="{cell_y}" width="64" height="40" fill="{fill}" stroke="white"/>'
                )
                parts.append(
                    f'<text x="{cell_x + 8}" y="{cell_y + 25}" font-family="sans-serif" font-size="12">{key} {row[key]}</text>'
                )
    return "\n".join(parts + ["</svg>"]) + "\n"


def run(config_path: Path, output_override: Path | None = None, reproduction: bool = False) -> Path:
    # Configs are JSON-compatible YAML; rejecting arbitrary YAML avoids loader ambiguity.
    config = read_json(config_path)
    root = config_path.resolve().parent.parent
    manifest_path = contained(root, config["benchmark_manifest"])
    benchmark = validate_manifest(manifest_path, config["evaluation_role"], [])
    benchmark_hash = sha256(manifest_path.read_bytes())
    selected_repositories = partition(config, root, benchmark, benchmark_hash)
    benchmark = {**benchmark, "repositories": selected_repositories}
    rules_dir = contained(root, config["rules_dir"]) if config.get("rules_dir") else None
    _, catalog_hash = load_rules(rules_dir)
    state = git_state(root)
    lock_path = root / "uv.lock"
    ledger = frozen_guard(
        config,
        root,
        benchmark_hash,
        catalog_hash,
        state,
        implementation_hash(root),
        sha256(lock_path.read_bytes()) if lock_path.exists() else "",
        reproduction,
    )
    if (
        benchmark["kind"] == "research"
        and (root / ".python-version").read_text().strip() != platform.python_version()
    ):
        raise ValueError("Research evaluation requires the exact pinned Python runtime")
    if benchmark["kind"] == "research" and (
        state["dirty"] or not state["commit"] or not lock_path.exists()
    ):
        raise ValueError(
            "Research evaluation requires a clean committed classifier and dependency lockfile"
        )
    output = output_override or contained(root, config["output"])
    if output.exists():
        raise ValueError("Run output must be a new directory; never overwrite runs")
    output.mkdir(parents=True)
    predictions = []
    evidence: list[dict[str, Any]] = []
    excluded_evidence: list[dict[str, Any]] = []
    errors = []
    documentation_errors = []
    coverage = []
    metrics = {}
    snapshots = []
    for item in sorted(benchmark["repositories"], key=lambda item: item["repository"]):
        snapshot = contained(manifest_path.parent, item["snapshot"])
        snapshots.append(
            {
                "repository": item["repository"],
                "commit": item["commit"],
                "manifest_sha256": item["snapshot_sha256"],
            }
        )
        # Integrity failures abort the run; they are never converted to all-negative predictions.
        for mode in MODES:
            result = analyze(snapshot, mode, rules_dir, item["snapshot_sha256"])
            if result["repository"] != item["repository"] or result["commit"] != item["commit"]:
                raise ValueError("Benchmark and snapshot identity mismatch")
            if bool(read_json(snapshot / "manifest.json").get("synthetic")) != (
                benchmark["kind"] == "synthetic"
            ):
                raise ValueError("Synthetic/research snapshot provenance mismatch")
            coverage.append(
                {
                    key: result[key]
                    for key in [
                        "repository",
                        "mode",
                        "scan_complete",
                        "inventory_complete",
                        "eligible_files",
                        "captured_files",
                        "unavailable_files",
                    ]
                }
            )
            evidence.extend({"mode": mode, **record} for record in result["evidence"])
            excluded_evidence.extend(
                {"mode": mode, **record} for record in result["excluded_evidence"]
            )
            for stage in STAGES:
                predicted = int(stage in result["labels"])
                gold = item["labels"][stage]
                row = {
                    "repository": item["repository"],
                    "commit": item["commit"],
                    "mode": mode,
                    "stage": stage,
                    "gold": gold,
                    "prediction": predicted,
                    "evaluated": result["scan_complete"],
                }
                predictions.append(row)
                if result["scan_complete"] and predicted != gold:
                    matches = [record for record in result["evidence"] if record["stage"] == stage]
                    errors.append(
                        {
                            "repository": item["repository"],
                            "mode": mode,
                            "stage": stage,
                            "type": "FP" if predicted else "FN",
                            "path": ";".join(record["path"] for record in matches),
                            "rule_ids": ";".join(record["rule_id"] for record in matches),
                            "evidence_urls": ";".join(record["url"] for record in matches),
                            "reason": "label-mismatch",
                        }
                    )
                    if mode == "documentation-only":
                        vetoed = [
                            record
                            for record in result["excluded_evidence"]
                            if record["stage"] == stage
                        ]
                        documentation_errors.append(
                            {
                                "repository": item["repository"],
                                "stage": stage,
                                "human_label": gold,
                                "documentation_prediction": predicted,
                                "rule_ids": ";".join(record["rule_id"] for record in matches),
                                "document_paths": ";".join(record["path"] for record in matches),
                                "line_ranges": ";".join(
                                    f"{record['start_line']}-{record['end_line']}"
                                    for record in matches
                                ),
                                "documentation_evidence": json.dumps(
                                    matches, sort_keys=True, ensure_ascii=False
                                ),
                                "excluded_candidates": json.dumps(
                                    vetoed, sort_keys=True, ensure_ascii=False
                                ),
                                "error_category": "qualifying-evidence-disagrees"
                                if predicted
                                else "no-qualifying-evidence",
                                "investigation_hypothesis": "missing-eligible-documentation"
                                if result["captured_files"] == 0
                                else "heuristic-insufficiency-or-codebook-ambiguity",
                                "review_status": "unreviewed; human label not presumed wrong",
                            }
                        )
            for failure in result["analysis_errors"]:
                errors.append(
                    {
                        "repository": item["repository"],
                        "mode": mode,
                        "stage": "",
                        "type": "analysis-failure",
                        "path": failure["path"],
                        "rule_ids": "",
                        "evidence_urls": "",
                        "reason": failure["reason"],
                    }
                )
            for file in read_json(snapshot / "manifest.json")["files"]:
                allowed = (
                    {"documentation"}
                    if mode == MODES[0]
                    else {"code"}
                    if mode == MODES[1]
                    else {"documentation", "code"}
                )
                if file["source"] in allowed and file["status"] == "unavailable":
                    errors.append(
                        {
                            "repository": item["repository"],
                            "mode": mode,
                            "stage": "",
                            "type": "acquisition-failure",
                            "path": file["path"],
                            "rule_ids": "",
                            "evidence_urls": "",
                            "reason": file["reason"],
                        }
                    )
    by_repo = {item["repository"]: item for item in benchmark["repositories"]}
    for mode in MODES:
        eligible_ids = [
            row["repository"] for row in coverage if row["mode"] == mode and row["scan_complete"]
        ]
        predicted_sets = [
            [
                row["stage"]
                for row in predictions
                if row["mode"] == mode and row["repository"] == repo and row["prediction"]
            ]
            for repo in eligible_ids
        ]
        calculated = calculate_metrics(
            [by_repo[repo]["labels"] for repo in eligible_ids], predicted_sets
        )
        calculated.update(
            coverage=ratio(len(eligible_ids), len(by_repo)),
            analysis_failure_rate=ratio(len(by_repo) - len(eligible_ids), len(by_repo)),
            failure_policy="exclude incomplete repositories per mode; keep predictions and coverage",
        )
        metrics[mode] = calculated
    write_csv(
        output / "predictions.csv",
        ["repository", "commit", "mode", "stage", "gold", "prediction", "evaluated"],
        predictions,
    )
    for filename, records in [
        ("evidence.jsonl", evidence),
        ("excluded_evidence.jsonl", excluded_evidence),
    ]:
        (output / filename).write_text(
            "".join(
                json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
                for record in records
            ),
            encoding="utf-8",
        )
    write_json(output / "metrics.json", metrics)
    write_csv(
        output / "documentation_errors.csv",
        [
            "repository",
            "stage",
            "human_label",
            "documentation_prediction",
            "rule_ids",
            "document_paths",
            "line_ranges",
            "documentation_evidence",
            "excluded_candidates",
            "error_category",
            "investigation_hypothesis",
            "review_status",
        ],
        documentation_errors,
    )
    primary = metrics["documentation-only"]
    comparison = [
        {
            "mode": mode,
            "role": "primary" if mode == "documentation-only" else "secondary",
            "evaluated_repositories": metrics[mode]["repository_count"],
            "macro_precision": metrics[mode]["macro"]["precision"],
            "macro_recall": metrics[mode]["macro"]["recall"],
            "macro_f1": metrics[mode]["macro"]["f1"],
            "precision_delta_from_documentation": round(
                metrics[mode]["macro"]["precision"] - primary["macro"]["precision"], 8
            ),
            "recall_delta_from_documentation": round(
                metrics[mode]["macro"]["recall"] - primary["macro"]["recall"], 8
            ),
            "same_evaluated_cohort": {
                row["repository"]
                for row in coverage
                if row["mode"] == mode and row["scan_complete"]
            }
            == {
                row["repository"]
                for row in coverage
                if row["mode"] == "documentation-only" and row["scan_complete"]
            },
        }
        for mode in MODES
    ]
    write_csv(output / "mode_comparison.csv", list(comparison[0]), comparison)
    write_json(
        output / "selection.json",
        {
            "primary_mode": "documentation-only",
            "metric": "macro.f1",
            "value": primary["macro"]["f1"],
            "evaluation_role": config["evaluation_role"],
            "partition": config.get("partition", "full"),
            "eligible_for_model_selection": config["evaluation_role"] == "exploratory"
            and config.get("partition") == "development",
            "secondary_combination": "logical OR; compare recall and precision with cohort caveat",
        },
    )
    metric_rows = []
    matrices = []
    for mode in MODES:
        for row in metrics[mode]["per_stage"]:
            metric_rows.append(
                {
                    "mode": mode,
                    "scope": row["stage"],
                    "precision": row["precision"],
                    "recall": row["recall"],
                    "f1": row["f1"],
                    "support": row["support"],
                }
            )
            matrices.append(
                {"mode": mode, **{key: row[key] for key in ["stage", "TP", "FP", "TN", "FN"]}}
            )
        for scope in ["micro", "macro"]:
            metric_rows.append(
                {
                    "mode": mode,
                    "scope": scope,
                    **metrics[mode][scope],
                    "support": sum(row["support"] for row in metrics[mode]["per_stage"]),
                }
            )
    write_csv(
        output / "metrics.csv",
        ["mode", "scope", "precision", "recall", "f1", "support"],
        metric_rows,
    )
    write_csv(
        output / "confusion_matrices.csv", ["mode", "stage", "TP", "FP", "TN", "FN"], matrices
    )
    write_csv(
        output / "errors.csv",
        ["repository", "mode", "stage", "type", "path", "rule_ids", "evidence_urls", "reason"],
        errors,
    )
    write_csv(
        output / "coverage.csv",
        [
            "repository",
            "mode",
            "scan_complete",
            "inventory_complete",
            "eligible_files",
            "captured_files",
            "unavailable_files",
        ],
        coverage,
    )
    (output / "confusion_matrices.svg").write_text(matrices_svg(metrics), encoding="utf-8")
    report = [
        "# Research Lifecycle Mapper evaluation",
        "",
        f"Benchmark: {benchmark['version']} ({benchmark['kind']}); role: {config['evaluation_role']}.",
        "Primary method: documentation-only; development model-selection metric: documentation macro-F1. Code-only and OR-combined are secondary comparisons.",
        "",
        "Candidate rules are unadjudicated. Synthetic metrics test the software and are not research performance estimates.",
        "",
        "Incomplete scans are excluded from metrics per mode. Undefined ratios are zero. Numbers are rounded to eight decimal places.",
        "",
        "| Mode | Evaluated | Micro F1 | Macro F1 | Exact match | Hamming loss | Coverage | Failure rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode in MODES:
        values = metrics[mode]
        report.append(
            f"| {mode} | {values['repository_count']} | {values['micro']['f1']:.8f} | {values['macro']['f1']:.8f} | {values['exact_match_accuracy']:.8f} | {values['hamming_loss']:.8f} | {values['coverage']:.8f} | {values['analysis_failure_rate']:.8f} |"
        )
    report.extend(
        [
            "",
            "See errors.csv for FP/FN and failures, evidence.jsonl for matched evidence, and excluded_evidence.jsonl for vetoed candidates.",
            "",
            "![Confusion matrices](confusion_matrices.svg)",
            "",
        ]
    )
    (output / "report.md").write_text("\n".join(report), encoding="utf-8")
    environment = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "system": platform.system(),
        "machine": platform.machine(),
        "classifier_version": __version__,
    }
    write_json(output / "environment.json", environment)
    execution = {
        "schema_version": 1,
        "classifier_git_commit": state["commit"],
        "source_dirty": state["dirty"],
        "classifier_source_sha256": implementation_hash(root),
        "rule_catalog_hash": catalog_hash,
        "benchmark_version": benchmark["version"],
        "benchmark_manifest_sha256": sha256(manifest_path.read_bytes()),
        "input_snapshots": snapshots,
        "runtime_version": platform.python_version(),
        "lockfile_sha256": sha256(lock_path.read_bytes()) if lock_path.exists() else None,
        "configuration": {key: value for key, value in config.items() if key != "output"},
        "undefined_metric_convention": "zero",
        "float_rounding_decimal_places": 8,
        "canonical_outputs": list(CANONICAL_OUTPUTS),
        "environment": {
            key: environment[key] for key in ["python", "implementation", "classifier_version"]
        },
    }
    write_json(output / "manifest.json", execution)
    if ledger is not None:
        hashes = {
            filename: sha256((output / filename).read_bytes()) for filename in CANONICAL_OUTPUTS
        }
        if reproduction:
            if read_json(ledger)["canonical_hashes"] != hashes:
                raise ValueError("Frozen final results differ; do not retune using test errors")
        else:
            write_json(
                ledger,
                {
                    "canonical_hashes": hashes,
                    "classifier_commit": state["commit"],
                    "purpose": "single final evaluation; further executions are reproduction-only",
                },
            )
    return output


def verify(config_path: Path, workspace: Path, reference: Path | None = None) -> dict[str, str]:
    if workspace.exists():
        raise ValueError("Verification workspace must not exist")
    workspace.mkdir(parents=True)
    first = run(config_path, workspace / "first", reproduction=True)
    second = run(config_path, workspace / "second", reproduction=True)
    hashes = {}
    for filename in CANONICAL_OUTPUTS:
        one = (first / filename).read_bytes()
        if one != (second / filename).read_bytes():
            raise ValueError(f"Non-reproducible output: {filename}")
        if (
            reference is not None
            and filename != "manifest.json"
            and one != (reference / filename).read_bytes()
        ):
            raise ValueError(f"Committed reference differs: {filename}")
        hashes[filename] = sha256(one)
    # Reference manifest carries the producing commit, which naturally changes in a later checkout.
    # Semantic result artifacts must still match byte-for-byte; current reruns include manifest.
    write_json(workspace / "verified_hashes.json", hashes)
    return hashes
