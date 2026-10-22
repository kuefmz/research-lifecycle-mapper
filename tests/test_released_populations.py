"""Population integrity and released benchmark prediction provenance."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_full_populations_are_unique_and_nested():
    populations = {}
    for name, expected in [("benchmark-100", 100), ("corpus-386", 386), ("corpus-3211", 3211)]:
        values = (ROOT / "results" / name / "repositories.txt").read_text().splitlines()
        identities = {v.casefold().removeprefix("https://github.com/").rstrip("/") for v in values}
        assert len(values) == len(identities) == expected
        populations[name] = identities
    assert populations["benchmark-100"] < populations["corpus-386"] < populations["corpus-3211"]
    assert not (ROOT / "results/openaire-3211").exists()
    assert not (ROOT / "results/llm").exists()


def test_consolidated_benchmark_preserves_original_assessment_and_order():
    directory = ROOT / "results/benchmark-100"
    source = list(csv.DictReader((directory / "assessment/all_modes_comparison.csv").open()))
    original = {(r["repository"].casefold(), r["mode"], r["stage"]): r for r in source}
    released = list(csv.DictReader((directory / "predictions.csv").open()))
    assert len(released) == len(original) == 1800
    identities = []
    seen = set()
    for row in released:
        repo = row["repository"].removeprefix("https://github.com/").casefold()
        key = (repo, row["mode"], row["stage"])
        assert key not in seen
        seen.add(key)
        expected = original[key]
        assert row["prediction"] == (expected["prediction"] or "?")
        assert row["scan_complete"] == expected["scan_complete"]
        assert row["commit"] == expected["commit"]
        if not identities or identities[-1] != repo:
            identities.append(repo)
    order = [
        v.removeprefix("https://github.com/").casefold()
        for v in (directory / "repositories.txt").read_text().splitlines()
    ]
    assert identities == order


def test_full_corpus_aggregates_reproduce_from_preserved_sources():
    import importlib.util
    import json

    path = ROOT / "results/corpus-3211/reproduce_results.py"
    spec = importlib.util.spec_from_file_location("corpus_counts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module.reproduce()
    saved = json.loads((path.parent / "aggregate_summary.json").read_text())
    assert rows == saved["stage_counts"]
    assert len(rows) == 18
    assert all(r["positive"] + r["negative"] + r["unknown"] == 3211 for r in rows)
    assert all(r["unknown"] > 0 for r in rows)
    keyed = {(r["mode"], r["stage"]): r for r in rows}
    for stage in module.STAGES:
        assert keyed["combined", stage]["positive"] >= max(
            keyed[mode, stage]["positive"] for mode in ("documentation-only", "code-only")
        )
