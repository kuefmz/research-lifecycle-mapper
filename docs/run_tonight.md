# Commands for tonight

Run from the maintained main checkout after updating it. Use one live API runner at a time: different processes do not share the quota gate.

## Setup

```bash
git pull --ff-only
uv sync --frozen
mkdir -p data/corpus data/runs
read -rsp "GitHub token: " GITHUB_TOKEN
export GITHUB_TOKEN
```

The token stays in the local process environment. Never add it to a file or Git.

## Start the 100-repository benchmark first

```bash
nohup uv run --frozen python -m lifecycle_mapper.corpus run \
  --input data/research_lifecycle_benchmark_100_msr27.json \
  --output data/runs/benchmark-main-master \
  --workers 2 --transport hybrid \
  > data/runs/benchmark-main-master.log 2>&1 &
```

Write the paper while this runs. Check progress from another terminal:

```bash
tail -f data/runs/benchmark-main-master.log
```

Stopping tail does not stop the runner. When the runner finishes, export documentation mismatches and separate source-evidence candidates:

```bash
uv run --frozen python -m lifecycle_mapper.corpus export \
  --output data/runs/benchmark-main-master \
  --reference data/research_lifecycle_benchmark_100_msr27.json
```

Then generate primary documentation metrics, constant baselines and bootstrap intervals:

```bash
uv run --frozen python -m lifecycle_mapper.summarize \
  --run data/runs/benchmark-main-master --expected-repositories 100
```

Repeat the exact run command to resume completed checkpoints. Add --retry-failed only for deliberate retries. Keep implementation/rules/input fixed; use a new directory after changing any of them. Captures use main, otherwise master, resolved to an immutable commit. No other branch or tag is substituted.

## Build the larger corpus while the benchmark runs

Extraction is local and consumes no GitHub requests. Enter the actual archive path and the exact Zenodo release actually downloaded:

```bash
read -r -p "Path to software.tar: " SOFTWARE_TAR
read -r -p "Exact Zenodo record URL: " OPENAIRE_RECORD
uv run --frozen python -m lifecycle_mapper.openaire \
  --software-tar "$SOFTWARE_TAR" \
  --source-record "$OPENAIRE_RECORD" \
  --output data/corpus/openaire
```

The list size is measured, not forced to 105,516. Do not infer the release ID from the desired repository count.

## Pilot after the benchmark finishes

```bash
uv run --frozen python -m lifecycle_mapper.corpus run \
  --input data/corpus/openaire/repositories.csv \
  --output data/runs/pilot-200-main-master \
  --sample 200 --workers 2 --transport hybrid
```

Check fresh-run wall time, completion rate, unavailable branches/files, acquisition bytes and code coverage. The normal hybrid path uses two REST calls for main and three when master fallback is needed; truncated-tree recovery and retries add requests. At 105,516 repositories, metadata pacing alone is approximately 47–70 hours with the default 0.8-second interval, before downloads/analysis. A full run is not promised to finish before the deadline.

## Start the full run if the pilot supports it

```bash
nohup uv run --frozen python -m lifecycle_mapper.corpus run \
  --input data/corpus/openaire/repositories.csv \
  --output data/runs/corpus-main-master \
  --workers 2 --transport hybrid \
  > data/runs/corpus-main-master.log 2>&1 &
```

After completion:

```bash
uv run --frozen python -m lifecycle_mapper.corpus export \
  --output data/runs/corpus-main-master
```

## Preserve generated data in this repository

All outputs above are under versionable data/ paths. Keep snapshots for replay. Commit completed checkpoints periodically after inspecting the changes; results should describe completed or explicitly partial runs.

```bash
git status --short
git add data .gitattributes
git commit -m "Preserve analysis inputs and checkpointed results"
git push origin main
```

If retaining the large original archive here too, install Git LFS, then:

```bash
git lfs install
mkdir -p data/raw
cp "$SOFTWARE_TAR" data/raw/software.tar
git add .gitattributes data/raw/software.tar
git commit -m "Preserve source archive through Git LFS"
git push origin main
```

The .gitattributes file already selects raw TAR archives for LFS. Verify that the anonymous mirror actually serves LFS-backed files before depending on those downloads for reviewers. A source URL/checksum is still required.

See writing_tonight.md for the writing schedule and data_availability.md for truthful DOI wording.

## Optional experiment-mentioned corpus

Keep the full extraction unchanged. To select OpenAIRE software descriptions that
mention the whole word `experiment` or `experiments` (case-insensitive), run:

```bash
uv run --frozen python -m lifecycle_mapper.openaire \
  --software-tar data/raw/software.tar \
  --source-record https://zenodo.org/records/20428976 \
  --description-experiments \
  --output data/corpus/openaire-experiments
```

Use the exact source record for your archive. The output directory must be new.
This streams the local archive and does not use a GitHub token. Selection reads
`description`/`descriptions` strings, lists, or explicit text/value wrappers;
missing/empty descriptions are excluded. Titles, repository READMEs and heuristic
predictions are not selection inputs. Matching happens before repository
deduplication: any matching software record includes its linked repositories.
`summary.json` records the selection rule, counts and hashes. A zero-match result
is valid; inspect its counts before starting acquisition. This corpus represents
experiment-mentioned software, not all research software. Do not apply this
selection to the independently annotated accuracy benchmark.

After checking the count, and after any other API runner has finished:

```bash
nohup uv run --frozen python -m lifecycle_mapper.corpus run \
  --input data/corpus/openaire-experiments/repositories.csv \
  --output data/runs/openaire-experiments-main-master \
  --workers 2 --transport hybrid \
  > data/runs/openaire-experiments-main-master.log 2>&1 &
```

Create `data/runs` first if it does not exist. Keep the `main`, otherwise `master`,
branch policy. Repeat the run command to resume; do not overwrite extraction or
mix differently selected inputs in one run directory.
