import csv
from lifecycle_mapper import STAGES
from lifecycle_mapper.summarize import summarize


def test_metrics_exclude_partial_scans_and_resample_repositories(tmp_path):
    path = tmp_path / "comparison.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "repository",
                "stage",
                "human_documentation",
                "prediction",
                "scan_complete",
            ],
        )
        writer.writeheader()
        for repo, complete in [("a/b", True), ("c/d", False)]:
            writer.writerows(
                {
                    "repository": repo,
                    "stage": s,
                    "human_documentation": 1,
                    "prediction": 1,
                    "scan_complete": complete,
                }
                for s in STAGES
            )
    result = summarize(path, expected=3, bootstrap=10)
    assert result["repository_count"] == 1
    assert result["coverage"] == 1 / 3
    assert result["macro"]["f1"] == 1
    assert result["excluded_partial_or_unavailable"] == 2
    assert result["bootstrap"]["unit"] == "repository with all six labels"
    assert result == summarize(path, expected=3, bootstrap=10)


def test_no_complete_scans_are_reported_without_accuracy_claim(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("repository,stage,human_documentation,prediction,scan_complete\n")
    result = summarize(path, expected=100, bootstrap=2)
    assert result["repository_count"] == 0 and result["bootstrap"] is None
    assert "not estimable" in result["warning"]
