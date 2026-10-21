import pytest

from lifecycle_mapper import MODES, STAGES
from lifecycle_mapper.assess import mode_metrics
from lifecycle_mapper.canonical import write_json, read_json
from lifecycle_mapper.openaire import file_hash
from lifecycle_mapper.paper_summary import build_summary


def fixture(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    assessment = tmp_path / "assessment"
    assessment.mkdir()
    write_json(
        run / "manifest.json",
        {
            "configuration": {
                "repository_count": 2,
                "repository_timeout_seconds": 120,
                "max_bytes": 10485760,
            }
        },
    )
    write_json(
        run / "summary.json",
        {
            "repository_count": 2,
            "finished": 2,
            "complete": 1,
            "partial": 0,
            "failed": 1,
            "timed_out": 1,
            "session_wall_seconds": 125,
            "session_api_network_calls": 6,
            "all_repositories_accounted_for": True,
        },
    )
    gold = {stage: int(stage == "Method") for stage in STAGES}
    row = {"gold": gold, "prediction": {stage: stage == "Method" for stage in STAGES}}
    metrics = mode_metrics([row], 2)
    report = {
        "expected_repositories": 2,
        "source_run_manifest_sha256": file_hash(run / "manifest.json"),
        "reference_sha256": "r" * 64,
        "rule_catalog_hashes": ["c" * 64],
        "per_mode": {mode: {"all": metrics} for mode in MODES},
        "common_complete_cohort": {mode: metrics for mode in MODES},
    }
    write_json(assessment / "all_modes_metrics.json", report)
    return run, assessment


def test_printed_report_uses_complete_denominator_and_retains_provenance(tmp_path):
    run, assessment = fixture(tmp_path)
    text = build_summary(run, assessment, tmp_path / "paper")
    assert "Attempted 2/2; complete 1; partial 0; failed 1; timed out 1." in text
    assert "| documentation-only | 1/2 | 1.000 | 1.000 | 1.000" in text
    assert "Always-positive" in text
    assert "development-set results" in text
    assert "no untouched-holdout" in text.lower()
    assert (tmp_path / "paper/paper_modes.tex").read_text().count(r"\\") == 4
    saved = read_json(tmp_path / "paper/paper_summary.json")
    assert saved["per_mode_complete"]["documentation-only"]["repository_count"] == 1
    assert saved["source_assessment_sha256"] == file_hash(assessment / "all_modes_metrics.json")


def test_summary_rejects_stale_assessment(tmp_path):
    run, assessment = fixture(tmp_path)
    write_json(run / "manifest.json", {"configuration": {"repository_count": 3}})
    with pytest.raises(ValueError, match="does not match"):
        build_summary(run, assessment, tmp_path / "paper")


def test_summary_rejects_unfinished_run(tmp_path):
    run, assessment = fixture(tmp_path)
    summary = read_json(run / "summary.json")
    summary["finished"] = 1
    write_json(run / "summary.json", summary)
    with pytest.raises(ValueError, match="attempts to finish"):
        build_summary(run, assessment, tmp_path / "paper")


def test_no_complete_scans_prints_not_estimable(tmp_path):
    run, assessment = fixture(tmp_path)
    report = read_json(assessment / "all_modes_metrics.json")
    empty = mode_metrics([], 2)
    report["per_mode"] = {mode: {"all": empty} for mode in MODES}
    report["common_complete_cohort"] = {mode: empty for mode in MODES}
    write_json(assessment / "all_modes_metrics.json", report)
    text = build_summary(run, assessment, tmp_path / "paper")
    assert "| documentation-only | 0/2 | n/a | n/a | n/a" in text


def test_paper_summary_rejects_replayed_metrics(tmp_path):
    run, assessment = fixture(tmp_path)
    report = read_json(assessment / "all_modes_metrics.json")
    report["replayed_offline"] = True
    write_json(assessment / "all_modes_metrics.json", report)
    with pytest.raises(ValueError, match="not an offline replay"):
        build_summary(run, assessment, tmp_path / "paper")
