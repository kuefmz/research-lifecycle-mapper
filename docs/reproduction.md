# Reproduction sequence

1. Clone the anonymous release, install Python 3.12/Git/uv, run `uv sync --frozen`.
2. Verify rule identities: `uv run --frozen python scripts/verify_final_profile.py`.
3. Create `local/`, then run `uv run --frozen pytest -q --basetemp local/pytest`.
4. Try the local UI (`python -m lifecycle_mapper ui` through uv) or run the README corpus command.
5. Follow data-generation.md to regenerate the OpenAIRE candidate list from software.tar.
6. Use explicit file cap/workers and fresh run directories; preserve manifests and failures.
7. Export saved runs and assess only the annotated reference cohort as described in results.md.
8. Compare manifests before pooling, checking catalog, implementation, branch, modes, caps,
   timeout, input identity and acquisition policies. Same profile name alone is insufficient.
9. Record dependencies, source revision, data hashes and any deviations alongside outputs.

Offline replay requires the original snapshots, not predictions.csv alone. Live reruns
may differ because repositories evolve or become unavailable. Do not overwrite original
reference labels or claim an untouched holdout from the old operational split.

## Legacy compatibility

The scientific matching predicates are unchanged. Catalog version metadata and some
rule identifiers were normalized for the single release. Root and packaged defaults
are identical to configs/heuristics. Historical schema
versions, importers and regression fixtures remain readable. This is a software packaging
change: implementation hashes change, so resuming an old run from this checkout is rejected.
Retain the original checkout for running/resuming existing work.
