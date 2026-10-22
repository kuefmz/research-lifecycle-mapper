from pathlib import Path

import pytest

from lifecycle_mapper.analysis import analyze, implementation_view, load_rules
from lifecycle_mapper.brace_code import executable_blocks
from test_rules import make_snapshot

RULES = (
    Path(__file__).resolve().parents[1]
    / "tests/fixtures/legacy-profiles/multilanguage-development-v5.1"
)


@pytest.mark.parametrize(
    "stage,rule,text",
    [
        ("Collection", "ACQUIRE", "void run(){ dataset = fetch(datasetUrl); }"),
        ("Processing", "TRANSFORM", "void run(){ features = normalize(data); }"),
        ("Method", "MODEL_CALL", "void run(){ model.fit(features, labels); }"),
        (
            "Method",
            "NAMED_COMPUTATION",
            "double cosineSimilarity(double x,double y){double result=x*y; return result;}",
        ),
        (
            "Experimentation",
            "TRIALS",
            "void run(){ for(int seed=0;seed<n_trials;seed++){results.push_back(runTrial(seed));} }",
        ),
        ("Evaluation", "METRIC_CALL", "void run(){ score=f1Score(labels,predictions); }"),
        ("Evaluation", "METRIC_ARITHMETIC", "void run(){ precision=tp/(tp+fp); }"),
        ("Dissemination", "EXPORT", "void run(){ saveFigure(figure,results); }"),
        ("Dissemination", "DEPOSIT", "void run(){ repository.publish(researchOutputs); }"),
    ],
)
def test_documented_brace_rules_require_executable_evidence(tmp_path, stage, rule, text):
    result = analyze(
        make_snapshot(tmp_path, text, "src/activity.cpp"), "code-only", rules_dir=RULES
    )
    assert result["scan_complete"]
    assert stage in result["labels"]
    matched = [
        a
        for e in result["evidence"]
        for a in e["matched_rules"]
        if "_BRACE_" in a["id"] and a["id"].endswith(rule + "_V51")
    ]
    assert matched
    assert matched[0]["code_syntax_policy"] == "brace-lexical-v1"
    assert matched[0]["code_context"]


@pytest.mark.parametrize(
    "text",
    [
        "void run(){ /* model.fit(features,labels); */ }",
        'void run(){ auto s="model.fit(features,labels);"; }',
        'void run(){ auto s=R"raw(model.fit(features,labels); { })raw"; }',
        "void first(){ model.fit(); } void second(){ features = labels; }",
        "class Model { double fit(features,labels); };",
        "void run(){ double accuracy=0; }",
        "void run(){ /* precision=tp/(tp+fp); */ }",
    ],
)
def test_non_executable_and_unrelated_evidence_does_not_predict(tmp_path, text):
    result = analyze(
        make_snapshot(tmp_path, text, "src/activity.cpp"), "code-only", rules_dir=RULES
    )
    assert result["scan_complete"]
    assert result["labels"] == []


@pytest.mark.parametrize(
    "suffix,header",
    [
        (".cpp", "void run()"),
        (".c", "void run()"),
        (".h", "void run()"),
        (".hpp", "void run()"),
        (".cc", "void run()"),
        (".java", "public void run()"),
        (".js", "function run()"),
        (".ts", "function run()"),
        (".go", "func run()"),
        (".rs", "fn run()"),
        (".scala", "def run() ="),
    ],
)
def test_recognized_brace_languages_use_explicit_lexical_policy(tmp_path, suffix, header):
    text = header + "{ model.fit(features,labels); }"
    result = analyze(
        make_snapshot(tmp_path, text, "src/activity" + suffix), "code-only", rules_dir=RULES
    )
    assert result["scan_complete"]
    assert "Method" in result["labels"]


@pytest.mark.parametrize(
    "suffix,text",
    [
        (".cpp", "void run(){"),
        (".cpp", 'void run(){auto s="unterminated;}'),
        (".js", "function run(){const s=`${model.fit(features,labels)}`;}"),
        (".js", "function run(){const re=/model.fit(features,labels)/;}"),
    ],
)
def test_native_syntax_gap_uses_labelled_lexical_fallback(tmp_path, suffix, text):
    result = analyze(
        make_snapshot(tmp_path, text, "src/activity" + suffix), "code-only", rules_dir=RULES
    )
    assert result["scan_complete"]
    assert result["analysis_errors"] == []
    assert result["source_warnings"][0]["reason"] == "brace-lexical-error"
    assert result["source_scans"][0]["policy"] == "pygments-lexical-v1"


def test_cpp_raw_literals_and_comments_preserve_offsets():
    text = 'void run(){\n/* } { */\n auto x=R"s({model.fit(features,labels);})s";\n}\n'
    view = implementation_view(text, "src/f.cpp")
    assert len(view) == len(text)
    assert view.count("\n") == text.count("\n")
    assert "model.fit" not in view
    assert executable_blocks(view)


def test_documentation_rules_are_identical_to_v5_and_modes_are_isolated(tmp_path):
    old, _ = load_rules(RULES.parent / "documentation-development-v5")
    new, _ = load_rules(RULES)
    assert [r for r in old if r["source"] == "documentation"] == [
        r for r in new if r["source"] == "documentation"
    ]
    assert len(new) == len(old) + 16
    snapshot = make_snapshot(tmp_path, "void run(){ model.fit(features,labels); }", "src/f.cpp")
    assert analyze(snapshot, "documentation-only", rules_dir=RULES)["labels"] == []
