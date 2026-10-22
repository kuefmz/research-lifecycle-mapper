from pathlib import Path

import pytest

from lifecycle_mapper.acquisition import POLICY_VERSION, source_kind
from lifecycle_mapper.analysis import analyze, analyze_modes
from lifecycle_mapper.canonical import read_json, write_json
from lifecycle_mapper.portable_code import token_view
from lifecycle_mapper.source_languages import CATALOG, language_names
from test_rules import make_snapshot

PROFILE = (
    Path(__file__).resolve().parents[1]
    / "tests/fixtures/legacy-profiles/multilanguage-development-v5.1"
)


def portable_snapshot(tmp_path, text, path):
    snapshot = make_snapshot(tmp_path, text, path)
    manifest = read_json(snapshot / "manifest.json")
    manifest["policy_version"] = POLICY_VERSION
    write_json(snapshot / "manifest.json", manifest)
    return snapshot


@pytest.mark.parametrize(
    "suffix,text",
    [
        (".js", "function run(){ model.fit(features,labels); }"),
        (".go", "func run(){ model.fit(features,labels); }"),
        (".c", "void run(){ fit(model,features,labels); }"),
        (".java", "void run(){ model.fit(features,labels); }"),
        (".py", "model.fit(features, labels)\n"),
        (".rb", "model.fit(features,labels)\n"),
        (".pl", "$model->fit($features,$labels);"),
        (".php", "<?php $model->fit($features,$labels); ?>"),
        (".erl", "run() -> model:fit(features,labels)."),
        (".ex", "model = fit(model, features, labels)"),
        (".hs", "results = fit model features"),
        (".f90", "call fit(model, features, labels)\n"),
        (".groovy", "def run(){ model.fit(features,labels); }"),
        (".kt", "fun run(){ model.fit(features,labels); }"),
        (".swift", "func run(){ model.fit(features,labels); }"),
        (".cs", "void Run(){ model.fit(features,labels); }"),
        (".rs", "fn run(){ model.fit(features,labels); }"),
        (".scala", "def run() = { model.fit(features,labels); }"),
        (".r", "results <- fit(model, features, labels)\n"),
        (".jl", "model = fit(model, features, labels)\n"),
    ],
)
def test_languages_are_included_and_scanned_without_native_parser(tmp_path, suffix, text):
    path = "src/activity" + suffix
    assert source_kind(path)[0] == "code"
    result = analyze(portable_snapshot(tmp_path, text, path), "code-only", rules_dir=PROFILE)
    assert result["scan_complete"]
    assert "Method" in result["labels"]
    assert result["source_scans"]
    assert not any(e["reason"] == "unsupported-source-language" for e in result["analysis_errors"])


@pytest.mark.parametrize(
    "suffix,text",
    [
        (".hs", '-- model.fit(features,labels)\nmessage = "model.fit(features,labels)"'),
        (".rb", "# model.fit(features,labels)\nmessage = 'model.fit(features,labels)'"),
        (".f90", "! model.fit(features,labels)\nmessage = 'model.fit(features,labels)'"),
        (".erl", '% model:fit(features,labels).\nmessage() -> "model.fit(features,labels)".'),
        (".groovy", "/* model.fit(features,labels) */\ndef s='model.fit(features,labels)'"),
    ],
)
def test_comments_and_literals_do_not_become_activity(tmp_path, suffix, text):
    result = analyze(
        portable_snapshot(tmp_path, text, "src/f" + suffix), "code-only", rules_dir=PROFILE
    )
    assert result["labels"] == []


def test_missing_lexer_uses_explicit_conservative_policy(monkeypatch):
    import lifecycle_mapper.portable_code as module
    from pygments.util import ClassNotFound

    def missing(*args):
        raise ClassNotFound("no lexer")

    monkeypatch.setattr(module, "get_lexer_for_filename", missing)
    view, info = token_view("model.fit(features, labels) # scientific comment", "f.hs")
    assert info["policy"] == "conservative-token-fallback-v1"
    assert "model.fit" in view and "scientific comment" not in view


@pytest.mark.parametrize(
    "suffix", [".ttl", ".rdf", ".owl", ".csv", ".tsv", ".json", ".parquet", ".npy"]
)
def test_data_overrides_any_language_extension_collision(suffix):
    assert source_kind("data/payload" + suffix)[0] is None
    assert language_names("data/payload" + suffix) == []


def test_catalog_is_pinned_and_old_snapshots_keep_old_eligibility():
    assert len(CATALOG["languages"]) == 562
    assert len(CATALOG["commit"]) == 40
    assert source_kind("src/f.erl")[0] == "code"
    assert source_kind("src/f.erl", "eligibility-2-notebook-cells")[0] is None


def test_portable_does_not_scan_documentation_as_code(tmp_path):
    snapshot = portable_snapshot(tmp_path, "model.fit(features, labels)", "README.md")
    result = analyze(snapshot, "combined", rules_dir=PROFILE)
    assert result["source_scans"] == []
    assert all(e["source"] == "documentation" for e in result["evidence"])


def test_native_parser_failure_is_explicit_lexical_fallback(tmp_path):
    snapshot = portable_snapshot(
        tmp_path, "model.fit(features,labels)\ninvalid syntax???\n", "src/f.py"
    )
    result = analyze(snapshot, "code-only", rules_dir=PROFILE)
    assert result["scan_complete"]
    assert "Method" in result["labels"]
    assert any(w["reason"] == "python-parse-error" for w in result["source_warnings"])
    assert result["source_scans"][0]["policy"] == "pygments-lexical-v1"


def test_projection_matches_independent_modes_with_fallback(tmp_path):
    snapshot = portable_snapshot(tmp_path, "results = fit model features", "src/f.hs")
    modes = ("documentation-only", "code-only", "combined")
    assert analyze_modes(snapshot, modes, rules_dir=PROFILE) == [
        analyze(snapshot, mode, rules_dir=PROFILE) for mode in modes
    ]


@pytest.mark.parametrize("language", ["javascript", "Go", "Java", "Haskell", "custom-kernel"])
def test_notebook_code_languages_are_scanned_with_markdown_separate(tmp_path, language):
    from test_notebooks import snapshot

    root = snapshot(
        tmp_path,
        [
            {"cell_type": "markdown", "source": "We collect raw research data from sensors."},
            {"cell_type": "code", "source": "model.fit(features,labels)"},
        ],
        language,
    )
    docs = analyze(root, "documentation-only", rules_dir=PROFILE)
    code = analyze(root, "code-only", rules_dir=PROFILE)
    assert docs["scan_complete"] and code["scan_complete"]
    assert "Collection" in docs["labels"]
    assert "Method" in code["labels"]
    assert all(e["notebook_cell"] == 2 for e in code["evidence"])
