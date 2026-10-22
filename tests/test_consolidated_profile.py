from pathlib import Path

import pytest

from lifecycle_mapper.acquisition import source_kind
from lifecycle_mapper.analysis import analyze
from lifecycle_mapper.portable_code import token_view
from test_portable_code import portable_snapshot
from test_rules import make_snapshot

PROFILE = Path(__file__).resolve().parents[1] / "configs/heuristics"


@pytest.mark.parametrize(
    "path,reason",
    [
        ("web/js/jquery-3.2.1.min.js", "generated-minified-asset-or-source-map"),
        ("inst/www/d3.min.js", "generated-minified-asset-or-source-map"),
        ("web/app.min.css.map", "generated-minified-asset-or-source-map"),
        ("assets/app.js.map", "generated-minified-asset-or-source-map"),
        ("other_data/py27/package/data_val.f", "parallel-corpus-artifact"),
        ("polyglot_data/train/polyglot_seg.e", "parallel-corpus-artifact"),
    ],
)
def test_generated_and_corpus_artifacts_are_excluded_before_download(path, reason):
    assert source_kind(path) == (None, reason)
    assert source_kind(path, "eligibility-5-legacy-text-decoding")[1] != reason


@pytest.mark.parametrize(
    "path", ["src/solver.f", "src/agent.js", "data/solver.f", "src/data_val.f"]
)
def test_ordinary_fortran_and_javascript_remain_source(path):
    assert source_kind(path)[0] == "code"


@pytest.mark.parametrize(
    "path,text,stage",
    [
        ("simulate.m", "[T,Y]=ode15s(@model,t,y0,options);", "Method"),
        ("simulate.m", "[T,Y]=ode15s(@model,t,y0,options);", "Experimentation"),
        ("fit.py", "import sklearn\nmodel.fit(X, y)\n", "Method"),
        ("analysis.R", "pvalue <- t.test(groupA,groupB)", "Evaluation"),
        ("analysis.py", "scores = cross_val_score(estimator, X, y)", "Evaluation"),
        ("model.py", "weights = np.linalg.solve(covariance, targets)", "Method"),
    ],
)
def test_scientific_operations_without_prescribed_variable_names(tmp_path, path, text, stage):
    result = analyze(portable_snapshot(tmp_path, text, path), "code-only", rules_dir=PROFILE)
    assert stage in result["labels"]


@pytest.mark.parametrize(
    "text,expected,absent",
    [
        (
            "This repository contains an implementation of a neural dependency parser. Run bash train_and_test.sh on training and validation files.",
            {"Method"},
            set(),
        ),
        (
            "This repository contains two versions of mathematical models simulating cell reactions.",
            {"Method"},
            set(),
        ),
        ("Our experiments achieve accuracy of 77% against the baseline.", {"Evaluation"}, set()),
        (
            "Download an existing dataset and convert its format before running the experiments.",
            set(),
            {"Collection"},
        ),
        (
            "The software can model systems from which we could collect noisy observations.",
            set(),
            {"Collection"},
        ),
        ("This repository contains code for the experiments in a paper.", set(), {"Method"}),
    ],
)
def test_documentation_role_and_scope_regressions(tmp_path, text, expected, absent):
    result = analyze(
        make_snapshot(tmp_path, text, "README.md"), "documentation-only", rules_dir=PROFILE
    )
    assert expected <= set(result["labels"])
    assert not absent.intersection(result["labels"])


def test_wolfram_masking_and_box_coverage_are_explicit(tmp_path):
    text = '(* NDSolve[model,t,y0] (* nested *) *)\nlabel="NDSolve[model,t,y0]";\nresult=NDSolve[model,t,y0];'
    view, info = token_view(text, "model.wl")
    assert view.count("NDSolve") == 1
    assert len(view) == len(text)
    assert view.count("\n") == text.count("\n")
    assert info["policy"] == "wolfram-linear-v1"
    result = analyze(
        portable_snapshot(
            tmp_path, 'Notebook[{Cell[BoxData[RowBox[{"NDSolve","[","model","]"}]]]]}]', "model.nb"
        ),
        "code-only",
        rules_dir=PROFILE,
    )
    assert not result["scan_complete"]
    assert any(
        e["reason"] == "serialized-notebook-box-code-unparsed" for e in result["analysis_errors"]
    )


def test_generated_asset_is_never_fetched(tmp_path, monkeypatch):
    import base64
    from lifecycle_mapper.acquisition import acquire, replay

    calls = []
    content = b"Research documentation.\n"

    def api(endpoint):
        if "/branches/main" in endpoint:
            return {
                "commit": {
                    "sha": "a" * 40,
                    "commit": {"tree": {"sha": "b" * 40}},
                    "html_url": "https://github.com/a/b/commit/" + "a" * 40,
                }
            }
        if "/git/trees/" in endpoint:
            return {
                "tree": [
                    {
                        "path": "README.md",
                        "type": "blob",
                        "mode": "100644",
                        "sha": "c" * 40,
                        "size": len(content),
                    },
                    {
                        "path": "web/jquery.min.js",
                        "type": "blob",
                        "mode": "100644",
                        "sha": "d" * 40,
                        "size": 1000000,
                    },
                ],
                "truncated": False,
            }
        calls.append(endpoint)
        assert endpoint.endswith("c" * 40)
        return {"encoding": "base64", "content": base64.b64encode(content).decode()}

    snapshot = tmp_path / "snapshot"
    manifest = acquire("https://github.com/a/b", snapshot, api_client=api)
    assert len(calls) == 1
    assert manifest["files"][1]["reason"] == "generated-minified-asset-or-source-map"
    assert set(replay(snapshot)[1]) == {"README.md"}


def test_unreadable_notebook_has_file_diagnostics(tmp_path):
    import json
    from lifecycle_mapper.analysis import analyze_modes
    from lifecycle_mapper.canonical import read_json, write_json

    snapshot = portable_snapshot(
        tmp_path, json.dumps({"nbformat": 3, "cells": []}), "analysis.ipynb"
    )
    manifest = read_json(snapshot / "manifest.json")
    manifest["files"][0]["source"] = "notebook"
    write_json(snapshot / "manifest.json", manifest)
    for result in analyze_modes(
        snapshot, ("documentation-only", "code-only", "combined"), rules_dir=PROFILE
    ):
        assert not result["scan_complete"]
        assert any(item["reason"] == "notebook-parse-error" for item in result["coverage_issues"])


@pytest.mark.parametrize(
    "path,reason",
    [
        ("experiment/js/jquery.js", "bundled-jquery-dependency"),
        ("web/jquery-3.2.1.js", "bundled-jquery-dependency"),
        ("client/test_data.py", "software-test-path"),
        ("src/tests/helper.py", "software-test-path"),
        ("experimental_data/results/result.txt", "data-directory-text-artifact"),
    ],
)
def test_full_run_failure_artifact_exclusions(path, reason):
    assert source_kind(path) == (None, reason)
    assert source_kind(path, "eligibility-6-generated-corpus-exclusions")[1] != reason


def test_data_readme_and_readable_research_code_stay_eligible():
    assert source_kind("data/README.txt")[0] == "documentation"
    assert source_kind("src/experiment.js")[0] == "code"
    assert source_kind("notes/protocol.txt")[0] == "documentation"
