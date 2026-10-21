import json
from pathlib import Path

src = Path("configs/documentation-development-v5")
dst = Path("configs/multilanguage-development-v5.1")
dst.mkdir(exist_ok=True)
exts = [".c", ".cpp", ".cc", ".h", ".hpp", ".java", ".js", ".ts", ".go", ".rs", ".scala"]
specs = [
    (
        "Collection",
        "ACQUIRE",
        r"\b(?:curl_easy_perform|curl_exec|fetch|readSensor|read_sensor|downloadData|downloadDataset|downloadCorpus)\s*\(",
        r"\b(?:dataset|corpus|observations|measurements|raw_data|dataUrl|datasetUrl|research_data)\b",
        "Acquire research inputs with a research-data identifier in the same executable block.",
    ),
    (
        "Processing",
        "TRANSFORM",
        r"\b(?:normalize|normalise|standardize|tokenize|preprocess|extractFeatures|extract_features|resample|splitDataset|cleanData)\s*\(",
        r"\b(?:data|dataset|corpus|samples|features|measurements|tokens|sentences|featureVector)\b",
        "Call a data-preparation operation on identified research-input variables.",
    ),
    (
        "Method",
        "MODEL_CALL",
        r"\b(?:fit|train|predict|infer|optimize|solve)\s*\(",
        r"\b(?:model|estimator|classifier|solver)\b",
        "Invoke scientific model computation with research-input variables.",
    ),
    (
        "Method",
        "NAMED_COMPUTATION",
        r"(?:\b[A-Za-z_]\w*(?:\[[^\]\n]+\])?\s*(?:\+=|-=|\*=|/=|=)|\b(?:sqrt|pow|exp|log|dot|matmul|solve|min|max)\s*\()",
        r"(?:\b[A-Za-z_]\w*(?:\[[^\]\n]+\])?\s*[*/+-]\s*[A-Za-z_0-9]|\b(?:sqrt|pow|exp|log|dot|matmul|solve)\s*\()",
        "Numerical operations within an explicitly named scientific computation routine.",
    ),
    (
        "Experimentation",
        "TRIALS",
        r"\b(?:for|while)\s*\(",
        r"\b(?:n_trials|num_trials|trialSeeds|seeds|experimentalConditions|parameterGrid|param_grid|nRepeats|trial|experiment)\b",
        "Controlled/repeated research runs with a scientific call and recorded outcomes.",
    ),
    (
        "Evaluation",
        "METRIC_CALL",
        r"\b(?:f1Score|f1_score|precisionScore|recallScore|accuracyScore|meanSquaredError|rmse|rocAuc|computeAccuracy)\s*\(",
        r"\b(?:y_true|referenceLabels|reference_labels|ground_truth|gold|labels|predictions|predicted)\b",
        "Scientific metric calls connected to reference/predicted research outcomes.",
    ),
    (
        "Evaluation",
        "METRIC_ARITHMETIC",
        r"\b(?:precision|recall|f1|fscore|accuracy|rmse|mse)\s*=",
        r"(?:/|\b(?:sqrt|pow)\s*\()",
        "Explicit metric arithmetic connected to reference/prediction counts.",
    ),
    (
        "Dissemination",
        "EXPORT",
        r"\b(?:savefig|saveFigure|exportFigure|writeFigure|exportPlot|writeReport|publishResults)\s*\(",
        r"\b(?:results|plot|figure|report|researchOutputs|trialResults)\b",
        "Export a scientific communication artifact with result/figure/report context.",
    ),
    (
        "Dissemination",
        "DEPOSIT",
        r"\b(?:zenodo\s*\.\s*deposit|repository\s*\.\s*publish)\s*\(",
        r"\b(?:researchOutputs|research_outputs|trialResults|researchDataset)\b",
        "Deposit identified research outputs through an explicit publication call.",
    ),
]
stages = {
    "Collection": "COL",
    "Processing": "PRO",
    "Method": "MET",
    "Experimentation": "EXP",
    "Evaluation": "EVA",
    "Dissemination": "DIS",
}
for path in src.glob("*.yaml"):
    d = json.loads(path.read_text())
    d["version"] = "0.5.1-development"
    for stage, key, p1, p2, desc in specs:
        if stage != d["stage"]:
            continue
        positives = [p1, p2]
        if key == "MODEL_CALL":
            positives.append(r"\b(?:data|dataset|features|samples|observations|targets|labels)\b")
        if key == "TRIALS":
            positives += [
                r"\b(?:runTrial|run_trial|runExperiment|run_experiment|fit|train|evaluate)\s*\(",
                r"\b(?:results|scores|observations|outcomes)\b",
            ]
        if key == "METRIC_ARITHMETIC":
            positives.append(
                r"\b(?:truePositives|falsePositives|tp|fp|fn|correct|predictions|labels|gold|predicted|n_correct)\b"
            )
        rule = {
            "id": stages[stage] + "_CODE_BRACE_" + key + "_V51",
            "stage": stage,
            "source": "code",
            "version": "0.5.1-development",
            "description": desc,
            "positive": positives,
            "supporting": [],
            "exclusions": [],
            "required_evidence_fields": [
                "repository",
                "commit",
                "path",
                "content_sha256",
                "start_line",
                "end_line",
                "matched_conditions",
                "url",
                "code_syntax_policy",
                "code_context",
            ],
            "justification": desc
            + " Comments/literals are masked and all matching conditions must occur inside one executable brace block, excluding declarations and software-test paths. Lexical candidate evidence, not semantic proof.",
            "status": "unadjudicated-development-candidate",
            "window_lines": 12,
            "extensions": exts,
            "scope": "lexical-block",
            "detector": "brace-lexical-v1",
        }
        if key == "NAMED_COMPUTATION":
            rule["context_pattern"] = (
                r"\b\w*(?:cosine|jaccard|similarity|likelihood|posterior|entropy|gradient|eigen|svd|estimate|infer|optim|regress|classifier|computeSimScore)\w*\s*\("
            )
        d["rules"].append(rule)
    (dst / path.name).write_text(json.dumps(d, indent=2) + "\n")
print("Created v5.1 profile with unchanged documentation rules and 9 added brace-code rules.")
portable_specs = [
    (
        "Collection",
        "ACQUIRE",
        [
            r"\b(?:fetch|download(?:\.file|[_-]?(?:data|dataset|corpus))?|curl_easy_perform|read[_-]?sensor|acquire[_-]?data)\b\s*(?:\(|[A-Za-z_$])",
            r"\b(?:dataset|corpus|observations|measurements|raw_data|dataUrl|datasetUrl|research_data)\b",
        ],
        "Acquire identified research inputs.",
    ),
    (
        "Processing",
        "TRANSFORM",
        [
            r"\b(?:normalize|normalise|standardize|tokenize|preprocess|extract[_-]?features|resample|split[_-]?dataset|clean[_-]?data)\b\s*(?:\(|[A-Za-z_$])",
            r"\b(?:data|dataset|corpus|samples|features|measurements|tokens|sentences|featureVector)\b",
        ],
        "Transform identified research inputs.",
    ),
    (
        "Method",
        "MODEL",
        [
            r"\b(?:fit|train|predict|infer|optimize|optim|solve|lm|glm)\b\s*(?:\(|[A-Za-z_$])",
            r"\b(?:model|estimator|classifier|solver|regression)\b",
            r"\b(?:data|dataset|features|samples|observations|targets|labels)\b",
        ],
        "Invoke scientific model computation on research inputs.",
    ),
    (
        "Experimentation",
        "TRIALS",
        [
            r"\b(?:run[_-]?trial|run[_-]?experiment|lapply|parallelMap|map|sweep)\b\s*(?:\(|[A-Za-z_$])",
            r"\b(?:trialSeeds|trial_seeds|seeds|experimentalConditions|parameterGrid|param_grid|trial_conditions)\b",
            r"\b(?:results|scores|outcomes)\b",
        ],
        "Apply a research runner across explicit conditions and retain results.",
    ),
    (
        "Evaluation",
        "METRIC",
        [
            r"\b(?:f1[_-]?score|precision[_-]?score|recall[_-]?score|accuracy[_-]?score|mean[_-]?squared[_-]?error|rmse|roc[_-]?auc|compute[_-]?accuracy)\b\s*(?:\(|[A-Za-z_$])",
            r"\b(?:y_true|y_test|referenceLabels|reference_labels|ground_truth|gold|labels|predictions|predicted)\b",
        ],
        "Compute a research metric against identified outcomes/reference labels.",
    ),
    (
        "Evaluation",
        "ARITHMETIC",
        [
            r"\b(?:precision|recall|f1|fscore|accuracy|rmse|mse)\s*(?:=|<-)",
            r"(?:/|\b(?:sqrt|pow)\s*\()",
            r"\b(?:truePositives|falsePositives|tp|fp|fn|correct|predictions|labels|gold|predicted|n_correct)\b",
        ],
        "Compute explicit metric arithmetic using prediction/reference counts.",
    ),
    (
        "Dissemination",
        "EXPORT",
        [
            r"\b(?:savefig|ggsave|saveFigure|exportFigure|writeFigure|exportPlot|writeReport|publishResults)\b\s*(?:\(|[A-Za-z_$])",
            r"\b(?:results|plot|figure|report|researchOutputs|trialResults)\b",
        ],
        "Export a scientific communication artifact from research outputs.",
    ),
]
for path in dst.glob("*.yaml"):
    d = json.loads(path.read_text())
    for stage, key, positive, desc in portable_specs:
        if stage != d["stage"]:
            continue
        d["rules"].append(
            {
                "id": stages[stage] + "_CODE_PORTABLE_" + key + "_V51",
                "stage": stage,
                "source": "code",
                "version": "0.5.1-development",
                "description": desc,
                "positive": positive,
                "supporting": [],
                "exclusions": [],
                "required_evidence_fields": [
                    "repository",
                    "commit",
                    "path",
                    "content_sha256",
                    "start_line",
                    "end_line",
                    "matched_conditions",
                    "url",
                    "code_syntax_policy",
                    "languages",
                ],
                "justification": desc
                + " All conditions must occur within one lexical statement. Comments and literals are masked. This is a language-neutral candidate heuristic, not a semantic proof.",
                "status": "unadjudicated-development-candidate",
                "window_lines": 12,
                "scope": "portable-statement",
                "detector": "portable-lexical-v1",
            }
        )
    path.write_text(json.dumps(d, indent=2) + "\n")
print("Added 7 portable lexical rules across all recognized source languages.")
