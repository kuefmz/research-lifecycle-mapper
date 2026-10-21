# Replay and inspect all 100 benchmark repositories with development rules v5

The requested 0.80 documentation / 0.90 combined F1 targets have not been achieved.
The supplied development texts support substantive recall improvements, but some
labels lack explicit support in the captured documentation under the current
concept definitions. Missing support can reflect historical drift, incomplete
captures or different human coding interpretations; it is not evidence that the
human label is wrong. Do not invent matches, change labels or add identity rules.

After active API acquisitions finish, update the maintained checkout and replay:

```bash
git pull --ff-only
uv sync --frozen
uv run --frozen python -m lifecycle_mapper.assess \
  --run data/runs/benchmark-main-master \
  --reference data/research_lifecycle_benchmark_100_msr27.xlsx \
  --replay \
  --rules-dir configs/documentation-development-v5 \
  --output data/reports/benchmark-development-v5-all100 \
  --review-documents
```

No token, API requests or downloads are needed. This reads saved immutable
captures and does not overwrite source results, labels or baseline reports.
Use a new assessment output directory. Prediction records cover all 100 reference
repositories, all three modes and all six stages, with missing decisions explicitly
unknown. Scored denominators remain complete scans; do not claim N=100 accuracy
merely because the report contains 100 rows in each mode.

Read mode_summary.csv for metrics and repository_summary.csv for per-repository
positive, negative and unknown stages in each mode. documentation_diagnostics.json
now lists unavailable documentation file paths/reasons, so the nine incomplete
documentation cases can be diagnosed before any targeted reacquisition. Per-mode
and common-complete-cohort metrics remain separate. Combined means union, not
averaging. Code/combined agreement with documentation labels is cross-scope.

## Development evidence and reproducibility

The 70 complete development error-review texts and source assessment exports are
preserved in data/reports/development-v5-inputs. The large JSONL is gzip-compressed
losslessly; input_manifest.json records original hashes and notes the identical
duplicate upload. The operational holdout error file was not read to choose or
revise rules. Reports under development-v5-final-text-replay compare only the
provided development subset with baseline and constant predictors. The initial
v5 text-replay report is retained too; its candidate differs from the final v5
and is labelled superseded. No new result is an independently blinded evaluation.

To reproduce the final development text replay:

```bash
gzip -dk data/reports/development-v5-inputs/documentation_review_development.jsonl.gz
uv run --frozen python scripts/evaluate_documentation_review.py \
  --review data/reports/development-v5-inputs/documentation_review_development.jsonl \
  --comparison data/reports/development-v5-inputs/all_modes_comparison.csv \
  --rules-dir configs/documentation-development-v5 \
  --output data/reports/development-v5-local-reproduction
```

Text replay scores only supplied complete development documents. Full assess
replay additionally verifies content hashes and uses all actual original captures.
The operational 80/20 split was made after prior aggregate inspection and is not
an independent generalization test. Baseline/proxy differences should be reviewed
against an explicit human codebook before choosing a final rule set for the paper.
