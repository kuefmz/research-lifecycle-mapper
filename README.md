# Research Lifecycle Mapper

An MSR replication package for detecting evidence of **Collection, Processing, Method,
Experimentation, Evaluation, and Dissemination** in public GitHub repositories.
The only maintained method is **release 1.0**, with 105 rules in
`configs/heuristics/`. The package defaults and repository-root rules are identical
copies of that profile. Historical regression fixtures are not alternative methods.

A positive is detected evidence, not proof of scientific correctness or reproducibility.
A negative means no qualifying evidence was detected in a completed eligible scan;
`null`/`?` means unknown. The annotated 100 were used during development, not held out.

## Install and try the UI

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Git, network access.
From a clone of the anonymous submission repository:

```bash
uv sync --frozen
uv run --frozen python -m lifecycle_mapper ui
```

Open **http://127.0.0.1:8000**, enter a public repository URL, and select Analyze.
The minimal local UI displays all three evidence modes, the commit, and inspectable
JSON evidence. It uses the guarded corpus runner: main, otherwise master; 120 seconds
per repository; 10 MiB per file. It never executes downloaded repository code.
Without a token it uses Git transport. For hybrid transport, set the token **before**
starting the UI (Bash):

```bash
read -rsp 'GitHub token: ' GITHUB_TOKEN
echo
export GITHUB_TOKEN
uv run --frozen python -m lifecycle_mapper ui
```

The token stays in the server environment. Do not commit it. UI runs are saved in ignored
`local/ui/`; `--state-dir` and `--port` are available. Keep this server local.

## Run the annotated benchmark

```bash
uv run --frozen python -m lifecycle_mapper.corpus run \
  --input data/corpus/benchmark_100.txt \
  --expected-repositories 100 \
  --output data/runs/benchmark-100-final \
  --transport hybrid --workers 1 --mode all \
  --max-bytes 10485760 \
  --reference data/final_agreement.csv

uv run --frozen python -m lifecycle_mapper.corpus export \
  --output data/runs/benchmark-100-final \
  --reference data/final_agreement.csv

uv run --frozen python -m lifecycle_mapper.assess \
  --run data/runs/benchmark-100-final \
  --reference data/final_agreement.csv \
  --output results/benchmark-100/assessment
```

Set the token first, as above; alternatively use `--transport git`. Use fresh output
paths for new configurations. Current corpus CLI defaults are two workers and no
file-size cap; the paper commands explicitly use one worker and 10 MiB. The 120-second
per-repository deadline is enforced by the runner.

**Do not pull this cleanup into an ongoing run's checkout.** Implementation fingerprints
change during cleanup; resume ongoing runs from their original checkout. Saved results
remain exportable and assessable without replay. Never rewrite their manifests.

## Package guide

| Path | Purpose |
|---|---|
| `docs/method.md` | Evidence policies, decision semantics, and limitations |
| `docs/rules.md` | Rule schema and exact per-rule specification |
| `docs/data-generation.md` | OpenAIRE source, extraction, funnel, cohort subtraction |
| `docs/results.md` | Result schemas, evaluation, upload and documentation instructions |
| `docs/ui.md` | Local demonstration and troubleshooting |
| `docs/reproduction.md` | Reproduction sequence and checks |
| `docs/submission.md` | Anonymous distribution and remaining release requirements |
| `prompts/` | LLM prompt provenance and space for exact historical prompts |
| `results/` | Documented destinations for final local results; not fabricated outputs |
| `data/` | Human annotations, workbook, repository lists, provenance |
| `configs/heuristics/` | The single final scientific profile |
| `src/lifecycle_mapper/` | Classifier, acquisition, CLI, UI, and saved-run compatibility code |
| `tests/` | Offline regression tests; historical profiles only as test fixtures |
| `scripts/` | Data/cohort helpers, anonymity audit, and release packaging |

See `docs/inventory.md` for retained compatibility components. Synthetic fixtures under `benchmark/` validate software behavior, not human accuracy.
The exact historical LLM prompts have **not** been found in the tracked repository:
`prompts/README.md` explains what must be supplied before reproducing that experiment.
Research run results still need to be copied from the researcher's local computer.

## Validation

```bash
mkdir -p local
uv run --frozen pytest -q --basetemp local/pytest
uv run --frozen ruff check src tests scripts
uv run --frozen mypy
```

Code license: [LICENSE](LICENSE). Annotation terms: [data/LICENSE-annotations.md](data/LICENSE-annotations.md).
Third-party repository contents retain their original licenses. No Zenodo DOI is claimed;
the archived release and its persistent identifier remain a release task.
