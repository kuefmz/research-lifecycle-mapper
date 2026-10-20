# Commands for tonight

For the current **software.tar-only metadata evidence audit**, use
[metadata_selection.md](metadata_selection.md). It does not require relation
downloads and does not label unreviewed references as verified paper links.

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

## Reconcile the legacy cohort and show the complete funnel

Save the original 386-candidate list as `data/corpus/legacy_386.txt`, one full GitHub
repository URL per line. Do not include researcher names in filenames or contents.
CSV (a `repository_url` or `github_repository_url` column), JSON, and XLSX are also
supported. For XLSX supply `--legacy-worksheet` and `--legacy-column` explicitly.
The actual deduplicated count is reported, never forced to 386.

```bash
uv run --frozen python -m lifecycle_mapper.funnel \
  --full-extraction data/corpus/openaire \
  --filtered-extraction data/corpus/openaire-experiments \
  --legacy-repositories data/corpus/legacy_386.txt \
  --output data/corpus/funnel
```

Read `data/corpus/funnel/funnel.md`. JSON and CSV versions accompany it. The report
shows software records, descriptions present/missing/nonmatching, selected links,
unique candidates, original cohort, intersection, exclusive sets, union, original
candidates absent from the current dump, and overlap with the annotated benchmark.
`membership.csv` retains flags for each repository. These are overlapping cohorts,
not a claim that the original 386 are a subset of the new 3,211. The union is
available as `data/corpus/funnel/union_repositories.csv` for `corpus run --input`.
Use a new run output directory for that different input.

The original cohort is reported as supplied paper-related candidates, not verified
paper links. Optionally provide `--paper-links data/corpus/paper_links.csv` with
`repository_url,paper_identifier` columns (one relation per row; full GitHub URLs
and nonempty DOI/arXiv/OpenAIRE publication identifiers). These are supplied
bibliographic evidence, not independently verified. Their absence is reported as
unknown, not zero. A software DOI or an experiment mention alone is not proof of
a relationship to a paper. OpenAIRE graph relation archives are separate from
software.tar; reproducing a graph-based publication filter requires the original
relation types, archives and endpoint types. Do not infer that historical rule.

To include checkpointed acquisition/analysis counts, repeat the funnel command
with `--run data/runs/openaire-experiments-main-master`. Multiple `--run` arguments
produce separately labeled sections: requested/pending, checkpointed, acquired,
main/master, complete, partial and failed. Overlapping runs are not added together.
Run manifests and checkpoint hashes are checked; regenerate after the run finishes
for final paper counts. The report may be refreshed in the same output directory.
It never modifies input data, snapshots, labels or predictions. Requested URLs
are normalized; renamed repository aliases are not resolved by this offline step.

Source layout documentation: https://zenodo.org/records/20428976 (relations are
published separately by source entity type and semantics).

Do not update the checkout during an active analysis. Finish that run first;
resume requires an unchanged implementation hash. The reporting module works
offline and does not consume GitHub API quota.

### Eligibility clarification

The collector reports that the original cohort required all four conditions:
OpenAIRE software classification, experimental context in the description or
associated metadata, a GitHub repository, and at least one linked research
publication. Preserve this as the reported historical protocol. Its exact query,
metadata fields, relation semantics and release still need provenance; membership
alone does not reconstruct them.

The new description-only rule is a narrower operationalization of experimental
context. Its 3,211 candidates are before publication linkage, not the final cohort.
When `--paper-links` is supplied, the report adds
`paper_linked_description` and its overlap with the historical cohort, and writes
`paper_linked_description_repositories.csv`. This is the selection output to use
for the four-criterion study after checking the supplied publication evidence.
Without evidence the final eligible count is null/pending, never assumed to equal
3,211 or zero. The union remains an exploratory reconciliation list, not an
eligibility-certified population. The historical 386 are shown alongside the new
funnel; they are not treated as its final stage unless measured overlap supports
that interpretation. Missing evidence in the new file is not evidence that a
historical repository lacked a publication link.

## Apply publication linkage to the experimental-context candidates

This is the fourth eligibility condition in one selection pipeline, not a second
study. Reuse the existing description-selected extraction; do not rerun GitHub
heuristics to determine inclusion. Put the OpenAIRE **product relation** TAR files
from the same release under `data/raw/relations/` (all parts and relevant relation
semantics, e.g. `product_IsRelatedTo_*.tar`, `product_References.tar`,
`product_IsSupplementTo.tar`, `product_Documents.tar`, and citation parts).
The filenames and available parts are listed at
https://zenodo.org/records/20428976. Include all product-to-product relation
archives if the rule is any software-publication relation; supplying just one
semantics archive is an explicitly restricted search, not complete coverage.
No archive is automatically downloaded: relation archives can be very large.

```bash
mkdir -p data/raw/relations
uv run --frozen python -m lifecycle_mapper.publications \
  --candidates data/corpus/openaire-experiments \
  --relations-dir data/raw/relations \
  --source-record https://zenodo.org/records/20428976 \
  --output data/corpus/openaire-experiments-publications
```

No GitHub token is needed. An empty relation directory fails instead of silently
skipping this condition. The output directory must be new. Relations are streamed;
only candidate-matching software/publication edges are retained. Both directions
qualify and original direction/name/archive/member/line are saved. By default any
named relation to a confirmed publication qualifies. If the historical query used
specific semantics, repeat `--relation-name NAME` to restrict them, recording the
actual names rather than assuming `IsRelatedTo` alone reproduces the old query.
Flat current and nested historical endpoint serialization are supported.

Publication endpoints must be explicitly typed `publication`. If the relation
files type them only as `product`/`result`, supply all corresponding publication
entity TAR parts with repeated `--publication-tar data/raw/publication_1.tar`
arguments. Those inputs confirm publication membership by ID; a DOI alone does
not. Unconfirmed endpoints and software IDs without a link in the supplied inputs
are counted separately. Missing archive coverage is not a negative publication
finding. The source-release declaration is recorded alongside every input hash.

Read `data/corpus/openaire-experiments-publications/funnel.md` and `summary.json`.
The latter carries upstream extraction counts and relation scan/exclusion counts.
`publication_links.csv` preserves inclusion evidence and `repositories.csv` is
the final selected repository list. The count is measured, not forced to 386.
The new dump and uncertain historical metadata/relation rules prevent a claim of
bit-for-bit historical reproduction merely because the four criteria are applied.

For measured overlap with the original 386 and annotated 100, place the original
list in `data/corpus/legacy_386.txt` as full GitHub URLs, one per line, and run:

```bash
uv run --frozen python -m lifecycle_mapper.funnel \
  --full-extraction data/corpus/openaire \
  --filtered-extraction data/corpus/openaire-experiments \
  --publication-extraction data/corpus/openaire-experiments-publications \
  --legacy-repositories data/corpus/legacy_386.txt \
  --output data/corpus/funnel
```

Add `--run PATH` to include completed/partial acquisition counts. For analysis of
the final selection use the publications output, not the union reconciliation:

```bash
nohup uv run --frozen python -m lifecycle_mapper.corpus run \
  --input data/corpus/openaire-experiments-publications/repositories.csv \
  --output data/runs/experiment-publication-main-master \
  --workers 2 --transport hybrid \
  > data/runs/experiment-publication-main-master.log 2>&1 &
```

Run only after other API runners finish, with GITHUB_TOKEN exported and data/runs
present. Do not update code underneath an active or resumable analysis. The
collection, eligibility and observed analysis counts belong in a single funnel;
original-cohort overlap is an audit of reproduction, not a separate experiment.
