# Research Lifecycle Mapper

A local UI and CLI for deterministic, inspectable **evidence** of Collection, Processing, Method, Experimentation, Evaluation and Dissemination in GitHub repositories. These are six independent binary labels. A match does not establish that an activity actually occurred, that research is scientifically valid, or that a repository is reproducible.

## Install and start

Requires Git and Python **3.12**. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
git clone --single-branch --branch main https://github.com/kuefmz/research-lifecycle-mapper.git
cd research-lifecycle-mapper
uv python install 3.12.14
uv sync --frozen
uv run --frozen python -m lifecycle_mapper ui
```

Open **http://127.0.0.1:8000**. To update an existing checkout, use `git pull --ff-only` before `uv sync --frozen`. The maintained branch is `main`. Windows PowerShell uses the same Git/uv commands. Dependencies and Python/uv versions are pinned; production code uses the Python standard library.

* **Analyze a repository:** paste a public repository URL, optionally choose a branch/tag/commit, and compare all three evidence modes. The revision resolves once to an immutable commit. Repository code is never executed.
* **Run the benchmark:** upload the original workbook, CSV, JSON or URL text. The verified workbook uses `final_agreement`, URL column **A**, header row **1**, and labels **B:G**. Preview the mapping. The original workbook is never modified. The legacy `Agreement Final` upload is also supported.
* **Review:** one overview row per repository, six predictions and human labels where available, mismatches, documentation/code/unique counts, status and errors. Filter by repository, stage-specific minimum count, mismatches or partial scans; sort by repository, mismatches or evidence. Click a row for the six-stage count table, file breakdown and complete evidence table.
* **Previous runs:** reopen saved runs after restarting, or import an exported `results.json`. Imported JSON restores review, not missing snapshots. Offline replay requires the original run directory and captured snapshots.

Reference labels are attached **after** classification and never become classifier features. No human labels are required for a new repository. CSV/JSON repository-list inputs do not automatically imply approved reference labels.

## GitHub token

`GITHUB_TOKEN` is used by `--transport api`; it does not authenticate `--transport git`. After setting the token in the same terminal, run `uv run --frozen python -m lifecycle_mapper benchmark execute --transport api`. CLI benchmark commands display `[completed/total] repository` progress on stderr while keeping their final JSON on stdout. Invalid-escape SyntaxWarnings in inspected Python string literals are suppressed narrowly; genuine syntax errors remain recorded as analysis failures.

The default API transport reads `GITHUB_TOKEN` only on the backend. Create a short-lived fine-grained token in GitHub **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**. For this public benchmark, public read access is sufficient; do not grant write permissions. If explicitly accessing selected private repositories, grant only the required read access, including Contents. Follow [GitHub's token instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) and [endpoint permission requirements](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens).

macOS/Linux (Bash):

```bash
read -rsp 'GitHub token: ' GITHUB_TOKEN; echo
export GITHUB_TOKEN
uv run --frozen python -m lifecycle_mapper ui
unset GITHUB_TOKEN
```

Windows PowerShell:

```powershell
$tokenInput = Read-Host 'GitHub token' -AsSecureString
$env:GITHUB_TOKEN = [System.Net.NetworkCredential]::new('', $tokenInput).Password
Remove-Variable tokenInput
uv run --frozen python -m lifecycle_mapper ui
Remove-Item Env:GITHUB_TOKEN
```

Enter secrets only in your local terminal. Never paste them into chat or the browser, commit them, or include them in exports. Authentication headers and API response bodies are not logged or exported. Invalid credentials, rate limits and inaccessible repositories produce sanitized errors. Temporary 5xx failures receive at most two short retries; rate-limit failures do not wait indefinitely. Token reset metadata is available on the sanitized exception. The optional public Git transport does not consume `GITHUB_TOKEN`.

## Run the full benchmark

The Excel workbook and its JSON equivalent are bundled under [`data/`](data/README.md). To run all 100 repositories and save each repository's results back into the same JSON, preserving earlier run history:

```bash
uv run --frozen python -m lifecycle_mapper benchmark execute --transport git
```

The UI includes **Run bundled benchmark and save results to JSON**. Keep the generated snapshot folders for offline replay. See [the dataset schema and persistence guide](data/README.md).

For a separate export without changing the JSON dataset:


```bash
uv run --frozen python -m lifecycle_mapper benchmark predict --input data/research_lifecycle_benchmark_100_msr27.xlsx --worksheet final_agreement --repository-column A --header-row 1 --output local/benchmark-run
```

All three modes run by default. A token is recommended for API batches. Without one, an optional public Git partial-clone transport avoids API request limits:

```bash
uv run --frozen python -m lifecycle_mapper benchmark predict --input /path/to/benchmark.xlsx --transport git --output local/git-run
```

Git transport requires a partial-clone-capable Git/server and can be slower for repositories with many small blobs. Git failures remain explicit. Use a new output directory for every run. The API transport remains the UI default.

## Single repository, modes and evidence

```bash
uv run --frozen python -m lifecycle_mapper acquire https://github.com/OWNER/REPO --ref main --snapshot local/snapshots/example
uv run --frozen python -m lifecycle_mapper analyze --snapshot local/snapshots/example --mode combined --output local/example.json
```

Documentation-only and code-only are isolated; **combined is their logical OR**. Supporting conditions alone never trigger a label. Rules require conjunctive research activity/object or operation/context signals and apply exclusions. Markdown/reStructuredText/AsciiDoc/plain text are supported; Python uses AST/tokenization, while R, Julia, MATLAB and shell have conservative lexical rules. Other inventoried code languages, notebooks and binary formats have limited or no detector coverage. Lexical detection is not semantic program analysis.

Each occurrence records repository URL/identifier, immutable commit, source, path, exact **1-based inclusive** line range, original excerpt, stable evidence ID, analysis run ID, rule ID/version, catalog hash and all matching rule attributions. Links use `/blob/COMMIT/path#Lstart-Lend`. Strength is a rule-match description, not a calibrated probability.

Deduplication key: repository/commit/stage/source/path/start/end/excerpt. Identical passages matched by several rules count once; all rule IDs/versions remain in `matched_rules`. Different locations or stages remain distinct. Overlapping but different line spans remain separate. Combined counts use occurrence IDs, never the sum of documentation/code/combined mode exports. Counts are scoped to the analyzed modes; use all three for the complete source comparison.

A complete scan with no match predicts 0. An incomplete scan with no match predicts **unknown** (`null` in JSON, empty CSV cell); observed positive evidence remains positive. Acquisition failures have errors and no fabricated six-negative prediction. Complete means complete under the documented eligibility/size/language policy, not complete scientific knowledge.

## Exports and offline replay

A batch run contains `results.json`, `predictions.csv`, `evidence_counts.csv`, `evidence.jsonl`, `excluded_evidence.jsonl`, `errors.csv`, a provenance manifest and hash-verified snapshots. JSONL includes mode-specific views; use `evidence_id` to avoid double-counting the same occurrence across views. Excluded candidates are separate from positive counts. Snapshot inventories preserve excluded/unavailable paths and acquisition errors. Run manifests record times, classifier commit/source hash, rule hash and parameters. Analysis IDs are content-addressed from snapshot/rules/mode, so identical replay retains identity.

Keep the **whole run directory** to replay captured input. From the UI choose **Replay captured inputs**; this makes a new run using current rules without GitHub access. Failed acquisitions have no snapshot to replay. Individual snapshots can also use `snapshot pack` / `snapshot unpack`; see [reproducibility](docs/reproducibility.md).

## Current research scope and corpus execution

Jenifer and Esteban jointly reviewed and agreed on final_agreement after independent annotation. The 600 final labels describe documentation only. Documentation-only predictions are the primary accuracy evaluation; source-code matches are separate evidence-expansion candidates, not automatic corrections to gold. See [current annotation status](docs/annotation_status_20261020.md), including the discrepancy between the reported historical-cell correction and the connected original tab.

For the local software.tar extractor, two-call API/raw acquisition, bounded resumable corpus execution, pilot commands and runtime estimates, see [corpus execution](docs/corpus.md). The new runner preserves existing detector rules and computes all requested source modes in one matching pass. See [the ten-page MSR paper plan](docs/paper_plan_msr2027.md).

## Human reference audit and measured comparisons

See [the implementation and evaluation report](docs/implementation_report_20261015.md) for actual measurements, acquisition coverage and limitations. The read-only workbook export and final-label JSON are bundled under data/. The verified mapping is `configs/final-agreement-import.yaml`; the older mapping remains for legacy workbooks.

```bash
uv run --frozen python -m lifecycle_mapper benchmark import /path/to/benchmark.xlsx --config configs/final-agreement-import.yaml --approval /path/to/exact-reference-approval.json --output local/reference
uv run --frozen python -m lifecycle_mapper benchmark audit /path/to/benchmark.xlsx --annotator-sheets research_lifecycle_benchmark_10 'Hoja 10' --output local/audit.json
uv run --frozen python -m lifecycle_mapper benchmark compare --reference local/reference --run local/benchmark-run --split benchmark/versions/split-20261015.json --rules benchmark/versions/baseline-rules --output local/baseline-development
uv run --frozen python -m lifecycle_mapper benchmark compare --reference local/reference --run local/benchmark-run --split benchmark/versions/split-20261015.json --output local/candidate-development
```

The Drive XLSX export renamed some long annotator tabs; use the names actually in your workbook for `audit`. It validates repository sets and joins annotations by identity. The exact-workbook approval schema and hashes are described in [the import guide](docs/agreement_final.md). The task's explicit instruction to use final_agreement authorizes this reference comparison; this does not invent a separately approved human codebook or sampling provenance.

`compare` defaults to development only. Freeze rules before adding `--partition held_out`. Use `--partition full_exploratory` for a clearly exploratory all-repository view. It reports per-stage P/R/F1/accuracy/confusion counts, macro/micro metrics, exact match, Hamming loss, coverage and mismatch CSVs. Complete-case metrics exclude partial/failed scans independently per mode. Captured-evidence metrics include partial scans and are explicitly exploratory. Do not report them as an unbiased held-out evaluation. The older formal `benchmark run` retains its separate publication-provenance requirements.

## Verify changes

```bash
uv run --frozen ruff check src tests scripts
uv run --frozen ruff format --check src tests scripts
uv run --frozen mypy
uv run --frozen pytest -q --basetemp local/pytest
uv run --frozen playwright install chromium
RLM_BROWSER_TEST=1 uv run --frozen pytest tests/browser -q --basetemp local/browser-tests
```

PowerShell: set `$env:RLM_BROWSER_TEST='1'` before the last command. Optional DOM checks (Node.js): `npm install --prefix local/ui-verification --ignore-scripts jsdom@30.1.3`, then set `NODE_PATH` to `local/ui-verification/node_modules` and run `node scripts/test_ui_dom.cjs`. They check table/filter/detail behavior and escaping, not visual browser layout. Synthetic fixture metrics are software checks, never human benchmark performance.

[Methodology](docs/methodology.md) · [Evaluation protocol](docs/evaluation_protocol.md) · [Rule-change protocol](docs/rule_change_protocol.md) · [Limitations](docs/limitations.md) · [Implementation provenance](docs/implementation_provenance.md)

The separate upstream `kuefmz/research_artefacts_and_processes` is not modified. Its previously inspected tree declared no license; no upstream source was copied.
