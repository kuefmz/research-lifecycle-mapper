"""Extend v5.2 with explicit physical-equation and agent-simulation evidence."""

import csv
import json
from pathlib import Path

source = Path("configs/workflow-development-v5.2")
target = Path("configs/simulation-development-v5.3")
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
specs = [
    dict(
        id="MET_CODE_PHYSICAL_EQUATION_V53",
        stage="Method",
        source="code",
        detector="portable-lexical-v1",
        scope="portable-statement",
        positive=[
            r"\b(?:energy|density|pressure|temperature|radiation|concentration|resistance|conductance|flux|velocity|acceleration|potential|entropy|likelihood)\w*\s*(?:<-|=(?!=))",
            r"(?:<-|=(?!=))\s*[^;\n]*\b[A-Za-z_]\w*\s*[*/^]\s*[A-Za-z_(]",
        ],
        file_context_patterns=[r"\b(?:exp|sqrt|log|log10|sin|cos|pow)\s*\("],
        description="Assign an identified physical/statistical quantity using multiplicative arithmetic, in source containing a nonlinear numerical operation. This is a lexical equation candidate; the file-context condition is not data-flow proof.",
    ),
    dict(
        id="MET_CODE_AGENT_DECISION_V53",
        stage="Method",
        source="code",
        detector="brace-lexical-v1",
        scope="lexical-block",
        extensions=[".java", ".js", ".ts", ".cpp", ".cc"],
        positive=[
            r"\b\w+\s*=\s*agent\w*\s*\.\s*(?:decide|act|chooseAction)\s*\(",
            r"\b(?:market|environment|world)\w*\s*\.\s*(?:send|applyAction|step)\s*\([^;\n]*\bagent\w*\b",
        ],
        description="Compute an agent decision and dispatch its action to a simulated environment in one executable brace block.",
    ),
    dict(
        id="EXP_CODE_AGENT_TIME_STEPS_V53",
        stage="Experimentation",
        source="code",
        detector="brace-lexical-v1",
        scope="lexical-block",
        extensions=[".java", ".js", ".ts", ".cpp", ".cc"],
        positive=[
            r"\b(?:while|for)\s*\([^\n]*(?:currentTick|timeStep|timestep|simulationTime)\s*\(",
            r"\b(?:queryAllAgents|updateAgents|stepAgents|advanceAgents)\s*\(",
            r"\.\s*(?:nextTick|advanceTime|nextTimeStep)\s*\(",
        ],
        description="Execute agent updates inside a bounded simulated-time loop and explicitly advance simulated time; not a generic software loop.",
    ),
]
rows = []
for path in sorted(source.glob("*.yaml")):
    catalog = json.loads(path.read_text())
    catalog["version"] = "0.5.3-development"
    # Tighten development proxies using evidence roles rather than stage words in titles or paths.
    for rule in catalog["rules"]:
        key = rule["id"]
        if key == "COL_DOC_WORKFLOW_V5_1":
            rule["positive"][0] = (
                r"(?<![\w./-])(?:collect\w*|acquir\w*|gather\w*|record\w*|survey\w*|recruit\w*)\b"
            )
        if key == "PRO_DOC_WORKFLOW_V5_1":
            rule["positive"][0] = (
                r"(?<![\w./-])(?:preprocess\w*|clean\w*|normaliz\w*|tokeniz\w*|transform\w*|convert\w*|merg\w*|split\w*|augment\w*|extract\w*\s+features?|prepar(?:e|es|ed|ing)\s+(?:the\s+)?data|data preparation)\b"
            )
        if key == "EXP_DOC_WORKFLOW_V5_1":
            rule["positive"][1] = (
                r"\b(?:code|scripts?|implementation|run|runs|running|ran|perform(?:s|ed|ing)?|conduct(?:s|ed|ing)?|reproduc\w*|replicat\w*|python|bash|Rscript|MATLAB|notebooks?|simulat(?:e|es|ed|ing)|configurations?)\b"
            )
        if key == "EVA_DOC_WORKFLOW_V5_1":
            rule["positive"].append(
                r"\b(?:accuracy|precision|recall|f1|metrics?|baselines?|confidence intervals?|significance|effect sizes?|held[- ]out|test sets?|test data|timing|runtime|elapsed|memory usage|prediction error)\b"
            )
        if key == "EVA_DOC_WORKFLOW_V5_2":
            rule["positive"].append(
                r"\b(?:accuracy|precision|recall|f1|metrics?|baselines?|confidence intervals?|significance|held[- ]out|cross[- ]validation|timing|runtime|prediction error)\b"
            )
        if key == "DIS_DOC_WORKFLOW_V5_2":
            rule["positive"] = [
                r"(?<![\w./-])(?:plots?|plotting|figures?|tables?|visualiz\w*|latex|knit\w*|reports?)\b",
                r"\b(?:paper|publication|manuscript|research results|publish\w*|export\w*|savefig|ggsave)\b",
            ]
        if rule["source"] == "documentation":
            rule["version"] = "0.5.3-development"
            rule["heading_exclusions"] = list(rule.get("heading_exclusions", [])) + [
                r"\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b"
            ]
    if catalog["stage"] == "Processing":
        template = next(
            r
            for r in catalog["rules"]
            if r["source"] == "documentation" and r.get("unit_policy") == "documented-workflow-v5"
        )
        catalog["rules"].append(
            dict(
                template,
                id="PRO_DOC_DATA_SUBSET_V53",
                version="0.5.3-development",
                positive=[
                    r"\b(?:subset|subsample|subsetting|subsampling|tail)\b",
                    r"\b(?:dataset|data|triples|corpus|observations|samples)\b",
                ],
                description="Construct a subset of identified research inputs; not filtering a software log or a path name.",
                justification="Explicit research-input subsetting is preprocessing evidence.",
            )
        )
    if catalog["stage"] == "Method":
        template = next(r for r in catalog["rules"] if r["id"] == "MET_DOC_COMPUTATIONAL_STEPS_V52")
        catalog["rules"].append(
            dict(
                template,
                id="MET_DOC_EXPERIMENTAL_DESIGN_V53",
                version="0.5.3-development",
                positive=[
                    r"\b(?:statistical design of experiments|factorial design|fractional factorial|response surface methodology)\b",
                    r"\b(?:code|package|implementation|implement\w*|developed)\b",
                ],
                unit_policy="documented-workflow-v5",
                document_context_pattern=r"\b(?:study|research|experiment\w*)\b",
                description="Repository implementation of an explicitly named experimental-design method.",
                justification="Named statistical design plus local implementation evidence; merely mentioning an experiment is insufficient.",
            )
        )
        catalog["rules"].append(
            dict(
                template,
                id="MET_DOC_AGENT_MECHANISM_V53",
                version="0.5.3-development",
                positive=[
                    r"\b(?:agents?|multiagent|multi-agent)\b",
                    r"\b(?:trade|interact|decid\w*|behaviou?r|actions?)\b",
                    r"\b(?:market|environment|simulation|simulat\w*)\b",
                ],
                unit_policy="documented-workflow-v5",
                document_context_pattern=r"\b(?:API|code|package|simulation|model)\b",
                description="Documented agent interaction/decision mechanism in a simulation implementation.",
                justification="Agent mechanism with its simulated environment, not merely a generic model or paper title.",
            )
        )
    if catalog["stage"] == "Dissemination":
        template = next(
            r
            for r in catalog["rules"]
            if r["source"] == "documentation" and r.get("unit_policy") == "documented-workflow-v5"
        )
        catalog["rules"].append(
            dict(
                template,
                id="DIS_DOC_RESEARCH_RESULTS_ARCHIVE_V53",
                version="0.5.3-development",
                positive=[
                    r"\b(?:experiment|research|study)\s+data\s+and\s+results\b",
                    r"\b(?:on|for|from|of|accompany\w*)\b",
                ],
                description="Repository explicitly presents archived research data and results; does not by itself establish runnable experiments or evaluation code.",
                justification="Sharing archived research outputs is Dissemination evidence.",
            )
        )
    if catalog["stage"] == "Experimentation":
        catalog["rules"].append(
            dict(
                id="EXP_CODE_FACTORIAL_RUNS_V53",
                stage="Experimentation",
                source="code",
                version="0.5.3-development",
                detector="portable-lexical-v1",
                scope="portable-statement",
                positive=[
                    r"\b(?:apply|lapply|sapply|map)\s*\(",
                    r"\bdesign\b",
                    r"\b(?:experiment|run_experiment|run_trial)\b",
                ],
                supporting=[],
                exclusions=[],
                window_lines=12,
                status="unadjudicated-development-candidate",
                required_evidence_fields=fields,
                description="Execute an experimental function across an explicit design table.",
                justification="Scientific runner over design rows, not a generic collection map.",
            )
        )
    for spec in specs:
        if spec["stage"] != catalog["stage"]:
            continue
        rule = dict(
            spec,
            version="0.5.3-development",
            supporting=[],
            exclusions=[],
            window_lines=12,
            status="unadjudicated-development-candidate",
            required_evidence_fields=fields,
            justification=spec["description"]
            + " Comments and string contents are masked. No repository identity or reference label is used.",
        )
        catalog["rules"].append(rule)
    if catalog["stage"] == "Collection":
        template = next(
            r
            for r in catalog["rules"]
            if r["source"] == "documentation" and r["layer"] == "explicit"
        )
        rule = dict(
            template,
            id="COL_DOC_PROVIDED_MEASUREMENTS_V53",
            version="0.5.3-development",
            positive=[
                r"\b(?:sample\s+(?:data|dataset)|(?:data|dataset)\s+(?:contains?|includes?))\b",
                r"\b(?:measured|observed|recorded|collected)\b",
                r"\b(?:meteorological|temperature|precipitation|humidity|wind|radiation|sensor|participants?|patients?|survey)\b",
            ],
            context_pattern=r"\b(?:sample|data|dataset|our|we|provided|contains)\b",
            description="Documentation explicitly describes supplied/sample measured research observations.",
            justification="Supplied measured observations are Collection evidence; generic generated examples or a data folder alone do not satisfy this rule.",
        )
        catalog["rules"].append(rule)
    target.joinpath(path.name).write_text(json.dumps(catalog, indent=2) + "\n")
    rows.extend(
        {"file": path.name, "rule": json.dumps(r, sort_keys=True)} for r in catalog["rules"]
    )
with target.joinpath("rule_catalog.csv").open("w") as stream:
    writer = csv.DictWriter(stream, fieldnames=["file", "rule"])
    writer.writeheader()
    writer.writerows(rows)
print(len(rows), "rules")
