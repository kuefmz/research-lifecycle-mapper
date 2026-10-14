# Research Lifecycle Mapper

A local UI and command-line tool for running deterministic research lifecycle heuristics on GitHub repositories and your benchmark. The six stages are Collection, Processing, Method, Experimentation, Evaluation and Dissemination.

## Start the UI

With Git installed, run these commands in a macOS/Linux terminal:

```bash
curl -LsSf https://astral.sh/uv/0.12.23/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
git clone --single-branch --branch main https://github.com/kuefmz/research-lifecycle-mapper.git
cd research-lifecycle-mapper
uv python install 3.12.14
uv sync --frozen
uv run --frozen python -m lifecycle_mapper ui
```

If already cloned, update with `git pull --ff-only`, then run the last two commands. Open **http://127.0.0.1:8000**.

* **Analyze a repository:** paste any public GitHub repository URL, select evidence mode, run the heuristics, and inspect labels, original evidence excerpts, paths, rule IDs and commit-pinned links.
* **Run the benchmark:** upload your original Excel workbook, CSV, JSON or text repository list, or paste URLs. Run the full list or a reproducible random subset. Approved human labels are not required to generate predictions.
* **Previous runs:** reopen saved results, download CSV/JSON exports, and replay captured inputs offline.

Excel batch prediction reads **Agreement Final**; select the repository URL column and header row after inspecting its preview. This extracts repository inputs, not gold labels. Formal consensus import and evaluation remain separate.

Documentation-only is the primary classifier. Code-only and combined (logical OR) are independently traced comparison modes. The rules are candidate heuristics and have not yet been empirically validated against the unavailable approved human benchmark.

See [UI and benchmark guide](docs/ui.md).

## Batch benchmark execution from the CLI

```bash
uv run --frozen python -m lifecycle_mapper benchmark predict --input /path/to/benchmark.xlsx --repository-column B --header-row 1 --output local/benchmark-predictions
uv run --frozen python -m lifecycle_mapper benchmark predict --input /path/to/repositories.csv --output local/csv-predictions
```

CSV columns may use `repository_url`, `github_repository_url` or `repository` (owner/name). JSON lists/manifests and one-URL-per-line text are also supported. The default runs all three modes; use `--mode documentation-only` for the primary method. Predictions, matched evidence, download/analysis errors, immutable snapshots and execution manifests are saved. Acquisition failures are not converted to negative labels. Use a new output directory for each run.

## Single repository and offline replay

```bash
uv run --frozen python -m lifecycle_mapper acquire https://github.com/OWNER/REPO --snapshot local/snapshots/example
uv run --frozen python -m lifecycle_mapper analyze --snapshot local/snapshots/example --mode documentation-only --output local/analysis.json
```

An optional `--ref` selects a commit, branch or tag during acquisition. The ref is resolved once to an immutable commit and blobs are captured by SHA. Replay verifies hashes and uses no GitHub network. `GITHUB_TOKEN` may be set in the shell before the UI/CLI for larger batches; it is not exposed to the browser or saved outputs. Inspected repository code is never executed.

## Approved human comparison

When the original workbook is available, adapt the unverified import mapping to its actual layout and supply exact-workbook/mapping approval:

```bash
uv run --frozen python -m lifecycle_mapper benchmark import original.xlsx --config configs/agreement-final-import.yaml --output local/imports/final-v1
uv run --frozen python -m lifecycle_mapper benchmark run --config configs/benchmark.yaml
```

The first import is candidate without an approval record. The human evaluation config is currently pending and refuses to compute human performance until the real codebook, approved consensus, sampling provenance, revisions and snapshots are present. This does **not** block UI or batch prediction. The original Google Sheet/workbook is never modified.

See [Agreement Final import](docs/agreement_final.md), [development/test and frozen evaluation](docs/evaluation_protocol.md), [methodology](docs/methodology.md), [rule-change review](docs/rule_change_protocol.md) and [limitations](docs/limitations.md).

## Development verification

```bash
mkdir -p local
uv run --frozen ruff check src tests scripts
uv run --frozen ruff format --check src tests scripts
uv run --frozen mypy
uv run --frozen pytest -q --basetemp local/pytest
```

CI also runs browser tests and offline regression fixtures. Historical synthetic artifacts are software checks only; they are not a prerequisite for normal use and are not human benchmark results. Python 3.12.14 and uv 0.12.23 are pinned; `uv.lock` pins all dependencies. Production classification and the local server use the Python standard library.

The upstream repository was audited at `dfb22f9545860a99a57199975dd78a4d9cb80fea`. No upstream code was copied because that inspected tree declares no license. Its evidence concepts informed the independently authored foundation reused by the UI. See [implementation provenance](docs/implementation_provenance.md) and [reproducibility](docs/reproducibility.md). The maintained branch is `main`.
