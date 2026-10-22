# Annotated 100-repository benchmark results

This folder contains:

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
- LLM Table 6 from 98/63/99 eligible repositories, with the combined micro-F1 rounding discrepancy reported.

## What still needs original run data

The latest worksheet exports do not encode the original scan-completeness flags used
for the paper's heuristic Table 4. Their binary-complete counts are 99/100/99, not the
paper's 96/95/95. The notebook computes the source tables as supplied and flags the
mismatch; it does not force the paper's numbers or treat missing values as zero.

To reproduce the original scan-complete evaluation and Table 5's 386-repository counts:

```bash
uv run --frozen python results/benchmark-100/reproduce_paper.py \
  --run /path/to/the/original-100-run \
  --corpus-predictions /path/to/the/original-386-predictions.csv
```

The first option reads original checksum-bound result.json files, requiring exactly the
100 reference identities. It performs no acquisition or reanalysis. The second requires
386 distinct repository identities and all 18 exported decisions per repository.
Without these optional inputs, the corresponding original-run tables are explicitly
marked unavailable. Table 7's heuristic rows still contain superseded scores and need
editorial correction; the older heuristic sheets are omitted from the selected exports.

The final labels are a mixed-source adjudicated reference, and all 100 repositories
informed heuristic development. Source-specific disagreement is not independently
validated evidence accuracy. The notebook does not establish held-out generalization.
