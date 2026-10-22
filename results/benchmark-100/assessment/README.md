# Benchmark assessment records

`all_modes_comparison.csv` contains 1,800 repository/stage decisions, pinned commit IDs,
reference labels and per-mode scan-completeness flags. Empty prediction cells are
unknown; the worksheet exports display unknown heuristic decisions as `?`.

`repository_summary.csv` contains repository/mode statuses and positive, negative and
unknown stages. `mode_summary.csv` and `per_stage_metrics.csv` contain aggregate
verification targets. The notebook validates predictions and reference labels against
these assessment records. SHA-256 checksums are recorded in `manifest.json`.

All 100 repositories informed rule development. Operational grouping fields do not
constitute independent held-out validation.
