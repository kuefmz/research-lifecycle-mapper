import json
from pathlib import Path

import pytest

from lifecycle_mapper.acquisition import POLICY_VERSION, replay
from lifecycle_mapper.analysis import analyze, analyze_modes
from lifecycle_mapper.canonical import sha256, write_json

BASE = Path(__file__).resolve().parents[1] / "benchmark/synthetic/snapshots"


def snapshot(tmp_path, cells, language="python"):
    manifest, _ = replay(BASE / "docs-positive")
    text = json.dumps(
        {"nbformat": 4, "metadata": {"language_info": {"name": language}}, "cells": cells}
    )
    manifest["policy_version"] = POLICY_VERSION
    manifest["files"] = [
        {
            "path": "study.ipynb",
            "source": "notebook",
            "status": "captured",
            "reason": None,
            "mode": "100644",
            "size": len(text.encode()),
            "sha256": sha256(text.encode()),
            "git_blob_sha": None,
        }
    ]
    (tmp_path / "content").mkdir()
    (tmp_path / "content/study.ipynb").write_text(text)
    write_json(tmp_path / "manifest.json", manifest)
    return tmp_path


def test_cells_are_isolated_and_outputs_raw_metadata_are_ignored(tmp_path):
    code = (
        "def evaluate_research_predictions():\n    return f1_score(reference_labels, predictions)\n"
    )
    path = snapshot(
        tmp_path,
        [
            {"cell_type": "markdown", "source": ["We collect raw research data from sensors.\n"]},
            {
                "cell_type": "code",
                "source": code,
                "outputs": [{"text": "We run controlled experiments."}],
            },
            {"cell_type": "raw", "source": "We run controlled experiments."},
        ],
    )
    modes = ("documentation-only", "code-only", "combined")
    direct = [analyze(path, mode) for mode in modes]
    together = analyze_modes(path, modes)
    assert direct[0]["labels"] == ["Collection"]
    assert direct[1]["labels"] == ["Evaluation"]
    assert set(direct[2]["labels"]) == {"Collection", "Evaluation"}
    for one, batch in zip(direct, together):
        assert one["predictions"] == batch["predictions"]
        assert one["evidence"] == batch["evidence"]
        assert one["scan_complete"] == batch["scan_complete"]
    for item in direct[2]["evidence"]:
        assert item["path"] == "study.ipynb"
        assert item["notebook_cell"] in {1, 2}
        assert item["line_scope"] == "notebook-cell"
        assert "#L" not in item["url"]


def test_conditions_do_not_join_across_cells(tmp_path):
    path = snapshot(
        tmp_path,
        [
            {"cell_type": "markdown", "source": "We collect."},
            {"cell_type": "markdown", "source": "Raw research data."},
        ],
    )
    assert analyze(path, "documentation-only")["labels"] == []


@pytest.mark.parametrize("language,code", [("unknown", "x = 1"), ("python", "%timeit x()")])
def test_unsupported_code_does_not_hide_complete_markdown(tmp_path, language, code):
    path = snapshot(
        tmp_path,
        [
            {"cell_type": "markdown", "source": "We collect raw research data."},
            {"cell_type": "code", "source": code},
        ],
        language,
    )
    for result in [
        analyze(path, "documentation-only"),
        analyze_modes(path, ("documentation-only", "code-only"))[0],
    ]:
        assert result["scan_complete"]
    assert not analyze(path, "code-only")["scan_complete"]


def test_corrupt_notebook_is_incomplete_in_both_modes(tmp_path):
    path = snapshot(tmp_path, [{"cell_type": "code", "source": 42}])
    assert not analyze(path, "documentation-only")["scan_complete"]
    assert not analyze(path, "code-only")["scan_complete"]


def test_duplicate_cell_evidence_keeps_distinct_ids(tmp_path):
    cell = {"cell_type": "markdown", "source": "We collect raw research data."}
    path = snapshot(tmp_path, [cell, cell])
    evidence = analyze(path, "documentation-only")["evidence"]
    assert {e["notebook_cell"] for e in evidence} == {1, 2}
    assert len({e["evidence_id"] for e in evidence}) == len(evidence)


def test_plotting_magic_is_masked_without_shifting_source_lines(tmp_path):
    path = snapshot(
        tmp_path,
        [
            {
                "cell_type": "code",
                "source": "%matplotlib inline\ndef evaluate_research_predictions():\n    return f1_score(reference_labels, predictions)\n",
            }
        ],
    )
    result = analyze(path, "code-only")
    assert result["scan_complete"]
    assert result["labels"] == ["Evaluation"]
    assert result["evidence"][0]["start_line"] == 2
