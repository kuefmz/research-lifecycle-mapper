# Reproduction status

Computed from the selected workbook CSVs:

- Independent agreement: 354/600.
- Final positive labels: 384/600.
- Full per-stage metrics, own-cohort and common-cohort baselines are in reproduction.json.

## Material differences from the draft

- Workbook CSV binary completeness does not establish runtime scan completeness.
- Paper Table 4 requires original result.json files to reconstruct the 96/95/95 scan-complete cohorts.
- Paper Table 5 requires the original 386-repository predictions export.
- Paper Table 7 retains superseded heuristic values and is inconsistent with Table 4.
- The combined LLM micro-F1 rounds to 0.795; the paper prints 0.794.
- All 100 repositories informed heuristic development; no held-out claim.

Original 100-run data: not supplied
Original 386 predictions: not supplied
