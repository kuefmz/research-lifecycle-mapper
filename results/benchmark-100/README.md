# Annotated 100-repository benchmark results

This folder contains:

- **[workbook/](workbook/README.md): all 10 selected current worksheet CSVs, with a file-by-file index.**
- **[predictions.csv](predictions.csv): consolidated 100-repository heuristic results (1,800 stage decisions), pinned commits and mode completeness.**

- `repositories.txt`: the complete 100-repository input list in its original order; list provenance is in `repository_list_provenance.json`.

- `workbook/`: ten separate source-sheet CSV exports, their mapping/checksums, and conversation references.
- `reproduce_paper.ipynb`: executed notebook for annotation statistics, mode-specific/common-cohort metrics, baselines, and paper consistency checks.
- `reproduce_paper.py`: the same offline calculations as a plain Python command.
- `paper_claims.json`: values transcribed from the attached draft, explicitly separated from computed outputs.
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
- LLM Table 6 from 98/63/99 eligible repositories, including the author-confirmed combined micro-F1 correction to 0.795.

## Original assessment and restored uncertainty

`assessment/` retains the supplied original prediction/completeness tables, metrics,
checksums and cell correction log. The three heuristic CSVs restore 58 zero-filled
unknowns to `?`, plus six existing blanks. Genuine 0/1 values and row order are unchanged.
The notebook verifies every decision against the assessment and uses its scan flags,
reproducing Table 4's **96/95/95** cohorts. The original workbook is not modified.

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
marked unavailable. Table 4 already reproduces using the supplied assessment files. The author confirmed that Table 7 was corrected to the Table 4 heuristic results;
the older heuristic sheets are omitted from the selected exports.

The final labels are a mixed-source adjudicated reference, and all 100 repositories
informed heuristic development. Source-specific disagreement is not independently
validated evidence accuracy. The notebook does not establish held-out generalization.

Original run evidence and status exports are pending transfer; see [UPLOAD.md](../UPLOAD.md).
