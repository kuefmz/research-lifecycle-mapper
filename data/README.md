# Benchmark inputs and persistent results

`research_lifecycle_benchmark_100_msr27.xlsx` is the unchanged read-only export of the supplied Google Drive workbook. It includes the original annotator and comparison sheets. The reference for this application is **final_agreement**, A2:A101 for URLs and B:G for six binary labels. The final documentation labels are jointly adjudicated by Jenifer and Esteban (confirmed 2026-10-20). The historical export has one missing independent annotation; a reported correction was not visible in the connected original tab during this update. See ../docs/annotation_status_20261020.md. Do not infer the independent value or change consensus to improve classifier agreement.

`research_lifecycle_benchmark_100_msr27.json` contains the same 100 repositories and final human labels, their worksheet rows, the workbook checksum and a versioned schema. It starts with empty run histories. Human labels and previous results never enter the matching algorithm.

From the repository root:

```bash
uv sync --frozen
uv run --frozen python -m lifecycle_mapper benchmark execute --transport git
```

This uses the bundled JSON automatically, creates a fresh snapshot/export directory under `local/benchmark-runs/<run-id>/`, and checkpoints each completed repository into **the same JSON file**. Use `--transport api` with server-side `GITHUB_TOKEN` if preferred. Optional `--mode documentation-only`, `--mode code-only`, `--mode combined`, and `--output local/new-run-directory` are supported. The default is all three modes. The UI's **Run bundled benchmark and save results to JSON** button uses this same workflow.

Every repository has `human_labels` and `results`, keyed by run ID. Each result embeds all modes, predictions, counts, evidence, exclusions and errors, plus acquisition/snapshot references. Top-level `runs` records timestamps, rule/source hashes, transport, modes, completion status and export-directory location (relative to this data folder). Snapshot paths within an acquisition record are relative to that run's output directory. Raw captured source files remain in the snapshot folders so the JSON stays portable and manageable; retain those folders for offline replay.

You can also open this same dataset JSON under **Previous runs** in the UI; it reviews the latest saved run, including partially checkpointed runs. A dataset with no executions reports that it must be run first.

Runs append rather than overwrite earlier results. Repository identity joins data and results, similar to the upstream project's repository-keyed JSON store, but cache reuse is not permanent by URL: different commits/rules/modes must remain distinguishable. Writes use a cross-process `.json.lock` and atomic replacement; a second writer is rejected. If a process is killed, verify it is no longer running before manually removing its stale lock. Completed checkpoints survive; an interrupted run may still show `running`. A later invocation creates a new history entry.

The dataset JSON intentionally becomes modified in Git after execution. Review it and use `git add data/research_lifecycle_benchmark_100_msr27.json` when you want to version the new results. Runtime does not commit automatically. The Excel source is never changed.

To regenerate a **new** JSON from the source workbook:

```bash
uv run --frozen python -m lifecycle_mapper benchmark dataset data/research_lifecycle_benchmark_100_msr27.xlsx --output local/fresh-benchmark.json
```

The converter refuses to overwrite an existing file or discard its history. The older `benchmark predict --input data/research_lifecycle_benchmark_100_msr27.json --output local/new-export` also works and attaches the reference labels; it only writes the run directory and does not mutate its input JSON.

Upstream inspected read-only at `dfb22f9545860a99a57199975dd78a4d9cb80fea`: `data/`, `storage.py` repository-keyed persistence, and `batch.py`. This implementation is independently authored; no upstream source was copied and that repository was not modified.
