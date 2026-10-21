from pathlib import Path

import pytest

from lifecycle_mapper.analysis import analyze
from test_portable_code import portable_snapshot
from test_rules import make_snapshot

PROFILE = Path(__file__).resolve().parents[1] / "configs/simulation-development-v5.3"


@pytest.mark.parametrize(
    "path,text,stage",
    [
        ("model.R", "response <- exp(x)\nenergy <- numerator/denominator\n", "Method"),
        (
            "Simulation.java",
            "void tick(){ Order action = agent.decide(book, day); if(action!=null){market.send(agent, action);} }",
            "Method",
        ),
        (
            "Simulation.java",
            "void run(){while(day.currentTick() <= day.totalTicks()){queryAllAgents(); day.nextTick();}}",
            "Experimentation",
        ),
    ],
)
def test_scientific_simulation_operations(tmp_path, path, text, stage):
    result = analyze(portable_snapshot(tmp_path, text, path), "code-only", rules_dir=PROFILE)
    assert result["scan_complete"]
    assert stage in result["labels"]


@pytest.mark.parametrize(
    "path,text",
    [
        ("model.R", "# energy <- numerator/denominator\nx <- exp(y)\n"),
        ("model.R", 'message <- "energy <- numerator/denominator"\nx <- exp(y)\n'),
        ("model.R", "energy <- 100\nx <- exp(y)\n"),
        ("model.R", "result <- numerator/denominator\nx <- exp(y)\n"),
        ("model.R", "energy <- numerator/denominator\n"),
        ("Simulation.java", "class Simulation { double energy = 0; }"),
        ("Simulation.java", "void run(){while(queue.size()>0){process(); clock.nextTick();}}"),
        (
            "Simulation.java",
            "void first(){Order action=agent.decide(book,day);} void second(){market.send(agent, action);}",
        ),
    ],
)
def test_generic_or_nonexecutable_operations_do_not_gain_stages(tmp_path, path, text):
    result = analyze(portable_snapshot(tmp_path, text, path), "code-only", rules_dir=PROFILE)
    assert not result["labels"]


def test_supplied_measurements_are_documented_collection(tmp_path):
    text = "The sample data contains five years of meteorological data measured at a field station."
    result = analyze(
        make_snapshot(tmp_path, text, "README.md"), "documentation-only", rules_dir=PROFILE
    )
    assert "Collection" in result["labels"]


@pytest.mark.parametrize(
    "text,present,absent",
    [
        (
            "Experiment data and results on empirically comparing retained and incremental machine learning for modeling performance of adaptable software.",
            {"Dissemination"},
            {"Experimentation", "Evaluation"},
        ),
        (
            "Generate and analyze data with our simulator. Use grep to filter lines from the generated log files.",
            set(),
            {"Collection", "Processing"},
        ),
        (
            "This code can plot prices and report HTTP status codes. See https://example.org/documentation.html",
            set(),
            {"Dissemination"},
        ),
        (
            "We used a subset of the dataset; the last million triples can be obtained using the tail command.",
            {"Processing"},
            {"Collection"},
        ),
        (
            "This package implements statistical design of experiments for the study.",
            {"Method"},
            set(),
        ),
        (
            "This Java API provides artificial agents that trade in a simulated market for experiments.",
            {"Method"},
            set(),
        ),
    ],
)
def test_documentation_activity_roles(tmp_path, text, present, absent):
    result = analyze(
        make_snapshot(tmp_path, text, "README.md"), "documentation-only", rules_dir=PROFILE
    )
    assert present <= set(result["labels"])
    assert not absent.intersection(result["labels"])


def test_factorial_design_execution(tmp_path):
    text = "experiments <- apply(design, 1, experiment, files=files)"
    result = analyze(portable_snapshot(tmp_path, text, "run.R"), "code-only", rules_dir=PROFILE)
    assert "Experimentation" in result["labels"]


def test_no_source_logging_is_explicit():
    from lifecycle_mapper.corpus import repository_log
    from lifecycle_mapper import STAGES

    payload = {
        "mode": "code-only",
        "predictions": {s: False for s in STAGES},
        "scan_complete": True,
        "eligible_files": 0,
    }
    block = repository_log(
        {"requested_url": "https://github.com/a/b", "complete": True, "modes": [payload]},
        {"finished": 1, "repository_count": 1, "complete": 1, "partial": 0, "failed": 0},
        ("code-only",),
    )
    assert "no eligible source files" in block
    assert "code-only: 0 | 0 | 0 | 0 | 0 | 0" in block
