# Annotated 100-repository benchmark results

This folder contains:

- **[workbook/](workbook/README.md): all 10 selected current worksheet CSVs, with a file-by-file index.**
- **[predictions.csv](predictions.csv): consolidated 100-repository heuristic results (1,800 stage decisions), pinned commits and mode completeness.**

- `repositories.txt`: the complete 100-repository input list in its original order; list provenance is in `repository_list_provenance.json`.

- `workbook/`: ten separate source-sheet CSV exports, their mapping/checksums, and conversation references.
- `reproduce_paper.ipynb`: executed notebook for annotation statistics, mode-specific/common-cohort metrics, baselines, and paper consistency checks.
- `reproduce_paper.py`: the same offline calculations as a plain Python command.
- `paper_claims.json`: reported paper values, explicitly separated from computed outputs.
- `analysis/`: computed tables, full-precision JSON and a reproduction-status summary.

## Run

From the repository root:

```bash
uv sync --frozen
uv run --frozen python results/benchmark-100/reproduce_paper.py
```

Calculations need only Python's standard library and this package. To interact with the
notebook, open it in an existing Jupyter installation, or use the optional convenience
command (Jupyter is not needed by the analysis script):

```bash
uv run --frozen --with jupyterlab jupyter lab results/benchmark-100/reproduce_paper.ipynb
```

## What is reproduced

- Table 3 initial agreement (354/600), disagreements (246/600), final label totals (384 positive/216 negative), and 12 all-positive repositories.
- The selected latest workbook predictions, with complete-vector metrics, confusion counts, common-cohort comparisons and always-positive/negative baselines.
- LLM Table 6 from 98/63/99 eligible repositories, with combined micro-F1 of 0.795.

## Predictions and evaluation

`assessment/` contains repository/stage predictions, independent per-mode scan-completeness
flags, aggregate metrics and integrity checksums. The notebook checks the released
heuristic tables against these records. Evaluation includes **96 documentation,
95 code and 95 combined repositories**. A prediction of `?` is unknown, not negative;
known positive findings can be retained even when a scan is incomplete.

## Optional raw run and 386-repository data

To reproduce the original scan-complete evaluation and Table 5's 386-repository counts:

```bash
uv run --frozen python results/benchmark-100/reproduce_paper.py \
  --run /path/to/the/original-100-run \
  --corpus-predictions /path/to/the/original-386-predictions.csv
```

The first option reads original checksum-bound result.json files, requiring exactly the
100 reference identities. It performs no acquisition or reanalysis. The second requires
386 distinct repository identities and all 18 exported decisions per repository.
Without these optional inputs, raw-run verification and the 386-repository table are
marked unavailable. Table 4 already reproduces using the supplied assessment files. Table 7 summarizes the same benchmark predictions and confusion counts.

The final labels are a mixed-source adjudicated reference, and all 100 repositories
informed heuristic development. Source-specific disagreement is not independently
validated evidence accuracy. The notebook does not establish held-out generalization.

Original run evidence and status exports are pending transfer; see [UPLOAD.md](../UPLOAD.md).

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
