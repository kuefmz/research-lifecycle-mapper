import json
from pathlib import Path

import pytest

from lifecycle_mapper import MODES, STAGES
from lifecycle_mapper.analysis import analyze, analyze_modes, load_rules
from lifecycle_mapper.assess import assess
from lifecycle_mapper.canonical import write_json
from lifecycle_mapper.openaire import file_hash
from test_rules import make_snapshot

CANDIDATE = Path(__file__).resolve().parents[1] / "configs/documentation-candidate-v4"
EXAMPLES = {
    "Collection": "This repository generates synthetic datasets.",
    "Processing": "This package augments training data.",
    "Method": "This library fits statistical models.",
    "Experimentation": "This repository conducts ablation studies.",
    "Evaluation": "This tool computes classification accuracy.",
    "Dissemination": "This code generates plots of experimental results.",
}


@pytest.mark.parametrize("stage", STAGES)
def test_candidate_general_wording_and_source_isolation(tmp_path, stage):
    rules, _ = load_rules(CANDIDATE)
    assert len(rules) == 48
    snapshot = make_snapshot(tmp_path, EXAMPLES[stage], "README.md")
    assert stage in analyze(snapshot, "documentation-only", rules_dir=CANDIDATE)["labels"]
    assert analyze(snapshot, "code-only", rules_dir=CANDIDATE)["labels"] == []
    for prefix in ("Future work: ", "This repository does not support this feature. Future work: "):
        from lifecycle_mapper.documentation import documentation_matches

        rule = next(r for r in rules if r["stage"] == stage and r["id"].endswith("EXTENDED_V4"))
        assert not any(
            not r["exclusion_reasons"]
            for r in documentation_matches(prefix + EXAMPLES[stage], rule)
        )


def test_candidate_does_not_promote_third_party_or_installation(tmp_path):
    from lifecycle_mapper.documentation import documentation_matches

    rules, _ = load_rules(CANDIDATE)
    for stage, text in EXAMPLES.items():
        rule = next(r for r in rules if r["stage"] == stage and r["id"].endswith("EXTENDED_V4"))
        for negative in (
            text.replace("This repository", "Another repository")
            .replace("This package", "Another package")
            .replace("This library", "Another library")
            .replace("This tool", "Another tool")
            .replace("This code", "External software"),
            "# Installation\n" + text,
            "We use another package to " + text.lower(),
        ):
            assert not any(
                not r["exclusion_reasons"] for r in documentation_matches(negative, rule)
            )


def test_assessment_separates_modes_and_replays_without_network(tmp_path, monkeypatch):
    from lifecycle_mapper import acquisition

    run = tmp_path / "run"
    folder = run / "repositories/key"
    folder.mkdir(parents=True)
    snapshot = make_snapshot(folder / "snapshot", EXAMPLES["Method"], "README.md")
    manifest_hash = file_hash(snapshot / "manifest.json")
    original = analyze_modes(snapshot, MODES, expected_hash=manifest_hash)
    result = {
        "requested_url": "https://github.com/a/b",
        "commit": "abc",
        "snapshot": "repositories/key/snapshot",
        "snapshot_sha256": manifest_hash,
        "modes": original,
    }
    write_json(folder / "result.json", result)
    (folder / "result.sha256").write_text(file_hash(folder / "result.json"))
    write_json(run / "manifest.json", {"configuration": {"repository_count": 1}})
    reference = tmp_path / "reference.json"
    write_json(
        reference,
        {
            "kind": "lifecycle-benchmark-dataset",
            "schema_version": 1,
            "stages": list(STAGES),
            "repositories": [
                {
                    "source_url": "https://github.com/a/b",
                    "human_labels": {s: int(s == "Method") for s in STAGES},
                    "results": {},
                }
            ],
            "runs": [],
        },
    )

    def blocked(*args, **kwargs):
        raise AssertionError("Network must not be used")

    monkeypatch.setattr(acquisition, "api_get", blocked)
    before = file_hash(folder / "result.json")
    report = assess(run, reference, tmp_path / "assessment", True, CANDIDATE)
    assert report["common_complete_repositories"] == 1
    rows = {r["mode"]: r for r in report["modes"]}
    assert rows["documentation-only"]["label_accuracy"] == 1
    assert rows["code-only"]["label_accuracy"] == 5 / 6
    assert rows["combined"]["label_accuracy"] == 1
    assert file_hash(folder / "result.json") == before
    saved = json.loads((tmp_path / "assessment/all_modes_metrics.json").read_text())
    assert saved["replayed_offline"] is True
    assert saved["per_mode"]["documentation-only"]["operational_holdout"]["repository_count"] == 1
    assert "cross-scope" in rows["code-only"]["interpretation"]
    assert (tmp_path / "assessment/documentation_errors_development.csv").is_file()
    with pytest.raises(ValueError, match="new assessment"):
        assess(run, reference, tmp_path / "assessment")


def test_assessment_keeps_missing_repositories_unknown(tmp_path):
    run = tmp_path / "empty-run"
    run.mkdir()
    write_json(run / "manifest.json", {"configuration": {"repository_count": 2}})
    reference = tmp_path / "reference.json"
    write_json(
        reference,
        {
            "kind": "lifecycle-benchmark-dataset",
            "schema_version": 1,
            "stages": list(STAGES),
            "runs": [],
            "repositories": [
                {
                    "source_url": "https://github.com/a/" + name,
                    "human_labels": {s: 1 for s in STAGES},
                    "results": {},
                }
                for name in ["one", "two"]
            ],
        },
    )
    out = tmp_path / "assessment"
    report = assess(run, reference, out)
    assert all(row["evaluated_repositories"] == 0 for row in report["modes"])
    import csv

    rows = list(csv.DictReader((out / "all_modes_comparison.csv").open()))
    assert len(rows) == 2 * 3 * 6
    assert all(row["prediction"] == "" and row["scan_complete"] == "False" for row in rows)
    summaries = list(csv.DictReader((out / "repository_summary.csv").open()))
    assert len(summaries) == 6
    assert all(len(json.loads(row["unknown_stages"])) == 6 for row in summaries)
