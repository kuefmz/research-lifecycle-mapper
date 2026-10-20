# Corpus execution verification — 2026-10-20

The update adds an independently authored streaming OpenAIRE extractor and resumable, bounded corpus runner; it does not copy upstream code or change detector rules. The human reference scope is documentation-only; source evidence candidates remain subject to human review.

## Live smoke test

Three convenience repositories, public unauthenticated acquisition, two metadata REST calls each, commit-pinned raw files verified against Git blob hashes. All requested modes completed.

| Repository | Eligible files | Acquisition seconds | Original three-pass analysis seconds | Total seconds |
| --- | ---: | ---: | ---: | ---: |
| kjetilk/doe-sparql | 12 | 3.05 | 0.05 | 3.10 |
| maidens/ACC-2016 | 6 | 2.41 | 0.02 | 2.43 |
| sisl/GrammarExpts.jl | 210 | 65.67 | 8.67 | 74.34 |

Exact commits/timings are recorded in corpus_smoke_20261020.json. This is a transport smoke test, not a representative pilot, full-corpus result or authenticated-token benchmark. Raw-network costs vary sharply even among these examples.

Replaying the captured GrammarExpts.jl snapshot on the same machine: independent three-mode analysis 8.45 seconds; one-pass mode projection 2.87 seconds. Outputs compared equal as complete Python result structures, including evidence IDs/run IDs, errors, counts and unknown/completeness semantics. One snapshot and one timed comparison do not establish a general speedup.

## Automated checks

The final verification passes Ruff lint/format, mypy, 185 pytest tests (two optional browser tests skipped), and deterministic synthetic replay against the V3 reference. Tests cover streaming extraction/provenance, malformed or hostile URLs, deduplication, raw hash verification/token isolation, direct HEAD/canonical rename handling, documentation-only acquisition, checkpoint resume and configuration mismatch, API cooldown, failures without six-negative output, source-evidence review separation and exact single-pass/multi-pass parity.

Synthetic-v2's committed reference predates the current V3 evidence schema and already failed the existing CI reference check on the unmodified base commit. This was reproduced in a pristine detached checkout. Synthetic-v3 is a new reference generated with the unmodified base implementation, preserving V1/V2 archives. The workflow now compares against V3, and current outputs are checked against that baseline. These are software regression fixtures, never human evaluation results.

Browser tests remain optional and were not run for this backend/documentation change. The local software.tar, 386 attached data and uploaded manuscript remain unavailable in the host runtime. No full corpus execution or attachment/manuscript edit is claimed.
