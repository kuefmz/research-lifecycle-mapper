# Reproduction status

Computed from the selected workbook CSVs:

- Independent agreement: 354/600.
- Final positive labels: 384/600.
- Full per-stage metrics, own-cohort and common-cohort baselines are in reproduction.json.

## Evaluation scope and available inputs

- Heuristic evaluation uses original assessment scan-completeness flags; known positives in incomplete scans are retained in CSVs.
- Paper Table 4 uses released predictions and assessment completeness flags (96/95/95 repositories).
- Paper Table 5 requires the original 386-repository predictions export.
- Table 7 summarizes the same predictions and confusion counts as the benchmark evaluation.
- Combined LLM micro-F1 is reported as 0.795 to three decimal places.
- All 100 repositories informed heuristic development; no held-out claim.

Original 100-run data: not supplied
Original 386 predictions: not supplied
