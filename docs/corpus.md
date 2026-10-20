# Corpus extraction and execution

Use [run_tonight.md](run_tonight.md) for complete runnable commands saving inputs, snapshots, predictions, evidence, logs and review exports under versionable data/ directories.

The local archive extractor streams JSONL/gzip records without extracting archive paths. It reads only codeRepositoryUrl/coderepositoryurl, validates GitHub repository URL syntax, normalizes known deep links and .git suffixes, deduplicates identities, and records source/output hashes and record-to-repository provenance. Syntax validation does not establish accessibility or research eligibility. The output count is measured from the exact archive, not forced to 105,516.

Hybrid acquisition resolves the actual main branch, or master only when main is absent. It records selected_branch, branch_policy=main-then-master-v1 and the immutable commit. It normally uses two REST requests for main or three for master fallback, plus extra calls for truncated tree recovery/retries. Eligible public files are downloaded from commit-pinned raw URLs, verified against Git blob hashes, and stored with SHA-256 checksums. No token is sent to the raw host. Raw and Git downloads still have service limits.

The runner bounds outstanding tasks and checkpoints each repository independently. Repeat the exact command to resume completed results. Inputs, implementation, rules, branch policy and selection must match. Use a new directory for a different scientific run. Failed/partial results are preserved by default; --retry-failed makes deliberate retries. An interrupted completed acquisition is replayed at its captured commit. Old-policy snapshots cannot be silently reused by the new corpus runner.

All requested evidence modes are computed in one source-matching pass, then projected to byte-equivalent per-mode results. Eligibility and classifier rules are unchanged. Documentation-only acquisition can avoid code downloads when --mode documentation-only is selected. Unsupported languages/artifacts remain explicitly limited; no claim is made that all repository files are analyzed semantically.

After exporting a reference run, summarize documentation_comparison.csv with python -m lifecycle_mapper.summarize. It excludes incomplete documentation scans, reports evaluated N/coverage, per-stage metrics, constant baselines and repository-level bootstrap intervals. The scope is an exploratory documentation-reference comparison. Code discoveries remain separate human-review candidates; bootstrap intervals do not remove development bias.

At a standard 5,000-request/hour token allowance and 105,516 accessible repositories, metadata consumes approximately 42–63 quota-hours depending on main/master selection. Default 0.8-second pacing implies approximately 47–70 hours before downloads, code analysis, disk and retries. Actual execution can take days or longer; use a fresh deterministic pilot, not a resumed session or the three convenience smoke tests, to estimate throughput. Run one live API process at a time unless aggregate quotas and traffic are explicitly coordinated.

The old batch UI results format and the new per-repository corpus layout are distinct. Full source/evidence stays in result.json and snapshot directories; compact exports are streamed. Keep the snapshots for offline replay. Inspect alias/rename duplicates before population summaries.

References: GitHub REST rate limits and the official update to anonymous raw/Git download limits are cited in run and verification documentation. The upstream 105,516 frame used Zenodo record 12819872; a later supplied release was 20428976. Record the release actually downloaded and its hash.
