"""Build the consolidated development profile; no repository identities enter rules."""

import csv
import hashlib
import json
from pathlib import Path

source = Path("configs/simulation-development-v5.3")
target = Path("configs/consolidated-development-v5.4")
target.mkdir(exist_ok=True)
fields = [
    "repository",
    "commit",
    "path",
    "content_sha256",
    "start_line",
    "end_line",
    "matched_conditions",
    "url",
]
# Every tuple describes conjunctive conditions; alternatives are within a condition.
doc_specs = [
    (
        "Method",
        "IMPLEMENTATION_OBJECT",
        [
            r"\b(?:implementation\s+of|implements?|implemented|contains?\s+(?:two\s+versions?\s+of\s+)?(?:the\s+)?(?:models?|algorithms?)|models?\s+simulating)\b",
            r"\b(?:parser|neural|tensor|bayesian|statistical|mathematical|mechanistic|differential|regression|optimization|inference|sampling|classification|discovery|reconstruction)\b",
        ],
    ),
    (
        "Method",
        "NUMERICAL_TECHNIQUE",
        [
            r"\b(?:compute\w*|calculat\w*|estimat\w*|implement\w*|learn\w*|discover\w*)\b",
            r"\b(?:compatibility probability|matrix functions?|gaussian process|grammar[- ]guided|symbolic regression|differential equations?|posterior|likelihood|dependency pars(?:er|ing)|neural networks?|statistical models?)\b",
        ],
    ),
    (
        "Evaluation",
        "REPORTED_METRIC",
        [
            r"\b(?:accuracy|precision|recall|f1|error rate|misclassification rate|runtime|run time|memory usage)\b",
            r"\b(?:results?|achiev\w*|obtain\w*|performance|measur\w*|evaluat\w*|report\w*|baseline)\b",
            r"\d+(?:\.\d+)?\s*(?:\\?%|seconds?|milliseconds?|MB|GB)\b?",
        ],
    ),
    (
        "Evaluation",
        "RESEARCH_EVALUATION_COMMAND",
        [
            r"(?m)^\s*(?:(?:python[23]?|bash|sh|Rscript|julia|matlab)\s+|\./)[^\n]*(?:eval(?:uate|uation)?|acc(?:uracy|s)?|benchmark|metrics?|score|test[_-]and[_-]train|train[_-]and[_-]test)[\w./-]*",
            r"\b(?:model|experiment\w*|dataset|data|train|validation|test|results?|accurac\w*|metric\w*|parser)\b",
        ],
    ),
    (
        "Experimentation",
        "SCIENTIFIC_TRAIN_TEST_COMMAND",
        [
            r"(?m)^\s*(?:(?:python[23]?|bash|sh|Rscript|julia|matlab)\s+|\./)[^\n]*(?:train|experiment|simulation|pipeline|run)[\w./-]*",
            r"\b(?:train|training|validation|experiments?|simulations?|parser|model|results?)\b",
        ],
    ),
    (
        "Processing",
        "DOCUMENTED_INPUT_PREPARATION",
        [
            r"\b(?:preprocess\w*|prepar\w*|transform\w*|convert\w*|filter\w*|outlier rejection|outlier analysis)\b",
            r"\b(?:input data|datasets?|raw data|training data|triples|sequences|images|observations|observer\w*)\b",
        ],
    ),
    (
        "Dissemination",
        "LINKED_RESEARCH_ARTIFACT",
        [
            r"(?:arxiv\.org/(?:abs|pdf)/|doi\.org/|aclanthology\.org/|aclweb\.org/anthology/|https?://[^\s)>]+\.pdf\b)",
            r"\b(?:code|repository|software|toolbox|package|experiments?|accompanies|replicat\w*|reproduc\w*)\b",
        ],
    ),
]
code_specs = [
    (
        "Method",
        "SCIENTIFIC_NUMERICAL_CALL",
        [
            r"\b(?:np\.linalg\.(?:solve|inv|eigh|eig|svd)|scipy\.optimize\.(?:minimize|least_squares)|trainNetwork|fitnet|patternnet|feedforwardnet|fminsearch)\s*\(",
            r"\(\s*[A-Za-z_]\w*",
        ],
    ),
    (
        "Method",
        "ODE_SOLVER",
        [
            r"\b(?:ode15s|ode45|ode23s?|ode113|odeint|solve_ivp|NDSolve|NDSolveValue|DSolve)\s*[\[(]",
            r"(?:@\w+|\b(?:model|rhs|fun|func|system|deriv\w*|t|tspan|y0|initial\w*)\b)",
        ],
    ),
    (
        "Method",
        "SCIENTIFIC_FIT_CALL",
        [r"\b\w+\s*\.\s*(?:fit|predict|forward|backward)\s*\(", r"\(\s*[A-Za-z_]\w*"],
        [r"\b(?:torch|tensorflow|keras|sklearn|scipy|numpy|Flux|GaussianProcesses)\b"],
    ),
    (
        "Method",
        "STATISTICAL_ESTIMATOR",
        [
            r"\b(?:lm|glm|optim|optimize|svd|eigen|nnls|lsqnonneg|fminunc|fmincon|fitglm|fitlm|FindMinimum|FindMaximum)\s*[\[(]",
            r"[\[(]\s*[A-Za-z_@]\w*",
        ],
    ),
    (
        "Experimentation",
        "ODE_SIMULATION_RUN",
        [
            r"\b(?:ode15s|ode45|ode23s?|ode113|odeint|solve_ivp)\s*\(",
            r"\b(?:t|tspan|time|times|t_eval)\b",
            r"\b(?:y0|initial\w*|state0)\b",
        ],
    ),
    (
        "Evaluation",
        "STATISTICAL_COMPARISON",
        [
            r"\b(?:t\.test|wilcox\.test|anova|ttest|ttest_ind|ttest_rel|mannwhitneyu|kstest|ks_2samp|chisquare|cor_test|cor\.test)\s*\(",
            r"\(\s*[A-Za-z_]\w*",
        ],
    ),
    (
        "Evaluation",
        "CROSS_VALIDATION_CALL",
        [r"\b(?:cross_val_score|cross_validate|crossval|cv\.glmnet)\s*\(", r"\(\s*[A-Za-z_]\w*"],
    ),
]
rows = []
for path in sorted(source.glob("*.yaml")):
    d = json.loads(path.read_text())
    d["version"] = "0.5.4-development"
    for rule in d["rules"]:
        if rule["id"] == "COL_DOC_RESEARCH_V3":
            rule["positive"][0] = (
                r"\b(?:collect(?:s|ed|ing)?|acquir(?:e|es|ed|ing)|record(?:s|ed|ing)?|gather(?:s|ed|ing)?|recruit(?:s|ed|ing)?)\b"
            )
            rule["positive"].append(
                r"\b(?:raw|sensor|participants?|patients?|responses|observations|measurements|survey|corpus\s+construct\w*)\b"
            )
            rule["version"] = "0.5.4-development"
        if rule["id"] == "COL_DOC_WORKFLOW_V5_1":
            rule["unit_policy"] = "sentence-scope-v54"
            rule["layer"] = "explicit"
            rule["context_pattern"] = (
                r"\b(?:we|our|this (?:study|repository|software|experiment)|collected (?:data|responses)|recorded (?:data|responses))\b"
            )
            rule["version"] = "0.5.4-development"
        if rule["id"] in {"COL_DOC_RESEARCH_V3", "COL_DOC_WORKFLOW_V5_1"}:
            rule["exclusions"] = list(rule["exclusions"]) + [
                r"\b(?:could|would|might|hypothetically|in principle)\b"
            ]
        if rule["id"] == "PRO_DOC_WORKFLOW_V5_1":
            rule["exclusions"] = list(rule["exclusions"]) + [
                r"\b(?:reduced model|model reduction|reduced[- ]order model)\b"
            ]
            rule["version"] = "0.5.4-development"
    for stage, name, patterns in doc_specs:
        if stage != d["stage"]:
            continue
        # Correct a percentage boundary without pretending a number alone is a metric.
        if name == "REPORTED_METRIC":
            patterns[-1] = r"\d+(?:\.\d+)?\s*(?:\\?%|seconds?\b|milliseconds?\b|MB\b|GB\b)"
        template = next(
            r
            for r in d["rules"]
            if r["source"] == "documentation" and r.get("unit_policy") == "documented-workflow-v5"
        )
        rule = dict(
            template,
            id=stage[:3].upper() + "_DOC_" + name + "_V54",
            version="0.5.4-development",
            positive=patterns,
            description=name.lower().replace("_", " "),
            justification="Conjunctive documentation evidence reviewed across the development log; no repository identity or labels enter matching.",
            exclusions=[r"\b(?:not implemented|future work|planned|todo|hypothetical)\b"],
            scope_exclusions=[
                r"\b(?:other|external|third[- ]party)\s+(?:repository|software|package|tool)\b"
            ],
            context_pattern=r"\b(?:we|our|this|code|repository|package|software|toolbox|model|method|algorithm|experiment\w*|results?|parser)\b",
        )
        d["rules"].append(rule)
    for spec in code_specs:
        stage, name, patterns, *context = spec
        if stage != d["stage"]:
            continue
        rule = dict(
            id=stage[:3].upper() + "_CODE_" + name + "_V54",
            version="0.5.4-development",
            stage=stage,
            source="code",
            detector="portable-lexical-v1",
            scope="portable-statement",
            positive=patterns,
            supporting=[],
            exclusions=[],
            window_lines=12,
            status="unadjudicated-development-candidate",
            required_evidence_fields=fields,
            description=name.lower().replace("_", " "),
            justification="Executable scientific API evidence with argument/context requirements; comments/literals masked. No general semantic guarantee.",
        )
        if context:
            rule["file_context_patterns"] = context[0]
        d["rules"].append(rule)
    target.joinpath(path.name).write_text(json.dumps(d, indent=2) + "\n")
    rows.extend({"file": path.name, "rule": json.dumps(r, sort_keys=True)} for r in d["rules"])
with target.joinpath("rule_catalog.csv").open("w") as stream:
    writer = csv.DictWriter(stream, fieldnames=["file", "rule"])
    writer.writeheader()
    writer.writerows(rows)
print(len(rows), "rules")

# Deterministic checksum record; the corpus manifest independently hashes runtime rules.

checksums = {
    p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.glob("*.yaml"))
}
target.joinpath("profile_checksums.json").write_text(
    json.dumps(
        {
            "version": "0.5.4-development",
            "rule_count": len(rows),
            "development_only": True,
            "yaml_sha256": checksums,
        },
        indent=2,
    )
    + "\n"
)
