# Evaluation protocol

The current experiment is development reference agreement on 100 annotated repositories.
All 100 informed rule development. No deterministic operational split creates a blinded
holdout retroactively. See method.md and results.md for the actual evaluation semantics.

Use the jointly adjudicated `data/final_agreement.csv`, keeping independent reviewer
labels separate. Treat the final reference as mixed-source unless a source-specific audit
establishes otherwise. Report per-mode and common-complete denominators, coverage, micro-
and macro-F1, exact match, stage metrics, and matching-cohort always-positive/negative
baselines. Incomplete vectors do not become all-negative. Inspect disagreements as
candidates; they are not automatically correct source-only discoveries.

The compatibility `protocol.py` module supports older formal split/freeze manifests, but
those controls do not establish that this study had an independent held-out evaluation.
No human approvals, annotation provenance or sampling history may be fabricated.
