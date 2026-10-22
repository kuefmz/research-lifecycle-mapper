# Original benchmark assessment

These four original CSVs were supplied with the request to restore missing predictions.
`all_modes_comparison.csv` contains 1,800 decisions, pinned commit IDs and independent
scan-completeness flags. Empty prediction cells are unknown, never zero.
`repository_summary.csv` retains the 300 repository/mode statuses and known/unknown stages.
`mode_summary.csv` and `per_stage_metrics.csv` are the supplied aggregate verification targets.
The reproduction script checks all decisions against the corrected seven-column CSVs
and checks the adjudicated reference against the assessment reference.

`uncertainty_corrections.csv` records 58 zero-to-question-mark changes and six blank-to-
question-mark changes. Original source-export hashes remain in the workbook manifest.
`manifest.json` binds these files by SHA-256. Historical operational partitions do not
constitute held-out validation: all 100 repositories informed heuristic development.
