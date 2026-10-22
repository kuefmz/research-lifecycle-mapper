# Research Lifecycle Mapper

**Replication artifact for the submitted MSR 2027 paper, _Beyond Artefact Types:
Mining Research Lifecycle Evidence from GitHub Repositories_.**

This artifact contains the implementation and materials used to make the paper's
heuristic analyses reproducible. It detects evidence of six research lifecycle stages
in public GitHub repositories: **Collection, Processing, Method, Experimentation,
Evaluation, and Dissemination**.

The tool reports documentation, source-code, and combined findings separately. Each
positive finding is linked to its matching rule and repository evidence. It inspects
repository content without executing it. Detected evidence is not a certification of
scientific correctness or reproducibility.

## How the heuristics work

The classifier applies **105 deterministic, contextual rules** to eligible repository
files. Documentation and source code are analyzed separately; notebook Markdown cells
count as documentation, code cells as source, and stored outputs are ignored. Data-file
contents, generated assets, and excluded dependencies do not provide lifecycle evidence.

Rules look for combinations of research activities, relevant objects, and surrounding
context. Documentation rules examine prose and workflow instructions; code rules examine
operations using syntax analysis or lexical matching, depending on the language.
For example, a research-data transformation can support Processing, while a scientific
metric calculation can support Evaluation. A generic keyword, import, or filename alone
is insufficient. Matching rules record their identifiers, excerpts, and file locations.

A stage is positive when qualifying evidence is found. Combined findings are the union
of documentation and code findings. A negative requires a completed eligible scan;
otherwise an undetected stage remains unknown. This approach identifies observable
evidence without executing the repository or establishing that the research is reproducible.

See [the method specification](docs/method.md) and
[the complete rule catalog](docs/rules.md) for exact conditions and limitations.

## Installation

Requirements: **Python 3.12**, **Git**, and **[uv](https://docs.astral.sh/uv/)**.
Network access is needed for live repository acquisition. Offline analysis requires
previously captured snapshots.

Clone the anonymous artifact repository using its supplied clone URL, change into the
checkout, and install the locked dependencies:

```bash
uv sync --frozen
uv run --frozen python -m lifecycle_mapper --help
```

The artifact has one maintained heuristic profile, `configs/heuristics/`. Its 105 rules
are also packaged as the installed default. No model service is needed for heuristics.

## Quick start: local UI

```bash
uv run --frozen python -m lifecycle_mapper ui
```

Open **http://127.0.0.1:8000**, enter a public GitHub repository URL, and click **Analyze**.
The UI displays all six stages for documentation, code, and combined evidence, with
inspectable evidence and a downloadable JSON result. Runs are saved under `local/ui/`.
Use `--port 8001` or `--state-dir local/demo` to change the port or storage directory.

Without a token, the UI uses Git transport. To use hybrid acquisition, set a GitHub token
in the server environment **before** starting the UI. In Bash:

```bash
read -rsp 'GitHub token: ' GITHUB_TOKEN
echo
export GITHUB_TOKEN
uv run --frozen python -m lifecycle_mapper ui
```

Do not commit the token. It is not entered through the browser or included in exports.
The server binds to the local loopback interface and is intended for local use.

## Batch analysis

Create a text file with one root GitHub repository URL per line. For example:

```text
https://github.com/owner/repository
```

Run all three evidence modes:

```bash
uv run --frozen python -m lifecycle_mapper.corpus run \
  --input repositories.txt \
  --output data/runs/example \
  --transport git --workers 1 --mode all \
  --max-bytes 10485760

uv run --frozen python -m lifecycle_mapper.corpus export \
  --output data/runs/example
```

For token-enabled raw-content/REST acquisition, set `GITHUB_TOKEN` as above and use
`--transport hybrid`. The paper settings use **one worker**, a **10 MiB per-file cap**,
and a **120-second repository deadline**. The UI uses these settings automatically.
The corpus CLI defaults to two workers and an unlimited file size, so specify the paper
settings explicitly. Acquisition uses `main`, falling back to `master` only, and records
the resolved commit. Other branches are outside the study's acquisition policy.

Use a fresh output directory for changed inputs or settings. Resume only from the same
implementation checkout and configuration. Do not update a checkout during an active run.

## Reproduce the annotated benchmark

The supplied 100-repository reference is a development benchmark: its repositories were
used while developing the heuristics. It is not an independent held-out evaluation.

```bash
uv run --frozen python -m lifecycle_mapper.corpus run \
  --input data/corpus/benchmark_100.txt --expected-repositories 100 \
  --output data/runs/benchmark-100 \
  --transport git --workers 1 --mode all --max-bytes 10485760 \
  --reference data/final_agreement.csv

uv run --frozen python -m lifecycle_mapper.corpus export \
  --output data/runs/benchmark-100 --reference data/final_agreement.csv

uv run --frozen python -m lifecycle_mapper.assess \
  --run data/runs/benchmark-100 --reference data/final_agreement.csv \
  --output results/benchmark-100/assessment --paper-summary
```

Assessment without `--replay` evaluates saved predictions and makes no GitHub requests.
It reports mode-specific and common-complete cohorts, reference-agreement metrics,
baselines, and coverage. The paper summary also produces Markdown, LaTeX, and JSON.
Reference labels are comparison metadata, never classifier inputs.

## Recalculate the worksheet results

**All 10 current Excel-sheet CSV exports are indexed [here](results/benchmark-100/workbook/README.md#where-are-the-worksheet-csvs).** They comprise four reviewer/agreement tables, three LLM tables and three heuristic tables. A separate consolidated `predictions.csv` is derived from the original assessment, not an eleventh worksheet.

The selected source sheets are available as ten CSV files in
[`results/benchmark-100/workbook/`](results/benchmark-100/workbook/).
Run the executed [reproduction notebook](results/benchmark-100/reproduce_paper.ipynb)
or its plain Python equivalent:

```bash
uv run --frozen python results/benchmark-100/reproduce_paper.py
```

This reproduces annotation statistics, benchmark metrics, confusion counts and
baselines from the released CSVs. Heuristic evaluation uses per-mode scan-completeness
flags, independently of known positive findings. See [benchmark documentation](results/benchmark-100/README.md)
for evaluation cohorts and optional original-run verification.
The three original LLM user prompts and shared-conversation references are included
under [`prompts/`](prompts/).

## Data source and selection funnel

The source is the [OpenAIRE Graph Dataset, release 11.1.1](https://zenodo.org/records/20428976).
The extraction streams `software.tar`, selects descriptions mentioning whole-word
“experiment” or “experiments”, normalizes GitHub repository URLs, and deduplicates them.
The reported intersection has 3,876 record-repository links and **3,211 repositories**.
The supplied **386 publication-associated repositories** are contained in this population;
**100** form the annotated development benchmark. The original publication-selection
query is unavailable, so containment does not establish an exactly reproduced query.

![OpenAIRE selection funnel](figures/openaire_funnel.png)

[Extraction and provenance](docs/data-generation.md) explain count units, archive hashes
and commands. [Figure sources](figures/README.md) generate editable SVG, PDF and PNG:

```bash
uv run --frozen --with matplotlib==3.10.8 python scripts/create_openaire_funnel.py
```

## Results overview

On the 100-repository development benchmark, combined documentation and code heuristics
achieved **0.757 micro-F1**, compared with **0.702** for documentation and **0.414**
for code alone. Their respective eligible cohorts were 95, 96 and 95 repositories.
The LLM results were **0.829**, **0.791** and **0.795** micro-F1 for documentation,
code and combined input, on 98, 63 and 99 repositories. These are agreement scores
against the adjudicated reference on different eligible cohorts, not a controlled
same-cohort ranking or held-out performance: all 100 repositories informed development.

For the 386-repository corpus, the paper reports more combined evidence for
Experimentation (247 repositories) and Dissemination (226) than Collection (33).
These are detected-evidence counts, not validated full-corpus accuracy. Selection
for publication association may enrich dissemination evidence.

The full OpenAIRE collection contains **3,211 repositories**. Results are organized
only by the three paper populations: `benchmark-100`, `corpus-386`, and `corpus-3211`.
The benchmark predictions and evaluation are included. Full 3,211-corpus stage aggregates are included: Dissemination and Experimentation
have the largest combined positive counts (2,024 and 2,007). Complete pooled
per-repository evidence files still await original uploads; aggregate reproduction
is distinguished from exact classifier replay.
See [detailed results](results/README.md).

## Outputs and interpretation

| Output | Contents |
|---|---|
| `predictions.csv` | Repository, commit, mode, stage, decision, and scan completeness |
| `repository_status.csv` | Per-repository completion and failure status |
| `manifest.json` | Inputs, rule/configuration hashes, and implementation provenance |
| `summary.json` | Completion totals, session time, and REST call counts |
| `repositories/*/result.json` | Decisions and supporting evidence |
| `repositories/*/attempt-*/snapshot/` | Captured inputs required for offline replay |

**1** means qualifying evidence was detected. **0** means no qualifying evidence was
detected in a completed eligible scan. **Unknown** (`null`, `?`, or an empty exported
prediction) means the scan cannot support a negative conclusion. Never convert unknowns
to zero. Combined findings use the logical union of documentation and code evidence.

## Artifact contents

| Directory | Purpose |
|---|---|
| `src/` | Final classifier, acquisition, corpus runner, evaluation, and minimal UI |
| `configs/heuristics/` | Final rules, exact catalog, and checksums |
| `data/` | Human annotation CSVs, repository inputs, and source provenance |
| `results/` | Destinations for final research exports and experiment documentation |
| `prompts/` | Exact LLM-prompt provenance requirements and upload location |
| `docs/` | Method, annotation questions, data generation, result schemas, submission, and audit report |
| `figures/` | Editable selection funnel, count provenance, and PDF/PNG exports |
| `scripts/` | Cohort subtraction, rule verification, result indexing, and packaging |
| `tests/` | Tests for the maintained workflow and artificial input fixtures |

Read [the method](docs/method.md), [detailed rule guide](docs/rule-guide.md), [exact rules](docs/rules.md),
[OpenAIRE extraction instructions](docs/data-generation.md), and
[result documentation](docs/results.md).

**Release contents:** the deterministic method and annotated input data are included.
Selected workbook results and exact LLM user prompts are included. Original
per-repository research runs, the 386-repository export, and complete LLM inference
configuration remain to be supplied. The notebook reports which paper tables are
reproducible from the available data; see [prompts/README.md](prompts/README.md).

## Verification

```bash
mkdir -p local
uv run --frozen python scripts/verify_final_profile.py
uv run --frozen pytest -q --basetemp local/pytest
uv run --frozen ruff check src tests scripts
uv run --frozen mypy
```

Tests use artificial captured inputs and do not require a token. Browser smoke tests are
optional and enabled in CI after installing Chromium with Playwright.

## Anonymous review and licensing

Submission-facing documentation uses no author names or identifying repository links.
The working repository's host account and Git history remain identifying. Follow
[anonymous packaging instructions](docs/submission.md) to create and inspect a history-free
distribution before uploading it to the anonymous review service. Do not expose the
working repository URL in the manuscript.

Code: [MIT license](LICENSE). Annotations: [data terms](data/LICENSE-annotations.md).
Third-party source contents and the bundled language catalog retain their own licenses.
The archival DOI will be added when the preserved release is deposited; none is claimed here.

See [submission instructions](docs/submission.md) for the history-free review package.
