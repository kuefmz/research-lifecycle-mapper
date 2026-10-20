# Run the UI and your benchmark

From the project root:

```bash
uv sync --frozen
uv run --frozen python -m lifecycle_mapper ui
```

Open http://127.0.0.1:8000. The server runs locally and reads the same versioned heuristic catalogs as the CLI. A different port can be selected with `--port 8001`.

## Any GitHub repository

Choose **Analyze a repository**, paste its public GitHub URL, choose documentation, code, combined, or all three, and click Analyze. Optionally select a branch, tag or commit. The acquisition resolves an immutable revision, captures its inventory/content, and stores a snapshot.

The result table has one row per repository; select the prediction mode above it. Each stage shows prediction, human reference when present, and documentation/code/overall unique occurrence counts. Filters and sorting support mismatch review. Click a row to inspect the original excerpts, rule IDs, paths, line numbers and revision-pinned GitHub links. Partial scans are marked explicitly; absent labels in partial scans are not reliable negatives. Download predictions, evidence, errors, complete results and execution manifests from the result panel.

## Run heuristics for the benchmark

Choose **Run the benchmark**. Upload:

* Original Excel workbook: the UI reads **final_agreement** (legacy **Agreement Final** also supported). Preview the first rows and specify the literal repository URL column and header row. The final_agreement A:G schema also supplies reference labels for display after classification.
* CSV: include `repository_url`, `github_repository_url`, `source_url`, `original_repository_url`, or `repository`. Owner/name identifiers are accepted in a repository column. Repeated repository-stage rows are deduplicated; conflicting revisions are rejected.
* JSON: a list of URLs/repository objects or an object with a `repositories` array, including the candidate manifest produced by the consensus importer.
* Text: one repository URL per line.

Or paste URLs directly. Leave sample size empty to execute the full list, or enter a sample size and seed to choose a reproducible random subset. Run all three modes or select one. The original uploaded file remains unchanged; an exact copy and checksum are retained locally. Sample settings, extracted source rows, resolved commits, snapshots and catalog version are recorded. No stage label from the uploaded workbook/CSV is used by prediction.

**Approved human labels are not required to execute heuristics.** The separate **Compare with approved human labels** action runs the existing research evaluation config when consensus, provenance and snapshots are ready. This distinction prevents missing labels from blocking ordinary prediction while preserving research integrity for reported metrics.

Equivalent batch CLI:

```bash
uv run --frozen python -m lifecycle_mapper benchmark predict --input /path/to/benchmark.xlsx --worksheet final_agreement --repository-column A --header-row 1 --output local/benchmark-predictions
uv run --frozen python -m lifecycle_mapper benchmark predict --input /path/to/repositories.csv --output local/csv-predictions
```

The default is all three modes. Add `--mode documentation-only` if desired. Use a new output directory per run. Workbook prediction does not require an approved consensus mapping; it only requires selecting the correct repository URL column. Formal `benchmark import` remains the separate audited Agreement Final label importer.

## History and offline replay

Run data and uploads are stored under ignored `local/ui/` (change with `--state-dir`). **Previous runs** reopens saved predictions after server restarts. **Replay captured inputs** reruns the captured repositories with current rules without accessing GitHub; replay also keeps a reusable copy of the snapshots. Original results are never overwritten. Replay after changing rules may legitimately change predictions and records the new rule hash.

For large batches, set `GITHUB_TOKEN` in the shell before starting the UI to use authenticated GitHub API limits. The token is read by the backend and is never included in browser responses or saved results. Repository acquisition never executes inspected code.

The UI uses candidate heuristics; measured reference comparisons and their limits are documented in the implementation report. The read-only workbook export and final-label JSON are bundled under data/. Imported `results.json` files can be reopened under Previous runs; snapshots must be retained separately for offline replay.
