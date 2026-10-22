import pytest

from lifecycle_mapper import STAGES
from legacy_catalog import analyze, load_rules
from lifecycle_mapper.documentation import documentation_matches
from test_rules import make_snapshot

CONTEXTUAL = {
    "Collection": "This package downloads experimental measurements.",
    "Processing": "This software filters research datasets.",
    "Method": "Our library provides principal component analysis.",
    "Experimentation": "This tool performs scientific simulations.",
    "Evaluation": "This software assesses scientific accuracy against reference data.",
    "Dissemination": "Our tool exports publication-ready figures.",
}


@pytest.mark.parametrize("stage", STAGES)
def test_layered_rules_have_individual_positive_and_negative_examples(stage):
    rules, _ = load_rules()
    explicit = {
        "Collection": "We collect raw research data.",
        "Processing": "We clean research dataset.",
        "Method": "We implement proposed algorithm.",
        "Experimentation": "We run controlled experiments.",
        "Evaluation": "We evaluate predictive performance against a baseline.",
        "Dissemination": "We deposit research dataset on Zenodo with DOI.",
    }
    for rule in [r for r in rules if r["stage"] == stage and r["source"] == "documentation"]:
        if rule["id"].endswith("RESEARCH_V3"):
            positive = {
                "Collection": "This code downloads datasets.",
                "Processing": "This code preprocesses datasets.",
                "Method": "This code implements an inference algorithm.",
                "Experimentation": "This code runs simulations.",
                "Evaluation": "This code evaluates prediction accuracy.",
                "Dissemination": "This code accompanies the paper described at https://arxiv.org/abs/1234.1234",
            }[stage]
        elif rule["layer"] == "explicit":
            positive = explicit[stage]
        elif rule["layer"] == "contextual":
            positive = CONTEXTUAL[stage]
        else:
            positive = (
                CONTEXTUAL[stage]
                + " Run this command:\n```bash\nmapper process --input observations.csv\n```"
            )
        matches = documentation_matches(positive, rule)
        assert matches and any(not match["exclusion_reasons"] for match in matches), rule["id"]
        negative = "Future work: " + positive
        assert all(match["exclusion_reasons"] for match in documentation_matches(negative, rule))


@pytest.mark.parametrize("stage", STAGES)
def test_contextual_recall_and_dimensions(tmp_path, stage):
    result = analyze(make_snapshot(tmp_path, CONTEXTUAL[stage], "README.md"), "documentation-only")
    assert stage in result["labels"]
    evidence = next(item for item in result["evidence"] if item["stage"] == stage)
    assert evidence["documentation_dimensions"]["scope"] == "repository"
    assert evidence["documentation_dimensions"]["polarity"] == "affirmative"


@pytest.mark.parametrize(
    "text",
    [
        "Install dependencies using pip to download experimental measurements.",
        "Another package downloads experimental measurements.",
        "We use another package to collect raw research data.",
        "We cite ExampleTool which cleans research datasets.",
        "This repository does not preprocess research data.",
        "# Roadmap\n## Planned functionality\nThis package downloads experimental measurements.",
        "Related work\n------------\nThis package downloads experimental measurements.",
        "We plan to add evaluation metrics for research outputs against reference data.",
        "This package exists. OtherTool downloads experimental measurements.",
        "<!-- This package downloads experimental measurements. -->",
        "- OtherTool downloads experimental measurements\n- We provide software documentation",
    ],
)
def test_scope_polarity_and_generic_exclusions(tmp_path, text):
    assert analyze(make_snapshot(tmp_path, text, "README.md"), "documentation-only")["labels"] == []


def test_wrapped_prose_exact_original_lines(tmp_path):
    text = "# Features\n\nThis package downloads\nexperimental measurements.\n"
    result = analyze(make_snapshot(tmp_path, text, "README.md"), "documentation-only")
    assert result["labels"] == ["Collection"]
    evidence = result["evidence"][0]
    assert (evidence["start_line"], evidence["end_line"]) == (3, 4)
    assert evidence["excerpt"] == "This package downloads\nexperimental measurements."


def test_workflow_documentation_isolated_from_code(tmp_path):
    text = "# Tutorial\nTo clean research datasets, run this command:\n\n```bash\nmapper preprocess --input observations.csv\n```\n"
    snapshot = make_snapshot(tmp_path, text, "tutorial.md")
    documentation = analyze(snapshot, "documentation-only")
    assert documentation["labels"] == ["Processing"]
    assert documentation["evidence"][0]["documentation_dimensions"]["layer"] == "workflow"
    assert analyze(snapshot, "code-only")["labels"] == []


@pytest.mark.parametrize("stage", STAGES)
def test_secondary_code_rules_individual_negative_context(tmp_path, stage):
    rules, _ = load_rules()
    rule = next(r for r in rules if r["stage"] == stage and r["source"] == "code")
    calls = {
        "Collection": "requests.get('health')",
        "Processing": "data.dropna()",
        "Method": "minimize(objective)",
        "Experimentation": "None",
        "Evaluation": "f1_score(ground_truth, predictions)",
        "Dissemination": "zenodo.deposit(data)",
    }
    text = "def generic_software_function():\n    return " + calls[stage] + "\n"
    result = analyze(make_snapshot(tmp_path, text), "code-only")
    # A named F1 calculation on ground truth and predictions is direct evaluation
    # evidence under V3, even when the enclosing function has a generic name.
    assert (stage in result["labels"]) == (stage == "Evaluation")
    assert all(item["rule_id"] != rule["id"] for item in result["evidence"])
