from pathlib import Path

import pytest

from lifecycle_mapper.analysis import analyze, load_rules
from lifecycle_mapper.documentation import documentation_matches, workflow_units
from test_rules import make_snapshot

RULES = (
    Path(__file__).resolve().parents[1]
    / "tests/fixtures/legacy-profiles/documentation-development-v5"
)


@pytest.mark.parametrize(
    "stage,text",
    [
        ("Collection", "## Data acquisition\n\nDownload the dataset from the survey archive."),
        ("Processing", "## Processing\n\nUse the script to process data and extract features."),
        ("Method", "This package contains code implementing statistical inference methods."),
        (
            "Experimentation",
            "## Experiments\n\nThis repository provides an implementation of the experiments.\n\n```bash\npython run_trials.py\n```",
        ),
        (
            "Evaluation",
            "## Evaluation\n\nRun the evaluation script on test data.\n\n```bash\npython evaluate.py\n```",
        ),
        (
            "Dissemination",
            "## Citation\n\nPlease cite the paper describing this repository.\n\n```bibtex\n@article{sample, title={Scientific result}}\n```",
        ),
    ],
)
def test_documented_stage_workflows_and_source_isolation(tmp_path, stage, text):
    snapshot = make_snapshot(tmp_path, text, "README.md")
    result = analyze(snapshot, "documentation-only", rules_dir=RULES)
    assert stage in result["labels"]
    assert analyze(snapshot, "code-only", rules_dir=RULES)["labels"] == []
    for e in result["evidence"]:
        if e["rule_version"] == "0.5.0-development":
            assert e["end_line"] - e["start_line"] < 12
            assert e["excerpt"] == "\n".join(
                text.splitlines()[e["start_line"] - 1 : e["end_line"]]
            ).rstrip("\r\n")


@pytest.mark.parametrize(
    "text",
    [
        "# Roadmap\n## Future work\nThis package will implement evaluation of model accuracy.",
        "# Installation\nDownload the dependency package for the data analysis example.",
        "# Dependencies\nAnother package implements statistical models.",
        "This repository does not implement evaluation of model accuracy.",
        "This repository uses another package to evaluate model accuracy.",
        "<!-- This repository computes prediction accuracy for experiments. -->",
        "This package provides unit tests that compute prediction accuracy.",
    ],
)
def test_v5_negative_scope_and_infrastructure(text):
    rules, _ = load_rules(RULES)
    for rule in [r for r in rules if r.get("unit_policy") == "documented-workflow-v5"]:
        assert not any(not e["exclusion_reasons"] for e in documentation_matches(text, rule)), rule[
            "id"
        ]


def test_numbered_plain_text_bibliography_is_not_data_acquisition():
    rules, _ = load_rules(RULES)
    rule = next(r for r in rules if r["id"] == "COL_DOC_WORKFLOW_V5_1")
    text = "Scientific data compression software\n\n5. REFERENCES.\nDownload the article about collecting data from this URL."
    assert not any(not e["exclusion_reasons"] for e in documentation_matches(text, rule))
    assert all(u["end_line"] - u["start_line"] < 12 for u in workflow_units(text))


def test_model_conditions_require_both_activity_and_object():
    rule = next(r for r in load_rules(RULES)[0] if r["id"] == "MET_DOC_WORKFLOW_V5_1")
    assert not any(
        not e["exclusion_reasons"] for e in documentation_matches("A model is mentioned.", rule)
    )
