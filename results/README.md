# Final research results

Selected workbook exports, their executed reproduction notebook, and exact LLM user prompts
are now included under benchmark-100/ and ../prompts/. Original per-repository corpus
runs still need uploading. Destinations:

- benchmark-100/: selected source-sheet CSVs, metrics, paper checks and executed notebook.
- corpus-386/: pooled detections from the 100 and additional 286, after compatibility checks.
- openaire-3211/: complete 3,211-repository population, pooling 100 + 286 + 2,825 after verification.
- llm/: reserved for additional original inference metadata; the three workbook LLM tables are under benchmark-100/workbook/.

For each populated folder add a README with:

1. Status (pending/provisional/final), source run paths and source commit.
2. Inputs/cohort IDs, archive/reference/catalog/implementation hashes.
3. Branch/acquisition policy, modes, limits, transport, workers and execution dates.
4. Attempted, finished, complete, partial and failed totals; per-mode denominators.
5. File inventory/schema and how to regenerate each export/table.
6. Reported metrics/baselines or stage positive/negative/unknown counts.
7. Known exclusions, errors, license/anonymization treatment and interpretation limits.

Keep original data/runs checkpoints intact. See docs/results.md for commands and schemas.
`python scripts/index_results.py` creates an inventory with content checksums after upload.

The complete 100- and 386-repository lists are already available as `repositories.txt`
in their respective folders. The full 3,211 list is reconstructed from the disjoint 386 list and 2,825-run log;
its source-input comparison and detailed result upload remain pending.
Follow [UPLOAD.md](UPLOAD.md) to transfer only relevant original result files.
Execution subsets will not be presented as independent result collections.
