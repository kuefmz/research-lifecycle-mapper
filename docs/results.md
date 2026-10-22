# Results: files, interpretation, and local upload

## Destinations

The three paper populations are under `results/benchmark-100/`, `results/corpus-386/`
and `results/corpus-3211/`. See `results/README.md` for included data and pending
original pooled result/evidence exports.
Actual corpus checkpoints remain under `data/runs/<original-run-name>/` so original
relative paths and checksums continue to work. Original assessment directories can
remain under `data/reports/`. These are versionable, not ignored. Large input archives
and transient UI runs are excluded from ordinary Git commits.

Do not relabel historical manifests as v1.0 or edit their hashes. Matching predicates are preserved, but normalized release metadata and rule identifiers
change catalog and implementation fingerprints.
Continue active runs from their original checkout. Validate compatibility before pooling.

## Corpus exports

Run this for each completed run, substituting its actual existing directory:

```bash
uv run --frozen python -m lifecycle_mapper.corpus export --output data/runs/benchmark-100-final --reference data/final_agreement.csv
uv run --frozen python -m lifecycle_mapper.corpus export --output data/runs/corpus-additional
```

| File | Meaning |
|---|---|
| `manifest.json` | Inputs/configuration hashes, rule hash, implementation and source provenance |
| `summary.json` | Attempts, complete/partial/failed totals, REST calls and session timing |
| `predictions.csv` | repository, commit, mode, stage, prediction, scan_complete |
| `repository_status.csv` | Per-repository operational status |
| `documentation_comparison.csv` | Exported documentation/reference comparisons when reference supplied |
| `additional_evidence_candidates.csv` | Evidence candidates requiring inspection, not confirmed omissions |
| `repositories/*/result.json` and `result.sha256` | Saved per-repository decisions and evidence with integrity hash |
| `repositories/*/attempt-*/snapshot/` | Inventories/content required for offline replay |
| Progress/stop diagnostics | Operational exclusions, incomplete scans and timeout causes |

CSV predictions are literal 0/1 or unknown representations from the exporter; do not
coerce empty or unknown values to zero. Evidence and labels are different outputs.
Session wall-time divided by total repositories is not trustworthy throughput after a
resume because checkpoints can be reused. Preserve timing_note and original logs.

## Annotated benchmark evaluation

```bash
uv run --frozen python -m lifecycle_mapper.assess \
 --run data/runs/benchmark-100-final \
 --reference data/final_agreement.csv \
 --output results/benchmark-100/assessment
```

The run paths above are examples. Substitute your actual existing paths; do not rename
completed runs or edit their manifests to match examples.

Use a new assessment output directory. Omit `--replay` to evaluate saved predictions.
`--paper-summary` additionally produces Markdown/LaTeX/JSON paper tables for a fully
attempted annotated run. `--replay --rules-dir PATH` is a different experiment and must
not be presented as the original saved predictions. The assessment reports own-complete
and common-complete cohorts; legacy partition names do not establish a held-out sample.

Per-stage precision/recall/F1 use TP/FP/TN/FN; micro pools six-label decisions, macro
averages stages, label agreement is correct decisions/all evaluated decisions, and
exact match requires all six labels to agree. Exclude incomplete vectors from complete-
cohort accuracy but report coverage and unknowns separately. No full-386 or full-3211
F1 is supported without their human labels.

## Uploading results from the original computer

Copy the original run directories without changing filenames or manifest content. For
a compact review copy include exports, manifests, summaries, result.json/hash pairs,
assessment outputs, and the exact reference. Include snapshots separately if replay is
claimed. Inspect licenses and identifying metadata before anonymous distribution.

After copying, run `python scripts/index_results.py` to inventory artifacts and checksums.
It does not validate scientific compatibility. Document each collection using the template
in `results/README.md`: source run/commit, configuration, dates, denominators, failures,
reference identity, evidence scope, metrics and limitations. Review `git status` before
committing; never add tokens, worker temporary files or the multi-GB software archive.

The researcher-reported latest benchmark had 100 attempts, 95 complete, 3 partial and
2 failed; evaluable mode counts 96/95/95. The supplied original assessment tables are now bundled under
`results/benchmark-100/assessment/`. The notebook verifies restored CSV predictions and
scan-completeness flags against them and reproduces Table 4. Raw acquisition snapshots
and the full 386-repository export remain separate inputs.
