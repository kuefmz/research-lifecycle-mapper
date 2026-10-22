# 386-repository corpus-repository collection

Status: repository list available; original run outputs pending upload.

`repositories.txt` contains all 386 unique repositories, in the original
list order. This collection combines the 100 annotated repositories with 286 additional
repositories. Execution batches are provenance, not separate scientific populations.

After verification, this folder will contain pooled `predictions.csv`,
`repository_status.csv`, `evidence.csv`, `summary.json`, and `provenance.json`.
Predictions retain documentation-only, code-only and combined decisions, original
commit IDs, unknowns and scan completeness. Failed attempts remain in the population.
Only the 100 annotated repositories support reference-based evaluation.
See [upload instructions](../UPLOAD.md).

## Aggregate stage results

[stage_counts.csv](stage_counts.csv) contains the supplied complete-corpus positive,
negative and unknown counts for every stage and input mode. Its source and checksum
are in [stage_counts_provenance.json](stage_counts_provenance.json). Positive totals
agree with paper Table 5. These aggregates do not replace the pending original
per-repository prediction/evidence export.

## Standard result files

All three paper corpora use the same output structure:

- `repositories.txt`: complete corpus identities.
- `stage_counts.csv`: 18 mode/stage rows with positive, negative, unknown and total counts, plus percentages using the full corpus denominator.
- `aggregate_summary.json`: machine-readable counts, source scope and limitations.
- `paper_table.tex`: LaTeX positive/negative/unknown table for this corpus.
- `paper_paragraph.tex`: corresponding LaTeX results paragraph.

Generate all three together from the repository root:

```bash
uv run --frozen python scripts/summarize_corpora.py
```

The shared schema does not imply identical source availability or ground-truth coverage;
those distinctions remain documented for each corpus.
