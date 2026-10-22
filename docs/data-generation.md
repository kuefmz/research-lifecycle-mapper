# OpenAIRE data generation and cohort provenance

## Source

[OpenAIRE Graph Dataset, Zenodo record 20428976](https://zenodo.org/records/20428976).
Download `software.tar` from that record and place it at **data/raw/software.tar**.
The archive is not bundled and is excluded from ordinary Git commits. Do not substitute
another release without recording it. Researcher-reported source SHA-256:

`c79362d68f9b4095286e97b6dffbdc11ee7af93de003cd5431c82d72ee687717`

Verify locally with `sha256sum data/raw/software.tar`. No relation/product archives are
needed for the description/GitHub extraction. Publication relationships are a separate
question and cannot be established merely from a text mention.

## Extract the full list and experiment-mentioned subset

```bash
mkdir -p data/raw
uv run --frozen python -m lifecycle_mapper.openaire \
 --software-tar data/raw/software.tar \
 --source-record https://zenodo.org/records/20428976 \
 --output data/corpus/openaire

uv run --frozen python -m lifecycle_mapper.openaire \
 --software-tar data/raw/software.tar \
 --source-record https://zenodo.org/records/20428976 \
 --description-experiments \
 --output data/corpus/openaire-experiments
```

Implementation: `src/lifecycle_mapper/openaire.py`. The filter searches description and
descriptions using case-insensitive whole-word `\bexperiments?\b`, excludes missing/empty
descriptions, matches records before repository deduplication, and includes a repository
if any associated record matches. GitHub links receive syntax validation and normalization;
existence, access and allowed branches are checked during acquisition. Outputs include
record-link CSV, deduplicated repository CSV/text and a count/provenance/checksum summary.

Reported funnel for this archive (revalidate generated summary rather than hardcode targets):

| Step | Count | Unit |
|---|---:|---|
| Software records | 730,346 | records |
| Description text present | 412,221 | records |
| Description matches experiment(s) | 11,316 | records |
| Repository field present, all records | 568,255 | records |
| GitHub links, all records | 553,703 | record-repository links |
| Unique GitHub repositories, all records | 432,399 | repositories |
| Matched records with repository field | 3,930 | records |
| GitHub links from matched records | 3,876 | record-repository links |
| Deduplicated matched repositories | 3,211 | repositories |

## Publication-associated collection and annotation sample

`data/corpus/publication_associations.json` preserves the collector-supplied publication-associated collection
and related_to associations. `benchmark_386.txt` is the maintained input list; the
duplicate normalized list was removed after checking identity equivalence. The collector reports software, experimental context,
GitHub and publication-association criteria. The original query has not been exactly
reproduced. Containment in the current 3,211 does not independently verify publications.
The initial 100 annotated repositories are a development reference, not an untouched test.
Do not infer a random sampling procedure without supporting records.

The current lists and received execution log verify containment of the 386 in the
reconstructed 3,211 population. The remainder contains 2,825 unique identities.
Direct comparison with the original full extraction input remains pending.
Reproduce subtraction (also writes normalization audit and input hashes):

```bash
uv run --frozen python scripts/select_repositories.py \
 --input data/corpus/benchmark_386.txt --exclude data/corpus/benchmark_100.txt \
 --output data/corpus/benchmark_386_remaining.txt

uv run --frozen python scripts/select_repositories.py \
 --input data/corpus/openaire-experiments/repositories.txt \
 --exclude data/corpus/benchmark_386.txt \
 --output data/corpus/corpus-3211-remaining.txt
```

Existing output files are not overwritten. Check counts 286 and 2,825; do not force them
if a new release or normalization changes membership. Deep-link normalization is not live
rename/alias resolution. A failed prior attempt still counts as an excluded identity.

## Analyze new cohorts

Set GITHUB_TOKEN as in the README, or substitute Git transport. Example for 286:

```bash
uv run --frozen python -m lifecycle_mapper.corpus run \
 --input data/corpus/benchmark_386_remaining.txt --expected-repositories 286 \
 --output data/runs/benchmark-386-remaining-final \
 --transport hybrid --workers 1 --mode all --max-bytes 10485760
```

For the additional collection use input `data/corpus/corpus-3211-remaining.txt`, expected
count 2825 and a fresh output `data/runs/openaire-additional-final`. Export with corpus
export, omitting a human reference for unlabeled repositories. Do not compute full-cohort
F1 from only the 100 annotations. Keep the final rule profile and acquisition configuration
compatible before combining results.

The full collection is experiment-mentioned software, not representative of all research
software. The publication-associated subset may enrich dissemination evidence.
OpenAIRE publication links are not automatic positive repository-level dissemination labels.


## Generate the selection funnel

[Figure sources and editable outputs](../figures/README.md) record the exact count units,
reported extraction provenance and source archive hash. Generate SVG, PDF and PNG:

```bash
uv run --frozen --with matplotlib==3.10.8 python scripts/create_openaire_funnel.py
```

To additionally validate independently regenerated extraction summaries before plotting:

```bash
uv run --frozen --with matplotlib==3.10.8 python scripts/create_openaire_funnel.py \
  --full-summary data/corpus/openaire/summary.json \
  --filtered-summary data/corpus/openaire-experiments/summary.json
```

The description/GitHub branches select in parallel, then intersect at 3,876 links and
deduplicate to 3,211 repositories. The supplied 386 publication-associated repositories
are contained in that population. Their original publication-selection query is not
bundled or reconstructed, and cannot be reproduced from software descriptions alone.
Containment verification and publication-selection reproduction are different checks.
The 100 annotated, 286 additional and 2,825 remaining repositories define the execution
partition. A graph-level publication association is not an automatic positive
repository-level Dissemination label.
