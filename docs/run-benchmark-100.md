# Run all 100 benchmark repositories with notebooks

This run uses the existing development v5 rule profile explicitly. The proposed
v6 catalogue still contains unresolved codebook choices and is not the runtime
classifier. No near-100% accuracy claim is warranted: the previous v5 development
replay had micro-F1 about 0.749 on 72 complete documentation scans. The final
agreement has mixed-source evidence links; mode comparisons measure agreement
with that reference, not independently verified documentation/code accuracy.

The checked input list contains exactly the 100 final-agreement repository URLs.
No sample or shard is used. The count guard fails before acquisition if selection
is not 100. Branch selection remains main, falling back to master only if main is
absent, with files pinned to the selected commit. Never execute downloaded code.

Run from the repository root. Set GITHUB_TOKEN locally if it is not already set:

```bash
git pull --ff-only
uv sync --frozen
read -rsp 'GitHub token: ' GITHUB_TOKEN
export GITHUB_TOKEN
```

Do not paste the token into a command, log or repository file. Then run:

```bash
uv run --frozen python -m lifecycle_mapper.corpus run \
  --input data/corpus/benchmark_100.txt \
  --expected-repositories 100 \
  --output data/runs/benchmark-100-notebooks-v5 \
  --transport hybrid \
  --workers 2 \
  --mode all \
  --rules-dir configs/documentation-development-v5 \
  --max-bytes 2000000

uv run --frozen python -m lifecycle_mapper.corpus export \
  --output data/runs/benchmark-100-notebooks-v5 \
  --reference data/research_lifecycle_benchmark_100_msr27.xlsx

uv run --frozen python -m lifecycle_mapper.assess \
  --run data/runs/benchmark-100-notebooks-v5 \
  --reference data/research_lifecycle_benchmark_100_msr27.xlsx \
  --replay \
  --rules-dir configs/documentation-development-v5 \
  --output data/reports/benchmark-100-notebooks-v5
```

Use a new output directory for this implementation/policy/profile. Old snapshots
cannot acquire notebooks through replay. The 2 MB per-file bound reduces size
exclusions relative to the old 250 KB setting; it is still an explicit coverage
limit, not a guarantee of complete evidence for every repository.

Hybrid transport uses unauthenticated, direct raw HTTP downloads for file contents,
verifies Git blob hashes and sends no bearer token to the raw host. REST is used
for branch/tree acquisition, normally two requests with main present and a
nontruncated tree, plus a fallback request for master or additional subtree reads
when required. Raw traffic has its own throttling constraints. REST primary quota
exhaustion waits for reset; raw downloads honor Retry-After with bounded retries.
Changing Python HTTP libraries alone does not reduce GitHub API usage.

After an interrupted run, rerun the same corpus command with unchanged code and
parameters. To retry recorded partial/failed repositories, append --retry-failed;
complete checkpoints remain cached. Then repeat export and assess. If a stale
.corpus.lock exists after a hard crash, verify no runner is active before removing
that exact lock. Never run two processes against the same output directory.

## Coverage and outputs

summary.json reports finished, complete, partial, failed and
all_repositories_accounted_for. Finished=100 means attempts recorded, not 100
successful complete scans. repository_status.csv contains one record per finished
repository. predictions.csv contains all requested modes/stages even for failed
repositories: a finished 100-repository run produces 1,800 rows (100 x 3 x 6).
Unknown predictions are blank, never fabricated zeros. documentation_comparison.csv
also includes unknown outcomes; human_documentation is a legacy field name for the
mixed-source final-agreement reference. Candidate code additions need review.

Metrics use complete scans and report coverage. They must not be advertised as
100-repository accuracy if some scans are incomplete. Inaccessible repositories,
unsupported notebook syntax/languages and size exclusions remain explicit.

Validation for this change includes a mocked 100-repository run with one
acquisition failure: 100 status records, 1,800 prediction rows, unknown values for
the failed repository, and explicit v5 rule-hash propagation. This is a software
coverage test, not a new live benchmark result.

## Live logging

After every repository finishes, the terminal and progress.log show its URL,
complete/partial/failed state, the six stages in a fixed order, separate
Documentation/Code/Combined predictions, running totals, elapsed repository time
and recorded REST calls. Values: 1=detected; 0=not detected in a complete scan;
?=unknown. Complete cached results are marked as cached checkpoints on resume;
their elapsed time and request counts describe their saved attempt.

Example (illustrative, not an actual benchmark result):

```text
[1/100] https://github.com/example/project | partial
  stages: Collection | Processing | Method | Experimentation | Evaluation | Dissemination
  documentation-only: 1 | 0 | 1 | 1 | 0 | 1  (scan complete)
  code-only: ? | 1 | 1 | ? | 1 | ?  (scan incomplete)
  combined: 1 | 1 | 1 | 1 | 1 | 1  (scan incomplete)
  totals: complete=0 partial=1 failed=0 | repo=12.0s | REST calls=2
```

Unknown values are not silently converted to 0. These are heuristic predictions,
not live correctness/F1 measurements against the reference. Logging adds no
network requests and never prints the token.
