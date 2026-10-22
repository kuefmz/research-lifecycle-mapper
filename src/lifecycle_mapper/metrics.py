"""Reference agreement metrics and reproducible implementation provenance."""

import subprocess
from pathlib import Path
from typing import Any
from . import STAGES
from .canonical import json_bytes, ratio, sha256


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
