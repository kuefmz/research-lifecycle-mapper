"""Deterministic whole-repository partitioning and frozen evaluation guards."""

from pathlib import Path
from typing import Any

from . import STAGES
from .canonical import contained, json_bytes, read_json, sha256, write_csv, write_json


def split_records(
    repositories: list[dict[str, Any]], test_fraction: float, seed: str
) -> dict[str, list[str]]:
    if not 0 < test_fraction < 1 or len(repositories) < 2:
        raise ValueError(
            "Split needs at least two repositories and a fraction strictly between zero and one"
        )
    count = min(len(repositories) - 1, max(1, round(len(repositories) * test_fraction)))
    totals = {stage: sum(item["labels"][stage] for item in repositories) for stage in STAGES}
    targets = {stage: totals[stage] * count / len(repositories) for stage in STAGES}
    selected_counts = dict.fromkeys(STAGES, 0)
    remaining = sorted(repositories, key=lambda row: row["repository"])
    selected: list[str] = []
    while len(selected) < count:

        def score(item: dict[str, Any]) -> tuple[float, str]:
            imbalance = sum(
                (selected_counts[stage] + item["labels"][stage] - targets[stage]) ** 2
                / max(totals[stage], 1)
                for stage in STAGES
            )
            return imbalance, sha256((seed + "\0" + item["repository"]).encode())

        item = min(remaining, key=score)
        remaining.remove(item)
        selected.append(item["repository"])
        for stage in STAGES:
            selected_counts[stage] += item["labels"][stage]
    return {"development": sorted(row["repository"] for row in remaining), "test": sorted(selected)}


def create_split(
    manifest_path: Path, output: Path, test_fraction: float = 0.2, seed: str = "rlm-split-v1"
) -> dict[str, Any]:
    from .benchmark import validate_manifest

    source = read_json(manifest_path)
    role = "synthetic" if source.get("kind") == "synthetic" else "exploratory"
    benchmark = validate_manifest(manifest_path, role, [])
    if output.exists():
        raise ValueError("Split output must be new; freeze before heuristic tuning")
    partitions = split_records(benchmark["repositories"], test_fraction, seed)
    split = {
        "schema_version": 1,
        "algorithm": "greedy-multilabel-squared-deficit-v1",
        "benchmark_sha256": sha256(manifest_path.read_bytes()),
        "seed": seed,
        "test_fraction": test_fraction,
        "partitions": partitions,
        "unit": "whole-repository",
        "primary_selection_metric": "documentation-only.macro.f1",
        "limitations": "Approximate marginal stratification; rare-label balance not guaranteed.",
        "test_label_custody": "Test labels stay with the original benchmark custodian; no test labels exported.",
    }
    output.mkdir(parents=True)
    write_json(output / "split.json", split)
    development = [
        row for row in benchmark["repositories"] if row["repository"] in partitions["development"]
    ]
    write_csv(
        output / "development_labels.csv",
        ["repository", "stage", "label"],
        [
            {"repository": row["repository"], "stage": stage, "label": row["labels"][stage]}
            for row in development
            for stage in STAGES
        ],
    )
    return split


def partition(
    config: dict[str, Any], root: Path, benchmark: dict[str, Any], benchmark_hash: str
) -> list[dict[str, Any]]:
    if not config.get("split_manifest"):
        if config["evaluation_role"] == "held-out":
            raise ValueError("Held-out evaluation requires a frozen split manifest")
        return benchmark["repositories"]
    split_path = contained(root, config["split_manifest"])
    split = read_json(split_path)
    if (
        sha256(split_path.read_bytes()) != config["split_manifest_sha256"]
        or split["benchmark_sha256"] != benchmark_hash
    ):
        raise ValueError("Split/input integrity mismatch")
    groups = split["partitions"]
    if (
        split.get("schema_version") != 1
        or split.get("algorithm") != "greedy-multilabel-squared-deficit-v1"
    ):
        raise ValueError("Unsupported frozen split schema/algorithm")
    development, test = set(groups["development"]), set(groups["test"])
    population = {row["repository"] for row in benchmark["repositories"]}
    if (
        development & test
        or development | test != population
        or not development
        or not test
        or len(development) != len(groups["development"])
        or len(test) != len(groups["test"])
    ):
        raise ValueError("Invalid whole-repository split")
    selection = config.get("partition", "development")
    if selection not in {"development", "test"}:
        raise ValueError("Unknown split partition")
    if selection == "test" and config["evaluation_role"] not in {"held-out", "synthetic"}:
        raise ValueError("Development evaluations cannot inspect test predictions or errors")
    if selection == "development" and config["evaluation_role"] == "held-out":
        raise ValueError("Held-out role requires test partition")
    if (
        config["evaluation_role"] == "held-out"
        and set(config.get("development_repositories", [])) != development
    ):
        raise ValueError("Declare the complete development cohort in held-out configuration")
    selected = development if selection == "development" else test
    return [row for row in benchmark["repositories"] if row["repository"] in selected]


def config_hash(config: dict[str, Any]) -> str:
    return sha256(
        json_bytes(
            {
                key: value
                for key, value in config.items()
                if key not in {"output", "frozen_manifest", "frozen_manifest_sha256"}
            }
        )
    )


def freeze(config_path: Path, output: Path, approval_reference: str) -> dict[str, Any]:
    from .analysis import load_rules
    from .benchmark import git_state, implementation_hash, validate_manifest

    config = read_json(config_path)
    root = config_path.resolve().parent.parent
    if config["evaluation_role"] != "held-out" or not approval_reference:
        raise ValueError("Freeze requires held-out configuration and researcher protocol approval")
    benchmark_path = contained(root, config["benchmark_manifest"])
    benchmark = validate_manifest(benchmark_path, "held-out", [])
    partition(config, root, benchmark, sha256(benchmark_path.read_bytes()))
    state = git_state(root)
    if state["dirty"] or not state["commit"]:
        raise ValueError("Freeze requires a clean committed classifier")
    rules = contained(root, config["rules_dir"]) if config.get("rules_dir") else None
    _, rules_hash = load_rules(rules)
    if output.exists():
        raise ValueError("Frozen protocol already exists")
    frozen = {
        "schema_version": 1,
        "approval_reference": approval_reference,
        "primary_selection_metric": "documentation-only.macro.f1",
        "classifier_commit": state["commit"],
        "classifier_source_sha256": implementation_hash(root),
        "catalog_sha256": rules_hash,
        "config_sha256": config_hash(config),
        "benchmark_sha256": sha256(benchmark_path.read_bytes()),
        "lockfile_sha256": sha256((root / "uv.lock").read_bytes()),
        "protocol": "test set untouched during tuning; first final run then reproduction-only",
    }
    write_json(output, frozen)
    return frozen


def frozen_guard(
    config: dict[str, Any],
    root: Path,
    benchmark_hash: str,
    catalog_hash: str,
    state: dict[str, Any],
    source_hash: str,
    lock_hash: str,
    reproduction: bool,
) -> Path | None:
    if config["evaluation_role"] != "held-out":
        return None
    path = contained(root, config["frozen_manifest"])
    frozen = read_json(path)
    if sha256(path.read_bytes()) != config["frozen_manifest_sha256"]:
        raise ValueError("Frozen protocol checksum mismatch")
    expected = {
        "classifier_commit": state["commit"],
        "classifier_source_sha256": source_hash,
        "catalog_sha256": catalog_hash,
        "config_sha256": config_hash(config),
        "benchmark_sha256": benchmark_hash,
        "lockfile_sha256": lock_hash,
    }
    if state["dirty"] or any(frozen.get(key) != value for key, value in expected.items()):
        raise ValueError("Frozen classifier/configuration/inputs changed")
    if not frozen.get("approval_reference"):
        raise ValueError("Frozen protocol is not researcher-approved")
    ledger = path.with_suffix(".evaluation.json")
    if ledger.exists() and not reproduction:
        raise ValueError(
            "Final evaluation already executed; use benchmark verify for reproduction only"
        )
    if reproduction and not ledger.exists():
        raise ValueError("Execute the approved final evaluation once before reproduction")
    return ledger
