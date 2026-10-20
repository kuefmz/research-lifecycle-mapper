# Extract and analyze the OpenAIRE corpus

## Extract a repository list from the local archive

Run from the maintained repository checkout after git pull --ff-only and uv sync --frozen:

```bash
uv run --frozen python -m lifecycle_mapper.openaire --software-tar /absolute/path/software.tar --source-record https://zenodo.org/records/ACTUAL_RECORD_ID --output local/openaire-corpus
```

Replace ACTUAL_RECORD_ID with the exact release actually downloaded. The archive's SHA-256 is recorded. The older upstream frame used record 12819872; the later supplied link identifies 20428976. Do not assume their counts are equal or force exactly 105,516.

The extractor streams JSONL/gzip members without extracting archive paths, reads only codeRepositoryUrl/coderepositoryurl, validates GitHub URL syntax, normalizes .git/known repository deep links, lowercases identities and deduplicates. Outputs: repositories.txt, repositories.csv, software_links.csv (record/member/line provenance), summary.json with source/output hashes and inclusion counts. It fails on malformed JSON/UTF-8 rather than silently skipping it. Rejected URL values are counted. Valid syntax does not mean a repository exists, remains public, or meets research eligibility; acquisition establishes accessibility. Forks, mirrors and aliases are not deduplicated by content. Different requested URLs resolving to the same canonical repository should be audited before population summaries.

## Run a fresh deterministic pilot

Set GITHUB_TOKEN in your local environment using the existing README instructions; never put the token in an argument or commit it. Then:

```bash
uv run --frozen python -m lifecycle_mapper.corpus run --input local/openaire-corpus/repositories.csv --output local/pilot-200 --sample 200 --workers 2 --transport hybrid
```

The pilot uses deterministic hash selection, independent of predictions. It does not estimate classifier accuracy without human labels. Check summary.json, per-repository timings/complete status, raw-file failures, bytes and file counts. Use fresh-run wall time, not a resumed session, for throughput. A 200-repository pilot does not characterize all heavy-tail behavior.

## Full run and recovery

```bash
uv run --frozen python -m lifecycle_mapper.corpus run --input local/openaire-corpus/repositories.csv --output local/corpus-all --workers 2 --transport hybrid
uv run --frozen python -m lifecycle_mapper.corpus export --output local/corpus-all
```

Repeat the exact run command to resume checksummed completed results. Failed/partial results are retained by default; add --retry-failed for a deliberate retry, which preserves earlier snapshot attempts. A completed acquisition interrupted before analysis is reused at its captured commit. Interrupted acquisition attempts remain separate. If a hard kill leaves .corpus.lock, verify that no runner is active before removing only that stale lock.

A clean interrupt may wait for in-flight requests/tasks to finish. Keep the source/rules/input unchanged during a run. Resume rejects changed source, rules, input, acquisition policy or selected set. Use a new output directory for a new scientific run. The pilot and full run are separate directories and do not automatically share captures.

The runner bounds outstanding tasks to worker count and checkpoints each repository separately; it does not collect all corpus evidence into one giant JSON. Each repository result includes immutable commit, snapshot checksum, timings, eligible-file count, bytes, API calls, explicit errors and mode completeness. Export streams compact CSVs. Full evidence remains in each result.json and captured source files in its snapshot directory. Disk usage can be substantial.

Hybrid mode resolves the default HEAD or supplied ref directly and requests its immutable tree (normally two REST requests). Canonical identity is grounded in the returned commit URL, including renames. It downloads eligible public blobs from commit-pinned raw URLs and verifies their Git blob SHA-1 plus stored SHA-256. No bearer token is sent to the raw host. It never silently switches to mutable default-branch raw URLs or converts failures into six negative labels.

The process-wide REST gate defaults to 0.8 seconds between calls; primary limits and Retry-After are respected with bounded retries. Raw transfers retry transient failures; raw 403/429 marks the remaining eligible files unavailable for that repository after bounded retries. Raw and Git downloads have their own service limits and are not unlimited. This runner is for public repositories. Use authenticated API transport for resources not publicly accessible; do not interpret a hybrid failure as repository disappearance.

Use --transport api to fetch blobs through REST, or --transport git for existing partial-clone acquisition. More workers do not increase a token's quota; start with two. Shards (--shard-index I --shard-count K) partition by identity hash but separate processes do not share a rate gate, so budget aggregate API/raw traffic. Do not multiply workers/processes to evade service limits.

Documentation-only analysis can use --mode documentation-only. Hybrid/API acquisition then downloads documentation only and marks code source-not-requested; code completeness is not claimed. All modes preserve the original classifier and eligibility limits. The multi-mode runner matches documentation and code once, then projects per-mode evidence with byte-equivalent predictions and evidence IDs; it avoids repeated parsing/matching for the combined mode. No detector rules were tuned in this update.

## Compare the 100 documentation labels and review code additions

```bash
uv run --frozen python -m lifecycle_mapper.corpus run --input data/research_lifecycle_benchmark_100_msr27.json --output local/reference-run --transport hybrid --workers 2
uv run --frozen python -m lifecycle_mapper.corpus export --output local/reference-run --reference data/research_lifecycle_benchmark_100_msr27.json
```

documentation_comparison.csv compares ONLY documentation-only predictions with the human documentation reference. additional_evidence_candidates.csv contains source evidence when documentation has no match; unknown documentation is explicitly flagged. These are review candidates, not confirmed omissions or corrected reference labels. The export never changes the reference. The new per-repository corpus layout is separate from the UI's legacy batch results.json format.

## Runtime estimate

For N repositories and F eligible downloadable files per repository, the original API batch uses about N*(3+F) REST calls (plus recursive-tree fallbacks and retries). A standard personal token normally provides 5,000 REST calls/hour; unauthenticated REST is normally 60/hour. See GitHub's official rate-limit documentation.

For N=105,516, quota-scale estimates for the original API batch are:
F=10: about 274 hours (11.4 days); F=50: about 1,118 hours (46.6 days); F=100: about 2,174 hours (90.6 days). These divide requests by hourly quota; initial available budget/reset timing and all non-API costs make actual elapsed time differ.

The hybrid path normally uses 211,032 REST calls for the same N. Dividing by 5,000/hour gives about 42.2 quota-hours. Its default 0.8-second pacing implies about 46.9 hours just for metadata request spacing if every repository needs two calls. Recursive trees, retries, raw download limits/bandwidth, analysis and disk add costs. Thus under two days is not a safe promise with one ordinary token and these defaults.

Planning scenarios, not benchmark predictions: at aggregate sustained 500 repositories/hour, completion takes 8.8 days; at 1,000/hour, 4.4 days; at 2,000/hour, 2.2 days. The default hybrid metadata gate caps ideal sustained throughput near 2,250/hour before other work. Measure your machine/network using the fresh pilot. Budget several days, potentially weeks for a large/heavy corpus; do not promise full-corpus results for the paper before the pilot.

Git transport does not consume the REST quota for its Git operations but remains constrained by server limits, repository size and network/disk/CPU. It is an alternate pilot, not a guaranteed faster full-corpus solution.

Official references:
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- https://github.blog/changelog/2025-05-08-updated-rate-limits-for-unauthenticated-requests/
