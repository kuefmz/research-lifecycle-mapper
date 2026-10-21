# Separate evidence modes and honest documentation evaluation

The existing corpus runner already computes documentation-only, code-only and
combined predictions with --mode all (also the default). Combined is the union
of documentation/code evidence, not an average of scores. The old summarize
command evaluates documentation only. Its printed precision, recall and F1 are
not accuracy. final_agreement remains the documentation-only human reference.

Run this offline command on the completed corpus captures to report all modes
without changing the saved predictions or calling GitHub:

```bash
uv run --frozen python -m lifecycle_mapper.assess \
  --run data/runs/benchmark-main-master \
  --reference data/research_lifecycle_benchmark_100_msr27.xlsx \
  --output data/reports/benchmark-baseline-modes \
  --review-documents
```

For candidate v4 documentation wording, replay the SAME pinned snapshots:

```bash
uv run --frozen python -m lifecycle_mapper.assess \
  --run data/runs/benchmark-main-master \
  --reference data/research_lifecycle_benchmark_100_msr27.xlsx \
  --replay \
  --rules-dir configs/documentation-candidate-v4 \
  --output data/reports/benchmark-candidate-v4-modes \
  --review-documents
```

Each assessment requires a new output directory. Snapshots, source results and
human labels remain unchanged. No GitHub token is needed. An old run can be
assessed after updating the implementation; live resume guards are unaffected.
Snapshot integrity and saved result checksums are verified before replay.
The default production catalog is preserved; v4 is an opt-in candidate whose
empirical benefit is not established. It adds synthetic/raw data generation,
research-data preparation/augmentation/splitting, statistical/neural model
fitting, ablation/sensitivity experiments, predictive metric computation, and
scientific result plotting wording. Local project scope and existing exclusions
are retained. No benchmark identity, labels or unique README phrases were used.
The profile has synthetic positive/negative tests; that is not a benchmark result.

Outputs:

- mode_summary.csv: separate mode coverage, per-label accuracy, exact six-stage
  match, precision, recall and F1. Code/combined reference comparisons are labelled
  cross-scope diagnostics, not validated code-ground-truth accuracy.
- per_stage_metrics.csv: stage-specific TP/FP/TN/FN and accuracy/precision/recall/F1.
- all_modes_comparison.csv: every observed repository/mode/stage, including partials.
- all_modes_metrics.json: metrics per complete-mode population and the common
  complete intersection (fairer paired mode comparison), constant baselines,
  input/catalog/checkpoint hashes, and deterministic operational review partitions.
- documentation_errors_development.csv: development-only FP/FN with accepted and
  excluded evidence. False negatives have no fabricated positive evidence.
- documentation_review_development.jsonl: captured documentation for development
  mismatches, if --review-documents is used. No source-code text enters this file.
- documentation_diagnostics.json: per-repository documentation completeness and
  excluded-evidence counts. Incomplete scans are excluded from accuracy metrics.

Per-label accuracy counts correct binary stage decisions across N*6 labels.
Exact-match accuracy requires all six labels correct for a repository. Neither
is precision or F1. A >90% target is an empirical goal, not a guaranteed property
of a heuristic. Always show recall, F1, baselines and coverage beside accuracy;
never force predictions to human labels or turn unknown scans into true negatives.
The 80/20 hash partition supports development error review only; after previous
aggregate inspection its remaining subset cannot be claimed as a blinded test.
No generalization claim follows from tuning/retesting these same 100 repositories.
Human codebook definitions and real development errors are required for further
rule changes; preserve baseline and unfavorable candidate results.

For the newer development-error-informed v5 candidate and explicit all-reference
repository coverage, see [development_v5.md](development_v5.md). Neither candidate
has achieved the requested accuracy/F1 targets. Keep the constant baselines in
view; a high-positive-label cohort can yield substantial F1 from always-positive
predictions without detecting any lifecycle evidence.
