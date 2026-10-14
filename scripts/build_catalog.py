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
for stage, prefix, description, documentation, code, justification in DEFINITIONS:
    rules = []
    for source, patterns in [("documentation", documentation), ("code", code)]:
        rules.append(
            {
                "id": f"{prefix}_{'DOC' if source == 'documentation' else 'CODE'}_ACTIVITY_V1",
                "stage": stage,
                "source": source,
                "description": description,
                "positive": patterns,
                "supporting": [],
                "exclusions": [
                    r"\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b"
                ],
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
                "version": "0.1.0-candidate",
                "status": "unadjudicated-candidate",
                "window_lines": 1 if source == "documentation" else 8,
                "justification": justification,
            }
        )
    (ROOT / "rules" / f"{stage.lower()}.yaml").write_text(
        json.dumps(
            {"version": "0.1.0-candidate", "stage": stage, "rules": rules}, sort_keys=True, indent=2
        )
        + "\n"
    )
package = ROOT / "src/lifecycle_mapper/rules"
package.mkdir(exist_ok=True)
for path in (ROOT / "rules").glob("*.yaml"):
    (package / path.name).write_bytes(path.read_bytes())
