"""Author the candidate catalog as JSON-compatible YAML, without a YAML dependency."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = [
    (
        "Collection",
        "COL",
        "Acquire or generate raw observations for research.",
        [
            r"\b(collect(?:s|ed|ing)?|acquir(?:e|es|ed|ing)|record(?:s|ed|ing)?)\b",
            r"\b(raw (?:research )?data|research dataset|sensor observations|participant responses)\b",
        ],
        [
            r"^\s*def\s+(?:collect|acquire|record)_(?:research_data|sensor_observations|participant_responses)\s*\(",
            r"\b(?:requests\.get|sensor\.read|survey\.responses)\s*\(",
        ],
        "A declared raw research acquisition activity plus an acquisition operation; HTTP alone is insufficient.",
    ),
    (
        "Processing",
        "PRO",
        "Prepare research data through cleaning or transformation.",
        [
            r"\b(clean(?:s|ed|ing)?|preprocess(?:es|ed|ing)?|normaliz(?:e|es|ed|ing))\b",
            r"\b(research dataset|raw research data|sensor observations|experimental measurements)\b",
        ],
        [
            r"^\s*def\s+(?:clean|preprocess|normalize)_(?:research_dataset|sensor_observations|experimental_measurements)\s*\(",
            r"\.(?:dropna|fillna|transform|fit_transform)\s*\(",
        ],
        "A preparation operation scoped to research observations; generic parsing is insufficient.",
    ),
    (
        "Method",
        "MET",
        "Implement a scientific model, algorithm, or analytical technique.",
        [
            r"\b(implement(?:s|ed|ing)?|estimat(?:e|es|ed|ing)|fit(?:s|ted|ting)?)\b",
            r"\b(scientific model|proposed algorithm|statistical model|research method)\b",
        ],
        [
            r"^\s*def\s+(?:fit_statistical_model|implement_proposed_algorithm|estimate_scientific_model)\s*\(",
            r"\b(?:minimize|optimizer\.step|np\.linalg\.solve)\s*\(",
        ],
        "Scientific method implementation, excluding packaging, entry points and software tests. Definition awaits human codebook.",
    ),
    (
        "Experimentation",
        "EXP",
        "Execute controlled research trials or parameter studies.",
        [
            r"\b(run(?:s|ning)?|execut(?:e|es|ed|ing)|conduct(?:s|ed|ing)?)\b",
            r"\b(controlled experiments|parameter sweep|research trials|experimental trials)\b",
        ],
        [
            r"^\s*def\s+(?:run_controlled_experiments|run_parameter_sweep|conduct_research_trials)\s*\(",
            r"^\s*for\s+\w+\s+in\s+(?:parameter_grid|trial_seeds|experimental_conditions)\s*:",
        ],
        "An explicit research trial activity together with iteration over controlled conditions; run.py alone is insufficient.",
    ),
    (
        "Evaluation",
        "EVA",
        "Assess scientific performance against reference outcomes or baselines.",
        [
            r"\b(evaluat(?:e|es|ed|ing)|compar(?:e|es|ed|ing)|assess(?:es|ed|ing)?)\b",
            r"\b(?:predictive performance against (?:a )?baseline|scientific accuracy against ground truth|ablation study|research benchmark against reference)\b",
        ],
        [
            r"^\s*def\s+(?:evaluate_research_predictions|compare_scientific_baselines|evaluate_ablation_study)\s*\(",
            r"\b(?:f1_score|mean_squared_error|accuracy_score)\s*\(\s*(?:ground_truth|reference_labels)\s*,",
        ],
        "Explicit scientific assessment with reference-labelled metric computation; unit tests and isolated metrics are excluded.",
    ),
    (
        "Dissemination",
        "DIS",
        "Communicate or deposit research outputs for external reuse.",
        [
            r"\b(publish(?:es|ed|ing)?|deposit(?:s|ed|ing)?|archiv(?:e|es|ed|ing)|releas(?:e|es|ed|ing))\b",
            r"\b(research (?:results|dataset|software)|scientific findings)\b[^\n]{0,100}\b(?:doi|zenodo|public repository|journal)\b",
        ],
        [
            r"^\s*def\s+(?:deposit_research_dataset|publish_research_results|archive_research_software)\s*\(",
            r"\b(?:zenodo\.deposit|repository\.publish)\s*\(",
        ],
        "External publication/deposition of research outputs; README presence and generic software releases do not suffice.",
    ),
]
FAMILIES = {
    "Collection": [
        r"\b(?:download(?:s|ed|ing)?|collect(?:s|ed|ing)?|acquir(?:e|es|ed|ing)|harvest(?:s|ed|ing)?|generat(?:e|es|ed|ing)|record(?:s|ed|ing)?)\b",
        r"\b(?:research (?:data(?:sets?)?|observations|inputs)|raw (?:research )?data|experimental measurements|sensor (?:data|observations)|participant responses|scientific datasets?)\b",
    ],
    "Processing": [
        r"\b(?:clean(?:s|ed|ing)?|filter(?:s|ed|ing)?|transform(?:s|ed|ing)?|normaliz(?:e|es|ed|ing)|preprocess(?:es|ed|ing)?|prepar(?:e|es|ed|ing)|extract(?:s|ed|ing)?\s+features)\b",
        r"\b(?:research data(?:sets?)?|raw (?:research )?data|scientific datasets?|experimental measurements|sensor observations|features from research data)\b",
    ],
    "Method": [
        r"\b(?:implement(?:s|ed|ing)?|provid(?:e|es|ed|ing)|estimat(?:e|es|ed|ing)|fit(?:s|ted|ting)|offer(?:s|ed|ing)?)\b",
        r"\b(?:scientific models?|statistical models?|proposed algorithms?|research methods?|analytical methods?|statistical analysis|principal component analysis|linear regression|bayesian inference|finite element methods?)\b",
    ],
    "Experimentation": [
        r"\b(?:run(?:s|ning)?|execut(?:e|es|ed|ing)|conduct(?:s|ed|ing)?|perform(?:s|ed|ing)?)\b",
        r"\b(?:controlled experiments?|research trials?|experimental trials?|parameter sweeps?|scientific simulations?|experimental workflows?)\b",
    ],
    "Evaluation": [
        r"\b(?:evaluat(?:e|es|ed|ing)|assess(?:es|ed|ing)?|compar(?:e|es|ed|ing)|measur(?:e|es|ed|ing))\b",
        r"\b(?:predictive performance|research outputs?|scientific accuracy|research benchmarks?|ablation stud(?:y|ies)|scientific models?)\b[\s\S]{0,160}\b(?:baselines?|ground truth|reference data|reference labels|scientific metrics|statistical tests|f1|accuracy|precision|recall)\b",
    ],
    "Dissemination": [
        r"\b(?:publish(?:es|ed|ing)?|deposit(?:s|ed|ing)?|archiv(?:e|es|ed|ing)|export(?:s|ed|ing)?|present(?:s|ed|ing)?|distribut(?:e|es|ed|ing)|prepar(?:e|es|ed|ing))\b",
        r"\b(?:research (?:results|datasets?|software|artifacts)|scientific (?:findings|figures|results)|publication[- ]ready figures)\b",
    ],
}
CONTEXT = r"\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b"
WORKFLOW_CONTEXT = r"\b(?:run|use|execute)\s+(?:this|the|our)\s+(?:command|workflow|tutorial)\b"
POLARITY = r"\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b"
SCOPE = [
    r"\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b",
    r"\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b",
]
HEADINGS = [
    r"\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b"
]
COMMAND = r"^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)"
for stage, prefix, description, documentation, code, justification in DEFINITIONS:
    common = {
        "stage": stage,
        "description": description,
        "supporting": [],
        "required_evidence_fields": [
            "repository",
            "commit",
            "path",
            "content_sha256",
            "start_line",
            "end_line",
            "matched_conditions",
            "url",
        ],
        "status": "unadjudicated-candidate",
        "justification": justification,
    }
    rules = [
        {
            **common,
            "id": f"{prefix}_CODE_ACTIVITY_V1",
            "source": "code",
            "positive": code,
            "exclusions": [
                r"\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b"
            ],
            "version": "0.1.0-candidate",
            "window_lines": 8,
        }
    ]
    for layer, patterns in [
        ("explicit", documentation),
        ("contextual", FAMILIES[stage]),
        ("workflow", FAMILIES[stage]),
    ]:
        rules.append(
            {
                **common,
                "id": f"{prefix}_DOC_{layer.upper()}_V2",
                "source": "documentation",
                "positive": patterns,
                "exclusions": [POLARITY],
                "scope_exclusions": SCOPE,
                "heading_exclusions": HEADINGS,
                "context_pattern": WORKFLOW_CONTEXT if layer == "workflow" else CONTEXT,
                "command_pattern": COMMAND,
                "layer": layer,
                "window_lines": 12,
                "version": "0.2.0-candidate",
                "justification": justification
                + " Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.",
            }
        )
    catalog = ROOT / "rules" / f"{stage.lower()}.yaml"
    retained = (
        [r for r in json.loads(catalog.read_text())["rules"] if r["version"] == "0.3.0-candidate"]
        if catalog.exists()
        else []
    )
    rules.extend(retained)
    catalog.write_text(
        json.dumps(
            {
                "version": "0.3.0-candidate" if retained else "0.2.0-candidate",
                "stage": stage,
                "rules": rules,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
package = ROOT / "src/lifecycle_mapper/rules"
package.mkdir(exist_ok=True)
for path in (ROOT / "rules").glob("*.yaml"):
    (package / path.name).write_bytes(path.read_bytes())
