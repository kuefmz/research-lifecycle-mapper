import json
from pathlib import Path

import pytest

from lifecycle_mapper import STAGES
from lifecycle_mapper.acquisition import replay
from lifecycle_mapper.analysis import analyze, default_rules, load_rules
from lifecycle_mapper.canonical import sha256, write_json

BASE = Path(__file__).resolve().parents[1] / "benchmark/synthetic/snapshots"


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize(
    "source,mode", [("docs-positive", "documentation-only"), ("code-positive", "code-only")]
)
def test_each_stage_positive(stage, source, mode):
    result = analyze(BASE / source, mode)
    assert stage in result["labels"]
    assert any(record["stage"] == stage for record in result["evidence"])


@pytest.mark.parametrize("source", ["generic-negative", "excluded-negative"])
@pytest.mark.parametrize("mode", ["documentation-only", "code-only", "combined"])
def test_generic_and_excluded_negatives(source, mode):
    result = analyze(BASE / source, mode)
    assert result["labels"] == []
    if source == "excluded-negative":
        assert result["excluded_evidence"]


def test_mode_isolation_and_union():
    assert analyze(BASE / "docs-positive", "code-only")["labels"] == []
    assert analyze(BASE / "code-positive", "documentation-only")["labels"] == []
    for name in ["docs-positive", "code-positive", "excluded-negative"]:
        documentation = analyze(BASE / name, "documentation-only")
        code = analyze(BASE / name, "code-only")
        combined = analyze(BASE / name, "combined")
        assert set(combined["labels"]) == set(documentation["labels"]) | set(code["labels"])
        assert all(item["source"] == "documentation" for item in documentation["evidence"])
        assert all(item["source"] == "code" for item in code["evidence"])


def test_exact_line_ranges_and_commit_links():
    result = analyze(BASE / "docs-positive", "combined")
    assert set(item["stage"] for item in result["evidence"]) == set(STAGES)
    for item in result["evidence"]:
        index = STAGES.index(item["stage"]) + 1
        assert item["start_line"] == item["end_line"] == index
        assert f"/blob/{result['commit']}/README.md#L{index}-L{index}" in item["url"]


def test_incomplete_repository_modes():
    assert not analyze(BASE / "incomplete", "documentation-only")["scan_complete"]
    assert analyze(BASE / "incomplete", "code-only")["scan_complete"]
    assert not analyze(BASE / "incomplete", "combined")["scan_complete"]


def test_catalog_packaging_and_stability():
    root = Path(__file__).resolve().parents[1] / "rules"
    for path in root.glob("*.yaml"):
        assert path.read_bytes() == (default_rules() / path.name).read_bytes()
    one, first = load_rules(root)
    two, second = load_rules()
    assert first == second and one == two
    assert len(one) == 42
    assert all(rule["status"] == "unadjudicated-candidate" for rule in one)


def make_snapshot(tmp_path, text, path="src/activity.py"):
    manifest, _ = replay(BASE / "code-positive")
    source = "documentation" if path.endswith(".md") else "code"
    manifest["files"] = [
        {
            "path": path,
            "size": len(text.encode()),
            "source": source,
            "mode": "100644",
            "git_blob_sha": None,
            "status": "captured",
            "reason": None,
            "sha256": sha256(text.encode()),
        }
    ]
    target = tmp_path / "content" / path
    target.parent.mkdir(parents=True)
    target.write_text(text)
    write_json(tmp_path / "manifest.json", manifest)
    return tmp_path


def test_comments_docstrings_and_adjacent_functions_do_not_trigger(tmp_path):
    text = '''# def collect_research_data():
#     return requests.get("data")
"""def collect_research_data():
    return requests.get("data")"""
def collect_research_data():
    pass
def unrelated_health_check():
    return requests.get("health")
'''
    assert analyze(make_snapshot(tmp_path, text), "code-only")["labels"] == []


def test_multilabel_code_and_evidence_line_span(tmp_path):
    text = """def collect_research_data():
    return requests.get("data")
def clean_research_dataset(data):
    return data.dropna()
"""
    result = analyze(make_snapshot(tmp_path, text), "code-only")
    assert result["labels"] == ["Collection", "Processing"]
    assert [(item["start_line"], item["end_line"]) for item in result["evidence"]] == [
        (1, 2),
        (3, 4),
    ]


def test_malformed_python_is_analysis_failure(tmp_path):
    result = analyze(make_snapshot(tmp_path, "def broken(:\n"), "code-only")
    assert not result["scan_complete"]
    assert result["analysis_errors"] == [
        {"path": "src/activity.py", "reason": "python-parse-error"}
    ]


def test_bad_rule_catalog(tmp_path):
    for path in default_rules().glob("*.yaml"):
        data = json.loads(path.read_bytes())
        data["rules"][0]["positive"] = ["keyword"]
        (tmp_path / path.name).write_text(json.dumps(data))
    with pytest.raises(ValueError, match="conjunctive"):
        load_rules(tmp_path)


@pytest.mark.parametrize(
    "text",
    [
        "We don't collect raw research data.\n",
        "We never collect raw research data.\n",
        "We do not collect raw research data.\n",
        "We collect raw research data as an example only.\n",
    ],
)
def test_negated_documentation_is_excluded(tmp_path, text):
    result = analyze(make_snapshot(tmp_path, text, "README.md"), "documentation-only")
    assert result["labels"] == []
    assert result["excluded_evidence"]


def test_string_assigned_code_example_does_not_trigger(tmp_path):
    text = '''example = """\n+def collect_research_data():
    return requests.get("data")
"""\n+'''
    assert analyze(make_snapshot(tmp_path, text), "code-only")["labels"] == []
