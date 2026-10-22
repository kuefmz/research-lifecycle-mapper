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
| `data/` | Human annotations, source workbook, repository lists, and source provenance |
| `results/` | Destinations for final research exports and experiment documentation |
| `prompts/` | Exact LLM-prompt provenance requirements and upload location |
| `docs/` | Method specification, data generation, result schemas, and submission instructions |
| `scripts/` | Cohort subtraction, rule verification, result indexing, and packaging |
| `tests/` | Tests for the maintained workflow and artificial input fixtures |

Read [the method](docs/method.md), [exact rules](docs/rules.md),
[OpenAIRE extraction instructions](docs/data-generation.md), and
[result documentation](docs/results.md).

**Release contents:** the deterministic method and annotated input data are included.
Original research run exports and exact historical LLM prompts/configuration still need
to be uploaded to their documented locations. Placeholder directories do not establish
that those experiments are reproducible. The LLM materials are separate from the fully
local heuristic implementation; see [prompts/README.md](prompts/README.md).

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
