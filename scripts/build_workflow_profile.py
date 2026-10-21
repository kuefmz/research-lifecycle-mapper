"""Build v5.2 from v5.1; preserve old profiles for comparison."""

import csv
import json
from pathlib import Path

src = Path("configs/multilanguage-development-v5.1")
dst = Path("configs/workflow-development-v5.2")
dst.mkdir(exist_ok=True)
added = [
    (
        "Processing",
        "SHELL_PREP",
        [
            r"(?m)^\s*(?:[\w./-]*/)?(?:prepare[-_][\w.-]*|preprocess[\w.-]*|tokenize[\w.-]*|cv-prepdata\.sh)\s+",
            r"(?:\$[\w{]|\s-\w|\b(?:data|corpus|input|train)\b)",
        ],
    ),
    (
        "Evaluation",
        "SHELL_EVALUATE",
        [
            r"(?m)^\s*(?:(?:python[23]?|perl|Rscript)\s+)?(?:[\w./-]*/)?(?:evaluate|eval|score)(?:[_.-][\w.-]+|\.py|\.pl)?\s+",
            r"(?:\$|>|\b(?:gold|reference|predict\w*|test)\b)",
        ],
    ),
    ("Method", "NUMERIC_UPDATE", [r"\b\w+\s*=\s*\w+\s*-\s*\w+\s*\*\s*\w*(?:grad|gradient)\w*\b"]),
    (
        "Method",
        "OPTIMIZER_CALL",
        [
            r"\b(?:grad_descent|gradient_descent|fminunc|fmincon|fminsearch|least_squares|curve_fit)\s*\(",
            r"\b(?:W|X|Y|data|features|params|parameters|weights|theta)\b",
        ],
    ),
    (
        "Experimentation",
        "REPEATED_SCIENTIFIC_CALL",
        [
            r"\b(?:grad_descent|gradient_descent|run_experiment|run_trial|cross_val_score|cross_validate)\s*\("
        ],
    ),
    (
        "Evaluation",
        "HELDOUT_ERROR",
        [r"\b\w+\s*=\s*[^;\n]*\b\w*(?:test|heldout|gold|reference)\w*\b[^;\n]*-\s*\w+"],
    ),
    (
        "Evaluation",
        "METRIC_NAMES",
        [
            r"\b(?:accuracy_score|precision_score|recall_score|f1_score|mean_squared_error|roc_auc_score|classification_report)\s*\(",
            r"\b\w*(?:true|gold|test|reference|labels|target)\w*\b",
        ],
    ),
]
rows = []
for path in sorted(src.glob("*.yaml")):
    d = json.loads(path.read_text())
    d["version"] = "0.5.2-development"
    if d["stage"] == "Method":
        d["rules"] = [
            r
            for r in d["rules"]
            if r["id"] not in {"MET_DOC_WORKFLOW_V5_1", "MET_DOC_WORKFLOW_V5_2"}
        ]
        d["rules"].append(
            dict(
                id="MET_DOC_IMPLEMENTED_METHOD_V52",
                stage="Method",
                source="documentation",
                version="0.5.2-development",
                description="Explicit implementation or derivation of a named research method, not merely code accompanying a paper or training an existing model.",
                positive=[
                    r"\b(?:implement(?:s|ed|ation|ing)?|introduc(?:e|es|ed|ing)|propos(?:e|es|ed|ing)|deriv(?:e|es|ed|ation))\b",
                    r"\b(?:algorithm|method|estimator|architecture|optimization procedure|inference procedure)\b",
                ],
                supporting=[],
                exclusions=[r"\b(?:not implemented|future work|planned|todo|related work)\b"],
                window_lines=6,
                status="unadjudicated-development-candidate",
                required_evidence_fields=[
                    "repository",
                    "commit",
                    "path",
                    "start_line",
                    "end_line",
                    "matched_conditions",
                    "url",
                ],
            )
        )
    if d["stage"] == "Method":
        template = next(r for r in d["rules"] if r["id"] == "MET_DOC_IMPLEMENTED_METHOD_V52")
        r = dict(template)
        r.update(
            id="MET_DOC_COMPUTATIONAL_STEPS_V52",
            description="Documented implementation with an explicit multistep computational mechanism, beyond merely training or citing a model.",
            positive=[
                r"\b(?:code|implementation|algorithm|method|pipeline|reranker|classifier)\b",
                r"\b(?:consists? of|comprises?|composed of)\b[^.!?]{0,100}\b(?:steps|stages|components)\b",
                r"\b(?:feature extraction|supervised learning|inference|optimization|sampling|ranking)\b",
            ],
            window_lines=8,
        )
        d["rules"].append(r)
    for stage, name, patterns in added:
        if stage != d["stage"]:
            continue
        r = dict(
            id=stage[:3].upper() + "_CODE_" + name + "_V52",
            stage=stage,
            source="code",
            version="0.5.2-development",
            description=name.lower().replace("_", " "),
            positive=patterns,
            supporting=[],
            exclusions=[],
            window_lines=8,
            scope="portable-statement",
            detector="portable-lexical-v1",
            status="unadjudicated-development-candidate",
            required_evidence_fields=[
                "repository",
                "commit",
                "path",
                "start_line",
                "end_line",
                "matched_conditions",
                "url",
            ],
        )
        if name == "REPEATED_SCIENTIFIC_CALL":
            r["file_context_patterns"] = [
                r"\bfor\b[^\n]*(?:reps|trials|seeds|folds|length\s*\(|range\s*\()"
            ]
            r["description"] = (
                "Scientific runner call in a file with an executable repeat/parameter loop; file-level context, not proven data flow."
            )
        d["rules"].append(r)
    dst.joinpath(path.name).write_text(json.dumps(d, indent=2) + "\n")
    for rule in d["rules"]:
        if rule["id"].endswith("_V52"):
            if rule["source"] == "documentation":
                rule["context_pattern"] = (
                    r"\b(?:we|our|this|code|implementation|algorithm|method|pipeline|reranker)\b"
                )
                template = next(
                    r
                    for r in d["rules"]
                    if r.get("layer") == "explicit" and not r["id"].endswith("_V52")
                )
                for key in [
                    "layer",
                    "context_pattern",
                    "command_pattern",
                    "heading_exclusions",
                    "scope_exclusions",
                ]:
                    if key in template:
                        rule.setdefault(key, template[key])
            if len(rule["positive"]) == 1:
                rule["positive"].append(r"(?:=|\()")
        rule.setdefault(
            "justification",
            rule["description"]
            + " Development evidence candidate; no repository identity or reference labels used.",
        )
    dst.joinpath(path.name).write_text(json.dumps(d, indent=2) + "\n")
    rows.extend({"file": path.name, "rule": json.dumps(r, sort_keys=True)} for r in d["rules"])
with dst.joinpath("rule_catalog.csv").open("w") as f:
    w = csv.DictWriter(f, fieldnames=["file", "rule"])
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rules")
