"""Scientific data integrity and independent reproduction of supplied benchmark tables."""

import csv
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "paper_reproduction", ROOT / "results/benchmark-100/reproduce_paper.py"
)
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


def test_ten_exact_rectangular_exports_and_anonymous_reviewers():
    tables, manifest = analysis.load_tables()
    assert len(tables) == 10
    assert not any(
        item["source_sheet"] in {"Hoja 14", "Hoja 15", "Hoja 16"} for item in manifest["sheets"]
    )
    source = list(csv.DictReader((ROOT / "data/annotations_independent.csv").open()))
    for row in source:
        for reviewer in ("reviewer1", "reviewer2"):
            assert tables[reviewer][row["repository"].casefold()][row["stage"]] == int(
                float(row[reviewer])
            )


def test_initial_agreement_and_final_consensus_are_separate():
    tables, _ = analysis.load_tables()
    result = analysis.annotation_statistics(tables)
    assert (result["agreement"], result["disagreement"]) == (354, 246)
    assert (result["final_positive_labels"], result["final_negative_labels"]) == (384, 216)
    assert result["all_six_positive_repositories"] == 12
    assert [row["agreement"] for row in result["per_stage"]] == [53, 55, 53, 72, 53, 68]


def test_llm_paper_cohorts_and_metrics_recomputed_from_csv():
    report = analysis.analyze()
    expected = {
        "llm_documentation": (98, 0.82878412),
        "llm_code": (63, 0.79061977),
        "llm_combined": (99, 0.79454927),
    }
    for role, (count, f1) in expected.items():
        result = report["workbook_metrics"][role]
        assert result["repository_count"] == count
        assert result["micro"]["f1"] == f1
    rounding = [
        row
        for row in report["paper_comparison"]
        if row["status"] == "rounding_difference" and row["table"] == "table_6"
    ]
    assert len(rounding) == 1 and rounding[0]["role"] == "llm_combined"
    assert rounding[0]["rounded_3dp"] == 0.795


def test_restored_csvs_use_original_scan_complete_cohorts():
    report = analysis.analyze()
    counts = [
        report["workbook_metrics"]["heuristics_" + mode]["repository_count"]
        for mode in ("documentation", "code", "combined")
    ]
    assert counts == [96, 95, 95]
    assert report["original_run_metrics"] is None and report["corpus_stage_counts"] is None
    assert not any(
        row["table"] == "table_4" and row["status"] != "matches"
        for row in report["paper_comparison"]
    )
    tables, _ = analysis.load_tables()
    assert any(
        value is None
        for row in tables["heuristics_documentation"].values()
        for value in row.values()
    )
    with pytest.raises(ValueError):
        analysis.binary("uncertain")
    assert analysis.binary("") is None and analysis.binary("Unverified") is None


def test_notebook_has_executed_python_cells_without_error_outputs():
    notebook = json.loads((ROOT / "results/benchmark-100/reproduce_paper.ipynb").read_text())
    cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert len(cells) == 6
    assert [cell["execution_count"] for cell in cells] == list(range(1, 7))
    for cell in cells:
        compile("".join(cell["source"]), "reproduce_paper.ipynb", "exec")
        assert not any(output["output_type"] == "error" for output in cell["outputs"])


def test_raw_run_completeness_excludes_partial_even_when_labels_are_binary(tmp_path):
    from lifecycle_mapper import MODES, STAGES
    from lifecycle_mapper.canonical import json_bytes
    import hashlib

    reference = {"a/complete": dict.fromkeys(STAGES, 1), "a/partial": dict.fromkeys(STAGES, 1)}
    for name, complete in (("complete", True), ("partial", False)):
        folder = tmp_path / "repositories" / name
        folder.mkdir(parents=True)
        payload = {
            "requested_url": "https://github.com/a/" + name,
            "modes": [
                {"mode": mode, "scan_complete": complete, "predictions": dict.fromkeys(STAGES, 1)}
                for mode in MODES
            ],
        }
        content = json_bytes(payload)
        (folder / "result.json").write_bytes(content)
        (folder / "result.sha256").write_text(hashlib.sha256(content).hexdigest())
    result = analysis.evaluate_original_run(tmp_path, reference)
    assert all(value["repository_count"] == 1 for value in result.values())
    assert all(value["micro"]["f1"] == 1 for value in result.values())
    (tmp_path / "repositories/partial/result.sha256").write_text("bad")
    with pytest.raises(AssertionError):
        analysis.evaluate_original_run(tmp_path, reference)


def test_restoration_preserves_all_known_labels_and_original_aggregate_metrics():
    import hashlib

    folder = ROOT / "results/benchmark-100/assessment"
    corrections = list(csv.DictReader((folder / "uncertainty_corrections.csv").open()))
    assert len(corrections) == 64
    assert sum(row["previous"] in ("0", "0.0") for row in corrections) == 58
    assert all(row["restored"] == "?" for row in corrections)
    tables, _ = analysis.load_tables()
    cohorts = analysis.assessment_cohorts(tables)
    report = analysis.analyze()
    modes = {"documentation-only": "documentation", "code-only": "code", "combined": "combined"}
    targets = list(csv.DictReader((folder / "mode_summary.csv").open()))
    for row in targets:
        result = report["workbook_metrics"]["heuristics_" + modes[row["mode"]]]
        assert result["repository_count"] == int(row["evaluated_repositories"])
        assert result["micro"]["f1"] == float(row["micro_f1"])
    # Completeness is independent of whether some positive evidence was already captured.
    assert any(
        repo not in cohorts[role] and 1 in labels.values()
        for role in cohorts
        for repo, labels in tables[role].items()
    )
    manifest = json.loads((folder / "manifest.json").read_text())
    assert all(
        hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
        for name, digest in manifest["files"].items()
    )
