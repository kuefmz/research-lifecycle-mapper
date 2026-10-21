# Run all 100 benchmark repositories with notebooks

This run uses consolidated development v5.4, incorporating the 61-repository development audit, operational exclusions and scientific workflow rules. See the profile README and exact rule catalogue. The proposed
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
echo
export GITHUB_TOKEN
```

Do not paste the token into a command, log or repository file. Then run:

```bash
uv run --frozen python -m lifecycle_mapper.corpus run \
  --input data/corpus/benchmark_100.txt \
  --expected-repositories 100 \
  --reference data/final_agreement.csv \
  --output data/runs/benchmark-100-v54-paper-check \
  --transport hybrid \
  --workers 1 \
  --mode all \
  --rules-dir configs/consolidated-development-v5.4 \
  --max-bytes 10485760

uv run --frozen python -m lifecycle_mapper.corpus export \
  --output data/runs/benchmark-100-v54-paper-check \
  --reference data/final_agreement.csv

uv run --frozen python -m lifecycle_mapper.assess \
  --run data/runs/benchmark-100-v54-paper-check \
  --reference data/final_agreement.csv \
  --rules-dir configs/consolidated-development-v5.4 \
  --output data/reports/benchmark-100-v54-paper-check \
  --paper-summary
```

Use a new output directory for this implementation/policy/profile. Old snapshots
cannot acquire notebooks through replay. This command applies a 10 MiB per-file cap and a 120-second repository wall-clock deadline. There is no file-count or total-download-size cap. The CLI size default remains 0 (unlimited); the benchmark command sets 10485760 explicitly.

Hybrid transport uses unauthenticated, direct raw HTTP downloads for file contents,
verifies Git blob hashes and sends no bearer token to the raw host. REST is used
for branch/tree acquisition, normally two requests with main present and a
nontruncated tree, plus a fallback request for master or additional subtree reads
when required. Raw traffic has its own throttling constraints. REST primary quota
exhaustion waits for reset and raw downloads honor Retry-After, but those waits
count toward the same two-minute repository deadline. A quota wait can therefore
time out; it must not be reported as a large-repository failure. Each isolated
worker paces its own REST calls; two workers remain the recommended setting.
Changing Python HTTP libraries alone does not reduce GitHub API usage.

After an interrupted run, rerun the same corpus command with unchanged code and
parameters. To retry recorded partial/failed repositories, append --retry-failed;
complete checkpoints remain cached. Then repeat export and assess. Assessment uses the saved predictions, avoiding
a second unbounded replay of large repositories. If a stale
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
notebook decoding failures and acquisition errors remain explicit. Recognized programming files receive portable lexical scanning even without a native parser. Scan completeness describes heuristic coverage, not semantic understanding.

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


## Two-minute hard stop and paper-ready stop records

Each repository runs in a separate subprocess. The 120-second wall-clock budget
covers worker startup, branch/tree acquisition, downloads, integrity checking,
notebook parsing, matching, result writing and rate-limit waits. On timeout the
parent sends SIGKILL to the worker process group on POSIX, including Git child
processes, and continues the corpus. It is not a thread Future timeout. Queue time
before a worker starts does not consume the repository budget. Small parent-side
checkpoint/log cleanup follows termination. This implementation is tested on Linux.

No repository code, notebook kernel, hooks or build commands are executed. Data
contents and the previously specified vendor/fixture exclusions remain outside
the evidence scope; these are methodological exclusions, not size/count limits.
The bounded evidence windows remain rule semantics and do not truncate the scan
to the first part of a file. The old first-6,000-character document-context check
is removed; context detection now examines the whole document.

Timeout artifacts:

- repositories/<id>/stop.json: timeout/error, elapsed seconds, exit status, and
  last atomic heartbeat containing phase, current file, counts and byte totals.
- repositories/<id>/heartbeat.json: last phase and counters, also available while
  a repository is running. captured_bytes counts completely captured files, not
  bytes in a partially downloaded in-flight file.
- repositories/<id>/worker.log: worker notices such as API quota cooldowns.
- stopped_repositories.json: final-attempt unsuccessful records across the run.
- summary.json: timed_out count, in addition to complete/partial/failed totals.
- repository_status.csv after export: stop phase, file counts, captured bytes,
  largest eligible file size, current file, last error and elapsed time.

A timeout records the observed phase and workload. Do not assert that file count
or size caused it solely because either is large. Examples: rate-limit-wait is
an observed quota wait; acquisition plus a large in-flight file is a download
timeout with the file size recorded; analysis means the detector had not finished.
Missing inventory or counters remain unknown rather than zero-valued evidence.
No timeout is converted to six negative labels; it exports unknown predictions.
The v5.1 profile scans recognized programming languages using native detectors where available plus portable token-based rules. Native parser gaps become explicit source warnings when portable scanning succeeds; acquisition and decoding failures still affect completeness.

The larger run should use this exact same policy if compared with the benchmark.
Report the timeout budget, selection counts, complete/partial/failed coverage and
stop-phase breakdown in the paper. Historical attempts are retained; the aggregate
stopped_repositories.json describes the latest checkpoint for each repository.

Other CLI acquisition helpers now also default to no size cap, but the hard
process deadline is enforced by corpus run. Use that entry point for the benchmark.

## Legacy Python and acquisition error diagnostics

Some historical repositories use Python 2 syntax. The pinned Python 3.12 runtime
now tries a syntax-only compatibility parse after native parsing fails. Only
print/except/raise/number/inequality/exec/repr syntax fixers are enabled. Conversion
must preserve physical line counts; original source bytes, line excerpts and
hashes are retained, and code evidence records its syntax policy. No repository
code is executed and no import/API rewriting occurs. Remaining unsupported or malformed syntax is retained as a source warning under v5.1 when portable scanning succeeds, or a parse error under older profiles.

Heartbeat writes are atomic, serialized and use unique temporary names. An OSError
from monitoring is nonfatal and retained as telemetry_write_error in the state;
monitoring failure must not classify a repository as inaccessible. Repository
errors retain sanitized module/function/line locations and OS errno/file basename,
without full local paths or exception messages containing secrets.

A FileNotFoundError is an acquisition/local I/O failure, not a timeout or size
exclusion. Its class alone is insufficient to infer the underlying cause. A
python-parse-error is a detector compatibility gap, not a download failure and
not evidence that the repository lacks research activities. Report these failure
categories separately from the two-minute deadline in the paper.

## Display author agreement without rerunning

The optional run --reference workbook displays final_agreement labels in each result block. These labels are loaded only by the parent logger and never passed into the classifier. Missing reference repositories have no agreement row. The reference has mixed-source evidence and is not independently validated code-only ground truth.

For an existing run, after processing finishes, display saved checkpoints alongside agreement without acquisition or heuristic replay:

```bash
uv run --frozen python -m lifecycle_mapper.corpus logs \
  --output data/runs/benchmark-100-v54-paper-check \
  --reference data/final_agreement.csv
```

This also writes agreement.log in the run directory. It does not change predictions or manifests. Finish an active run before pulling implementation changes; implementation fingerprints intentionally prevent resuming a run with changed classifier code.

The benchmark input follows the supplied final-agreement row order. Corpus selection preserves input order. Use one worker for terminal completion blocks in exactly that order; concurrent workers finish at different times. Saved `corpus logs` output follows reference row order.

## Dense TXT folders (eligibility policy 4)

Before content acquisition, count regular files whose suffix is .txt (case-insensitive) within each immediate Git directory. If the count is greater than five, exclude all .txt files in that directory with inventory reason `txt-folder-more-than-5`. Exactly five remain eligible under the other rules. Nested directories are counted independently; the root is a directory too. README.txt has no exemption in a dense folder; README.md, code and notebooks are unaffected. Symlinks/submodules do not contribute to the count. Both Git and API/raw acquisition apply the same inventory policy. Replay recomputes the directory counts from the manifest; previous eligibility policies retain their original behavior.

This is an explicit user-selected data-content proxy, not proof that excluded TXT files are datasets. It can exclude real documentation and must be reported as a selection limitation. It does not exclude data using other suffixes, such as .f files mistaken for Fortran. The current benchmark uses a 120-second repository deadline and an explicit 10 MiB per-file cap. Use a fresh output directory, e.g. `data/runs/benchmark-100-v53-txt-policy4`; earlier checkpoints cannot be resumed across the changed implementation/policy. The v5.3 heuristic profile is unchanged.

## Legacy text decoding (eligibility policy 5)

Eligible text is decoded using strict UTF-8 first. If that fails, the decoder tries strict Windows-1252, rejects undefined bytes and binary/control-character content, and checks an exact round trip to the original bytes. No errors=ignore/replace mode is used. Windows-1252 is an explicitly recorded fallback hypothesis, not universal encoding detection. The observed integraseModel/minimalModel/makeFig3.m failure contains CP1252 curly quotes in a comment; this source now completes the code scan in a targeted replay.

Snapshots retain original bytes, byte counts, Git blob identity and SHA-256. Each captured file records text_encoding and decoding_policy; replay uses the versioned decoder and verifies recorded provenance. Older snapshot policies retain strict UTF-8 behavior. Non-UTF-8 fallback files are recorded in each applicable mode's text_decodings field and counted in progress logs. Source excerpts use decoded characters with physical lines preserved. Binary/unsupported text remains an explicit acquisition failure, never fabricated negative evidence.

Policy 5 includes the previously requested TXT-folder exclusion unchanged. It does not resolve dataset files using programming-language suffixes. For a fresh benchmark use output `data/runs/benchmark-100-v53-text-fixes` with `--rules-dir configs/consolidated-development-v5.4`; heuristic rules and reference labels are unchanged. Do not mix checkpoints across policy/implementation versions.

Current execution budget: 120 seconds per repository, including acquisition, analysis and quota waits. The benchmark commands use a 10 MiB per-file cap. Start a fresh output directory after this change; the manifest records the deadline. Timeout diagnostics and unknown-value reporting remain unchanged.

## Consolidated v5.4 freeze

Finish the existing baseline run before pulling changes. Use a fresh `data/runs/benchmark-100-v54-paper-check` output. Exact rules and the paired README-only development check are documented in the profile README and `data/reports/consolidated-v54-development-audit.json`. This is a development freeze, not a guarantee of target F1. Both run and reference order remain unchanged.

## Final complete-log check and printable paper results

Acquisition policy 7 adds exclusion of known bundled jquery/jquery-version/jquery-ui JavaScript basenames; non-README TXT artifacts under data/datasets/experimental_data/test_data/testdata/fixtures directories; and programming files in the already-excluded software-test path class before download/tokenization. This avoids the observed unminified-jQuery, experimental-result-text and test_data.py work. The TXT density rule still applies outside data directories; README.txt remains eligible unless its immediate folder exceeds five TXT files. These policies are explicit selection proxies, not guaranteed semantic file classification. Older policy-6 snapshots retain their original behavior. The v5.4 matching rules themselves are unchanged.

The completed uploaded baseline is preserved in data/reports/completed-baseline-progress.log and completed-baseline-log-audit.json. Its omitted first header was restored only after exact matching against the earlier supplied first-block body; no predictions or labels were changed. All 600 printed reference labels were checked against final_agreement.csv. The baseline completed 91 repositories, with two partial and seven timed out; its documentation/combined micro-F1 were 0.6860/0.7316 on 91 complete scans. These are baseline results, not a measured full v5.4 result.

The final assess command's --paper-summary flag prints Markdown tables and a draft results paragraph, and saves paper/paper_summary.md, paper/paper_modes.tex and paper/paper_summary.json under the assessment directory. It includes complete/partial/failed coverage, per-mode denominators, a common complete cohort, micro/macro F1, precision/recall, label agreement, exact matches, documentation-stage metrics, always-positive baselines, resource limits and hashes. Unknowns never become negative predictions. Code modes remain reference agreement, not independently validated code accuracy. Both the table and paragraph disclose development-set status.

--rules-dir without --replay now validates the saved catalogue hash; it does not rerun classification. A mismatched profile fails explicitly. Paper printing rejects unfinished runs, stale assessment/run-manifest combinations, and offline-replayed assessments. A finished run can still contain failed/partial repositories. Existing assessments can be printed without acquisition or matching:

```bash
uv run --frozen python -m lifecycle_mapper.paper_summary \
  --run data/runs/benchmark-100-v54-paper-check \
  --assessment data/reports/benchmark-100-v54-paper-check \
  --output data/reports/benchmark-100-v54-paper-check/paper
```

Preserve the completed baseline. Use a new run and assessment directory for the final check, since the acquisition implementation changed. Do not claim target F1 before the new run is measured.
