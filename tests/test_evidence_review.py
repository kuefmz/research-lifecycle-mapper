import base64
from pathlib import Path
from urllib.error import HTTPError
from email.message import Message

import pytest

from lifecycle_mapper import STAGES
from lifecycle_mapper.acquisition import GitHubAPIError, api_get
from legacy_catalog import analyze
from lifecycle_mapper.analysis import implementation_view
from lifecycle_mapper.canonical import write_json
from lifecycle_mapper.comparison import compare
from lifecycle_mapper.reference import describe_reference, final_reference
from lifecycle_mapper.web import Application
from test_consensus import fixture
from test_rules import make_snapshot

ROOT = Path(__file__).resolve().parents[1]


def final_workbook(tmp_path, count=100, mutation=None):
    path, config = fixture(tmp_path, count=count, mutation=mutation, sheet_name="final_agreement")
    # Reuse real XML fixture builder, rearrange to the observed A:G schema.
    import zipfile
    from xml.etree import ElementTree as ET

    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    tree = ET.fromstring(entries["xl/worksheets/sheet1.xml"])
    for row in tree.findall("s:sheetData/s:row", ns):
        cells = list(row)
        row.remove(cells[0])
        row.remove(cells[-1])
        for i, cell in enumerate(row):
            cell.set("r", chr(65 + i) + row.attrib["r"])
        if row.attrib["r"] == "1":
            row[0].find(".//s:t", ns).text = "GitHub URL"
    entries["xl/worksheets/sheet1.xml"] = ET.tostring(tree)
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return path


def test_observed_reference_layout_counts_and_no_mutation(tmp_path):
    p = final_workbook(tmp_path)
    raw = p.read_bytes()
    labels = final_reference(p)
    assert len(labels) == 100
    assert all(set(row) == set(STAGES) for row in labels.values())
    assert all(v["positive"] == 50 for v in describe_reference(labels)["stages"].values())
    assert p.read_bytes() == raw


@pytest.mark.parametrize("value", ["", "?", "2", "0.5", "true"])
def test_missing_or_invalid_reference_rejected(tmp_path, value):
    p = final_workbook(
        tmp_path, mutation=lambda row, i: row.__setitem__(2, value) if i == 0 else None
    )
    with pytest.raises(ValueError, match="nonbinary"):
        final_reference(p)


def test_duplicate_reference_rejected(tmp_path):
    p = final_workbook(
        tmp_path,
        mutation=lambda row, i: row.__setitem__(1, "https://github.com/synthetic/repo-0")
        if i == 1
        else None,
    )
    with pytest.raises(ValueError, match="Duplicate"):
        final_reference(p)


def test_all_matches_deduplicated_with_rule_attributions_and_counts(tmp_path):
    snapshot = make_snapshot(
        tmp_path, "We collect raw research data.\nWe collect raw research data.\n", "README.md"
    )
    result = analyze(snapshot, "combined")
    assert result["evidence_counts"]["Collection"] == {"documentation": 2, "code": 0, "overall": 2}
    evidence = result["evidence"]
    assert len(evidence) == 2
    assert len({e["evidence_id"] for e in evidence}) == 2
    assert all(len(e["matched_rules"]) >= 2 for e in evidence)
    assert all(e["run_id"] == result["run_id"] and e["rule_version"] for e in evidence)
    assert analyze(snapshot, "combined") == result
    documentation = analyze(snapshot, "documentation-only")
    assert [e["evidence_id"] for e in evidence] == [
        e["evidence_id"] for e in documentation["evidence"]
    ]


def test_incomplete_absence_is_unknown():
    snapshot = ROOT / "benchmark/synthetic/snapshots/incomplete"
    result = analyze(snapshot, "documentation-only")
    assert not result["scan_complete"]
    assert all(v is None for v in result["predictions"].values())


CODE = {
    "Collection": "def download_dataset():\n    return requests.get(url)\n",
    "Processing": "def preprocess_data(data):\n    return data.dropna()\n",
    "Method": "def estimate_model(x):\n    return np.linalg.solve(x, y)\n",
    "Experimentation": "search = GridSearchCV(estimator=model, param_grid=grid)\nsearch.fit(x, y)\n",
    "Evaluation": "score = f1_score(y_true, y_pred)\n",
    "Dissemination": "fig.savefig(output_file)\n",
}


@pytest.mark.parametrize("stage", STAGES)
def test_new_python_rule_positive_and_comments_strings_tests_negative(tmp_path, stage):
    text = CODE[stage]
    positive = analyze(make_snapshot(tmp_path / "positive", text), "code-only")
    assert stage in positive["labels"]
    assert any(
        any(r["id"].endswith("CODE_RESEARCH_V3") for r in e["matched_rules"])
        for e in positive["evidence"]
        if e["stage"] == stage
    )
    for name, negative in [
        ("comment", "\n".join("# " + line for line in text.splitlines())),
        ("string", repr(text)),
    ]:
        assert stage not in analyze(make_snapshot(tmp_path / name, negative), "code-only")["labels"]
    assert (
        stage
        not in analyze(
            make_snapshot(tmp_path / "test", text, "tests/test_activity.py"), "code-only"
        )["labels"]
    )


MULTI = {
    "Collection": ("download.file(data_url, destfile=dataset)\n", ".r"),
    "Processing": ("data = zscore(data);\n", ".m"),
    "Method": ("estimate <- function(data) {\n model <- lm(data)\n}\n", ".r"),
    "Experimentation": ("for seed in seeds\n run_trial(seed)\nend\n", ".jl"),
    "Evaluation": ("accuracy = mean(predictions == labels);\n", ".m"),
    "Dissemination": ("ggsave(output, plot=results)\n", ".r"),
}


@pytest.mark.parametrize("stage", STAGES)
def test_multilingual_positive_and_comment_exclusion(tmp_path, stage):
    text, suffix = MULTI[stage]
    assert (
        stage
        in analyze(
            make_snapshot(tmp_path / "positive", text, "src/activity" + suffix), "code-only"
        )["labels"]
    )
    comment = "%" if suffix == ".m" else "#"
    masked = "\n".join(comment + " " + line for line in text.splitlines())
    assert (
        stage
        not in analyze(
            make_snapshot(tmp_path / "negative", masked, "src/activity" + suffix), "code-only"
        )["labels"]
    )
    assert implementation_view(text, "src/activity" + suffix).count("\n") == text.count("\n")


@pytest.mark.parametrize(
    "status,remaining,code",
    [
        (401, None, "invalid-token"),
        (403, "0", "rate-limit"),
        (404, None, "not-found-or-inaccessible"),
        (429, None, "rate-limit"),
    ],
)
def test_auth_and_api_errors_are_sanitized(monkeypatch, status, remaining, code):
    from lifecycle_mapper import acquisition

    token = "secret-never-export"
    monkeypatch.setenv("GITHUB_TOKEN", token)
    headers = Message()
    if remaining is not None:
        headers["X-RateLimit-Remaining"] = remaining

    def fail(request, timeout):
        assert request.get_header("Authorization") == "Bearer " + token
        raise HTTPError(request.full_url, status, token, headers, None)

    monkeypatch.setattr(acquisition, "urlopen", fail)
    with pytest.raises(GitHubAPIError) as exc:
        api_get("/repos/a/b")
    assert exc.value.code == code
    assert token not in str(exc.value)


def test_workbook_upload_reference_comparison_and_reopen(tmp_path, monkeypatch):
    from lifecycle_mapper import batch
    from test_batch import fake_acquisition
    from test_web import wait_job

    monkeypatch.setattr(batch, "acquire", fake_acquisition)
    p = final_workbook(tmp_path, count=1)
    app = Application(ROOT, tmp_path / "state")
    try:
        upload = app.upload(
            {"filename": "benchmark.xlsx", "content": base64.b64encode(p.read_bytes()).decode()}
        )
        assert upload["worksheet"] == "final_agreement" and upload["repository_column"] == "A"
        job_id = app.start({"kind": "batch", "upload_id": upload["upload_id"], "mode": "all"})["id"]
        job = wait_job(app, job_id)
        assert job["status"] == "completed"
        assert job["result"]["repositories"][0]["human_labels"] is not None
        restored_id = app.import_results({"result": job["result"]})["id"]
        restored = app.job(restored_id)["result"]
        assert restored["imported"]
        assert restored["repositories"] == job["result"]["repositories"]
        with pytest.raises(ValueError):
            app.import_results({"result": {"repositories": [{}]}})
    finally:
        app.pool.shutdown()


def test_comparison_rejects_overlapping_split_before_writing(tmp_path):
    # Real fixture import produces checksum-bound labels; no network is involved.
    from lifecycle_mapper.consensus import import_final
    from lifecycle_mapper.canonical import sha256

    source, config = fixture(tmp_path)
    approval = tmp_path / "approval.json"
    write_json(
        approval,
        {
            "status": "approved",
            "worksheet": "Agreement Final",
            "workbook_sha256": sha256(source.read_bytes()),
            "import_config_sha256": sha256(config.read_bytes()),
            "approval_reference": "synthetic-test",
        },
    )
    reference = tmp_path / "reference"
    import_final(source, reference, config, approval)
    split = tmp_path / "split.json"
    write_json(split, {"development": ["synthetic/repo-0"], "held_out": ["synthetic/repo-0"]})
    with pytest.raises(ValueError, match="partition"):
        compare(reference, tmp_path / "missing", split, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_documentation_commands_and_isolated_algorithm_word_do_not_trigger(tmp_path):
    text = "python client/query.py --filters data/algorithm.txt\n"
    assert (
        analyze(make_snapshot(tmp_path / "flags", text, "README.md"), "documentation-only")[
            "labels"
        ]
        == []
    )
    text = "This repository discusses an algorithm.\n"
    assert (
        "Method"
        not in analyze(
            make_snapshot(tmp_path / "keyword", text, "README.md"), "documentation-only"
        )["labels"]
    )


def test_python_statement_rules_cannot_borrow_context_from_next_statement(tmp_path):
    text = "score = f1_score(a, b)\ny_true = labels\n"
    assert "Evaluation" not in analyze(make_snapshot(tmp_path, text), "code-only")["labels"]


def test_git_transport_immutable_capture_and_replay(tmp_path, monkeypatch):
    import subprocess
    from lifecycle_mapper import git_acquisition
    from lifecycle_mapper.acquisition import replay

    content = b"data = zscore(data);\n"
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        if "ls-remote" in args:
            value = ("a" * 40 + "\trefs/heads/main\n").encode()
        elif "clone" in args:
            Path(args[-1]).mkdir(parents=True)
            value = b""
        elif "rev-parse" in args:
            value = (("b" if args[-1].endswith("^{tree}") else "a") * 40 + "\n").encode()
        elif "ls-tree" in args:
            value = (
                f"100644 blob {'c' * 40} {len(content)}\tsrc/model.m\0"
                f"100644 blob {'d' * 40} 300000\tlarge.txt\0"
                f"120000 blob {'e' * 40} 3\tlink.py\0"
            ).encode()
        elif "cat-file" in args:
            value = content
        else:
            raise AssertionError(args)
        return subprocess.CompletedProcess(args, 0, stdout=value, stderr=b"")

    monkeypatch.setattr(git_acquisition.subprocess, "run", fake_run)
    manifest = git_acquisition.acquire_git("https://github.com/owner/repo", tmp_path / "snapshot")
    assert manifest["commit"] == "a" * 40 and manifest["transport"] == "git-partial-clone"
    assert any("--no-checkout" in call for call in calls)
    _, files = replay(tmp_path / "snapshot")
    assert files == {"src/model.m": content.decode()}
    assert analyze(tmp_path / "snapshot", "code-only")["labels"] == ["Processing"]
    assert not analyze(tmp_path / "snapshot", "combined")["scan_complete"]
    assert all("GITHUB_TOKEN" not in str(call) for call in calls)


def test_git_failures_do_not_expose_subprocess_output(tmp_path, monkeypatch):
    import subprocess
    from lifecycle_mapper import git_acquisition

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args, stderr=b"secret-response")

    monkeypatch.setattr(git_acquisition.subprocess, "run", fail)
    with pytest.raises(OSError) as exc:
        git_acquisition.acquire_git("https://github.com/owner/repo", tmp_path / "snapshot")
    assert "secret-response" not in str(exc.value)
    assert not (tmp_path / "snapshot").exists()


def test_verified_config_accepts_final_sheet_without_row_id_column(tmp_path):
    from lifecycle_mapper.consensus import import_final

    p = final_workbook(tmp_path)
    output = tmp_path / "imported"
    imported = import_final(p, output, ROOT / "configs/final-agreement-import.yaml")
    assert imported["pair_count"] == 600
    assert imported["source_worksheet"] == "final_agreement"
    assert "final_agreement!2" in (output / "benchmark.csv").read_text()


def test_comparison_reports_missing_acquisitions_without_negative_labels(tmp_path):
    import shutil
    from lifecycle_mapper.consensus import import_final
    from lifecycle_mapper.canonical import read_json, sha256

    source, config = fixture(tmp_path)
    approval = tmp_path / "approval.json"
    write_json(
        approval,
        {
            "status": "approved",
            "worksheet": "Agreement Final",
            "workbook_sha256": sha256(source.read_bytes()),
            "import_config_sha256": sha256(config.read_bytes()),
            "approval_reference": "synthetic-test",
        },
    )
    reference = tmp_path / "reference"
    import_final(source, reference, config, approval)
    split = tmp_path / "split.json"
    write_json(
        split,
        {
            "development": [f"synthetic/repo-{i}" for i in range(80)],
            "held_out": [f"synthetic/repo-{i}" for i in range(80, 100)],
        },
    )
    run = tmp_path / "run"
    snapshot = run / "snapshots/one"
    shutil.copytree(ROOT / "benchmark/synthetic/snapshots/docs-positive", snapshot)
    manifest = read_json(snapshot / "manifest.json")
    manifest.update(repository="synthetic/repo-0", source_url="https://github.com/synthetic/repo-0")
    write_json(snapshot / "manifest.json", manifest)
    write_json(
        run / "manifest.json",
        {
            "repositories": [
                {
                    "repository": "synthetic/repo-0",
                    "status": "analyzed",
                    "snapshot": "snapshots/one",
                    "snapshot_sha256": sha256((snapshot / "manifest.json").read_bytes()),
                }
            ]
        },
    )
    output = tmp_path / "comparison"
    metrics = compare(reference, run, split, output)
    assert metrics["development"]["combined"]["complete"] == 1
    assert metrics["development"]["combined"]["population"] == 80
    assert metrics["development"]["combined"]["complete_case"]["macro"]["f1"] == 0.5
    rows = read_json(output / "results.json")["repositories"]
    assert len(rows) == 80 and sum(bool(r["modes"]) for r in rows) == 1
    assert all(r["modes"] == [] for r in rows if r.get("error"))
    assert (output / "evidence.jsonl").stat().st_size > 0


def test_unicode_separators_and_crlf_keep_github_physical_line_numbers(tmp_path):
    text = "Preamble with a Unicode separator\u2028still physical line one.\r\nWe collect raw research data.\r\n"
    result = analyze(make_snapshot(tmp_path, text, "README.md"), "documentation-only")
    evidence = result["evidence"][0]
    assert evidence["start_line"] == evidence["end_line"] == 2
    assert evidence["excerpt"] == "We collect raw research data."
    assert evidence["url"].endswith("#L2-L2")
