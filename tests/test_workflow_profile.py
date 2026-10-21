from pathlib import Path

import pytest

from lifecycle_mapper.analysis import analyze
from test_portable_code import portable_snapshot
from test_rules import make_snapshot

PROFILE = Path(__file__).resolve().parents[1] / "configs/workflow-development-v5.2"


@pytest.mark.parametrize(
    "text",
    [
        "Code to run the simulations in the paper. The main script trains the autoencoder model over synthetic datasets.",
        "This repository contains code for the experiments in our paper.",
    ],
)
def test_paper_code_and_training_are_not_method_proxies(tmp_path, text):
    result = analyze(
        make_snapshot(tmp_path, text, "README.md"), "documentation-only", rules_dir=PROFILE
    )
    assert "Method" not in result["labels"]


@pytest.mark.parametrize(
    "path,text,stage",
    [
        ("run.sh", 'evaluate.py "$gold" "$predictions" > "$output"\n', "Evaluation"),
        ("run.sh", "python evaluate.py gold.tsv predictions.tsv > scores.txt\n", "Evaluation"),
        ("fit.m", "W = W-eta*grad_mat;", "Method"),
        (
            "run.m",
            "for u=1:A_reps\n[W_final, final_norm] = grad_descent(W, X, Y, k);\nend",
            "Experimentation",
        ),
        ("run.m", "Y_diff_final = W_final_norm_T*X_test - Y_test;", "Evaluation"),
        ("run.py", "score = f1_score(y_true, y_pred)", "Evaluation"),
    ],
)
def test_executable_workflow_evidence(tmp_path, path, text, stage):
    result = analyze(portable_snapshot(tmp_path, text, path), "code-only", rules_dir=PROFILE)
    assert result["scan_complete"]
    assert stage in result["labels"]


@pytest.mark.parametrize(
    "text",
    [
        '# evaluate.py "$gold" "$predictions" > "$output"\n',
        'echo "evaluate.py gold predictions > output"\n',
    ],
)
def test_shell_comments_and_messages_are_not_operations(tmp_path, text):
    result = analyze(portable_snapshot(tmp_path, text, "run.sh"), "code-only", rules_dir=PROFILE)
    assert "Evaluation" not in result["labels"]


def test_single_optimizer_call_does_not_prove_repeated_experiment(tmp_path):
    result = analyze(
        portable_snapshot(tmp_path, "W = grad_descent(W, X, Y);", "run.m"),
        "code-only",
        rules_dir=PROFILE,
    )
    assert "Experimentation" not in result["labels"]


def test_documented_computational_mechanism_is_method(tmp_path):
    text = "This code implements a reranker. The reranker consists of two main steps: feature extraction and supervised learning."
    result = analyze(
        make_snapshot(tmp_path, text, "README.md"), "documentation-only", rules_dir=PROFILE
    )
    assert "Method" in result["labels"]
