# Complete-development verification of frozen v5

The second updated review export contains 65 mismatching repositories. It adds
texts for two previously error-free development cases and drops seven previously
mismatching cases. Shared text and snapshot hashes are unchanged. Combining both
exports supplies all 72 complete development repositories in the earlier comparison.
The frozen v5 replay reproduces the updated file's mismatch stages exactly.
No operational-holdout error file was used, and no new rule changes were made.

| Documentation metric | Baseline | Frozen v5 |
|---|---:|---:|
| Micro F1 | 0.42165242 | 0.74903475 |
| Macro F1 | 0.38150669 | 0.70213799 |
| Micro precision | 0.87058824 | 0.76984127 |
| Micro recall | 0.27819549 | 0.72932331 |
| Per-label accuracy | 0.53009259 | 0.69907407 |
| Exact six-label match | 0.02777778 | 0.09722222 |

Always-positive micro F1 is 0.76217765. Targets and F1-baseline superiority remain
unmet. This is a complete-development result, not the full 91-documentation/100-
repository benchmark result or independent validation. There are 130 mismatched
binary decisions among 432, versus 203 at baseline. The 65-row review export is
not the evaluation denominator: seven correct repositories must remain included.

Reconstruct inputs and replay from the repository root (choose fresh output paths):

```bash
uv run --frozen python scripts/merge_development_reviews.py \
  --original-gzip data/reports/development-v5-inputs/documentation_review_development.jsonl.gz \
  --additional data/reports/development-v5-complete-inputs/additional_documents.jsonl \
  --updated-mismatches data/reports/development-v5-complete-inputs/updated_mismatches.json \
  --output data/reports/development-v5-reconstructed.jsonl
uv run --frozen python scripts/evaluate_documentation_review.py \
  --review data/reports/development-v5-reconstructed.jsonl \
  --comparison data/reports/development-v5-inputs/all_modes_comparison.csv \
  --rules-dir configs/documentation-development-v5 \
  --output data/reports/development-v5-complete-reproduced
```
