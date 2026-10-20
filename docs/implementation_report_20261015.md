# Research Lifecycle Mapper: implementation and measured comparison

Historical measurements/audit: retain the source version and denominators below. For current jointly adjudicated documentation reference status and source/code interpretation, see [2026-10-20 annotation status](annotation_status_20261020.md). No historical scores have been relabeled as new measurements.

Run date: 2026-10-15 UTC. Reference: the user-approved `final_agreement` worksheet. These measurements concern detectable repository evidence, not whether research activities occurred or whether results are valid or reproducible.

## Completed implementation

- Verified final-sheet import (A:G, no separate row-ID column), strict binary validation, case-insensitive repository deduplication, checksummed provenance, reference audit and observed comparison CLI.
- Preserved the V1/V2 catalogs and added 18 general V3 rules across all six stages. Documentation requires activity/object and repository scope; implementation uses operation/context conjunctions. Python statements/functions are bounded; R, Julia, MATLAB and shell use conservative lexical masking.
- Stable occurrence and analysis IDs, exact LF/CRLF physical line references (Unicode paragraph separators do not shift GitHub anchors), original excerpts, catalog/rule versions, all matching rule attributions, per-source counts, excluded-candidate exports and unknown absent labels for incomplete scans.
- One-row-per-repository dashboard with mode selection, reference comparison, mismatch/count/name sorting and filters; six-stage detail summary, file breakdown and full evidence table with source badges and commit-pinned links. Saved-run history, JSON result import, single-URL/ref analysis and offline replay remain supported.
- Backend-only token support, sanitized authentication/rate-limit failures, bounded transient retries, efficient recursive-tree acquisition with fallback walking, and optional public Git transport in CLI/UI. Documentation includes Bash and PowerShell token setup.

## Human reference audit

The connected [benchmark spreadsheet](https://docs.google.com/spreadsheets/d/1LZvDotVmgFIGUGCA8x8UD75cqVTNtlB1iWPX0Z6TV3M/edit) was exported read-only. `final_agreement` has header row 1, repository URLs in A2:A101 and six labels in B2:G101. Strict parsing verified 100 unique repositories and 600 binary labels, with no missing final labels or duplicate canonical identifiers. The source workbook was not modified. Notes/legend cells outside A:G are not label inputs.

| Stage | Positive | Negative | Prevalence |
|---|---:|---:|---:|
| Collection | 36 | 64 | 36% |
| Processing | 44 | 56 | 44% |
| Method | 71 | 29 | 71% |
| Experimentation | 88 | 12 | 88% |
| Evaluation | 66 | 34 | 66% |
| Dissemination | 79 | 21 | 79% |

Label cardinality is 3.84 positive stages per repository; 12 repositories have all six and 0 have none.

Co-occurrence below counts repositories positive for both stages (diagonal = prevalence count).

| Stage | Collection | Processing | Method | Experimentation | Evaluation | Dissemination |
|---|---:|---:|---:|---:|---:|---:|
| Collection | 36 | 22 | 30 | 29 | 31 | 29 |
| Processing | 22 | 44 | 38 | 39 | 35 | 33 |
| Method | 30 | 38 | 71 | 64 | 50 | 53 |
| Experimentation | 29 | 39 | 64 | 88 | 59 | 69 |
| Evaluation | 31 | 35 | 50 | 59 | 66 | 54 |
| Dissemination | 29 | 33 | 53 | 69 | 54 | 79 |

### The 246 versus 247 discrepancy

The two independent annotator sheets contain **599 valid binary pairs: 353 agreements and 246 disagreements**, plus one missing Method annotation. The missing cell is D61 in the second annotator sheet (`Hoja 10` in the XLSX export; Jenifer in the live spreadsheet), for `michael135/count-vector-paper-experiments`. The first annotation is 0; the second is blank. The `agreement` sheet marks this pair as 1 (agreement).

Thus 247 arises if blank-versus-0 is counted as a disagreement; 246 counts only binary disagreements. The manuscript Table 2 reports 246 disagreements and 354 agreements over 600 decisions, reproducing the agreement-sheet treatment of the blank. The defensible observed result is 246/599 = 41.0684% disagreement on valid pairs, with one separately reported missing pair. Neither an agreement nor a disagreement can be inferred for that missing independent annotation. No source cell or consensus label was changed.

| Stage | Valid pairs | Agreements | Disagreements | Missing | Cohen kappa (valid pairs) |
|---|---:|---:|---:|---:|---:|
| Collection | 100 | 53 | 47 | 0 | 0.2066 |
| Processing | 100 | 55 | 45 | 0 | 0.1393 |
| Method | 99 | 52 | 47 | 1 | 0.0651 |
| Experimentation | 100 | 72 | 28 | 0 | 0.1255 |
| Evaluation | 100 | 53 | 47 | 0 | 0.1051 |
| Dissemination | 100 | 68 | 32 | 0 | 0.1757 |

The XLSX export truncates/renames some long sheet names. Annotator sheets were grounded by live metadata/order and verified headers/repository sets, not guessed from a truncated filename. The reproducible audit joins by repository identity.

## Baseline, protocol and model selection

The original classifier at `5e8b89e043db13ea9e0f8c5c4af9d18cfb78bd29` was executed on all 98 captured repositories in all three modes. It produced zero positive labels. The retained baseline catalogs, run through the updated engine, were verified to reproduce all 294 original label vectors and scan-completeness statuses exactly. A pure text-segmentation cache was used for the original execution; no original matching logic/rules were changed.

The repository-level 80/20 split was fixed before rule changes: sort SHA256(`rlm-msr27-20261015-v1:` + casefold(repository)), assign the lowest 20 hashes to held-out and the rest to development. The exact split is versioned under `benchmark/versions/`. There was one development mismatch review/refinement round on the initially acquired development subset. It removed command/path keyword coincidences and isolated algorithm-word matches, and generalized conversion and associated-paper wording. External implementation delegation, indirect descriptions and ambiguous human paper labels remain limitations; gold labels were not changed to improve scores.

Rules were frozen before held-out comparison. No held-out mismatch inspection drove further rule changes. The complete final-label table was available in the conversation, so **this is an operational held-out split, not an independently blinded or unbiased evaluation**. A later physical-line correctness fix was driven solely by a synthetic Unicode/CRLF test; final measurements below use that corrected engine and the same frozen catalog. The baseline and candidate use identical captured inputs and per-mode completeness policies. Full-benchmark metrics below are exploratory.

## Acquisition coverage

All 100 repositories were attempted. **98 have immutable snapshots; two remain acquisition failures** (`ciaranm/cp2015-subgraph-isomorphism`, `taochen/all-versus-one`). These are transport/inventory-budget failures, not evidence of six negative stages. The Git attempt captured 89; bounded API recovery captured nine more (two with a 16-request limit, seven with a four-request limit, prioritizing README). Those recovery snapshots often remain partial. Git subprocesses had 180-second per-command limits; no GitHub token was available in this environment. Recovery request budgets were execution constraints, not classifier features or the default application API policy.

The snapshot inventories contain 54,962 entries: 3,453 captured eligible files, 2,566 unavailable eligible files and 48,943 excluded entries. Unavailable reasons: UnicodeDecodeError: 14, recovery-request-budget-exhausted: 2,158, size-limit: 394. Code analysis errors: python-parse-error: 119.

Complete-case metrics exclude incomplete/failed repositories independently per mode; N and coverage are essential parts of every result. A complete scan means complete under the size/eligibility/detector policy, not complete knowledge of the repository’s research. Captured-evidence exploratory metrics include partial scans and treat unmatched stages as absent observations for that sensitivity analysis only; UI/JSON predictions remain unknown where appropriate.

## Measured results

Baseline macro/micro F1 is 0 in every nonempty cohort because it predicts no positives. Baseline accuracy can still be nonzero because it predicts negatives; all baseline per-stage values are retained in the machine-readable results.

| Partition | Mode | Complete N | Population | Macro P | Macro R | Macro F1 | Micro F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| development | documentation-only | 70 | 80 | 0.8708 | 0.2829 | 0.3965 | 0.4594 |
| development | code-only | 49 | 80 | 0.8000 | 0.0942 | 0.1644 | 0.1895 |
| development | combined | 47 | 80 | 0.8123 | 0.3059 | 0.4185 | 0.5106 |
| held_out | documentation-only | 18 | 20 | 0.7333 | 0.2536 | 0.3521 | 0.3800 |
| held_out | code-only | 13 | 20 | 0.8333 | 0.1818 | 0.2920 | 0.3188 |
| held_out | combined | 13 | 20 | 0.9583 | 0.4296 | 0.5660 | 0.5783 |
| full_exploratory | documentation-only | 88 | 100 | 0.8817 | 0.2771 | 0.3931 | 0.4420 |
| full_exploratory | code-only | 62 | 100 | 0.8125 | 0.1160 | 0.1990 | 0.2239 |
| full_exploratory | combined | 60 | 100 | 0.8707 | 0.3437 | 0.4706 | 0.5283 |

Full exploratory benchmark, complete cases only: per-stage confusion counts and accuracy. Cohorts differ by mode, so these tables do not establish a causal benefit of adding code.

### documentation-only

| Stage | TP | FP | TN | FN | Precision | Recall | F1 | Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Collection | 8 | 5 | 52 | 23 | 0.6154 | 0.2581 | 0.3636 | 0.6818 |
| Processing | 9 | 0 | 48 | 31 | 1.0000 | 0.2250 | 0.3673 | 0.6477 |
| Method | 11 | 3 | 20 | 54 | 0.7857 | 0.1692 | 0.2785 | 0.3523 |
| Experimentation | 30 | 0 | 9 | 49 | 1.0000 | 0.3797 | 0.5505 | 0.4432 |
| Evaluation | 3 | 0 | 29 | 56 | 1.0000 | 0.0508 | 0.0968 | 0.3636 |
| Dissemination | 40 | 5 | 14 | 29 | 0.8889 | 0.5797 | 0.7018 | 0.6136 |

### code-only

| Stage | TP | FP | TN | FN | Precision | Recall | F1 | Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Collection | 0 | 0 | 45 | 17 | 0.0000 | 0.0000 | 0.0000 | 0.7258 |
| Processing | 4 | 0 | 37 | 21 | 1.0000 | 0.1600 | 0.2759 | 0.6613 |
| Method | 7 | 1 | 19 | 35 | 0.8750 | 0.1667 | 0.2800 | 0.4194 |
| Experimentation | 4 | 0 | 5 | 53 | 1.0000 | 0.0702 | 0.1311 | 0.1452 |
| Evaluation | 3 | 0 | 24 | 35 | 1.0000 | 0.0789 | 0.1463 | 0.4355 |
| Dissemination | 11 | 0 | 12 | 39 | 1.0000 | 0.2200 | 0.3607 | 0.3710 |

### combined

| Stage | TP | FP | TN | FN | Precision | Recall | F1 | Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Collection | 4 | 4 | 40 | 12 | 0.5000 | 0.2500 | 0.3333 | 0.7333 |
| Processing | 8 | 0 | 36 | 16 | 1.0000 | 0.3333 | 0.5000 | 0.7333 |
| Method | 13 | 3 | 15 | 29 | 0.8125 | 0.3095 | 0.4483 | 0.4667 |
| Experimentation | 24 | 0 | 4 | 32 | 1.0000 | 0.4286 | 0.6000 | 0.4667 |
| Evaluation | 4 | 0 | 23 | 33 | 1.0000 | 0.1081 | 0.1951 | 0.4500 |
| Dissemination | 31 | 3 | 8 | 18 | 0.9118 | 0.6327 | 0.7470 | 0.6500 |

### Partial-scan sensitivity analysis (exploratory)

| Mode | Acquired N | Complete N | Captured-evidence macro F1 | Captured-evidence micro F1 |
|---|---:|---:|---:|---:|
| documentation-only | 98 | 88 | 0.3921 | 0.4427 |
| code-only | 98 | 62 | 0.1555 | 0.1722 |
| combined | 98 | 60 | 0.4659 | 0.5113 |

## Evidence and reproducibility

Each positive occurrence retains repository/commit, relative path, source, 1-based inclusive line range, exact original excerpt, evidence ID, content/catalog hashes, analysis run ID, primary rule/version and all matching rule attributions. Deduplication uses repository/commit/stage/source/path/start/end/excerpt. Distinct positions and stage interpretations remain separate; matching the same passage with several rules does not inflate its occurrence count. Overlapping but different spans remain separate. Mode views share stable evidence IDs; do not sum documentation/code/combined JSONL rows.

Complete structured results, gold import/provenance, original XLSX export, fixed input manifests, all referenced captured snapshots, original-baseline parity check and comparison CSV/JSON/JSONL are supplied privately in the result archive. The public repository contains implementation, the split, baseline catalogs and this aggregate report; it does not publish the raw human workbook/labels or redistribute captured repository contents.

From the source checkout, after extracting the archive:

```bash
uv sync --frozen
uv run --frozen python -m lifecycle_mapper benchmark compare --reference /path/to/archive/reference --run /path/to/archive/captures --split benchmark/versions/split-20261015.json --rules benchmark/versions/baseline-rules --partition development --partition held_out --partition full_exploratory --output local/reproduced-baseline
uv run --frozen python -m lifecycle_mapper benchmark compare --reference /path/to/archive/reference --run /path/to/archive/captures --split benchmark/versions/split-20261015.json --partition development --partition held_out --partition full_exploratory --output local/reproduced-candidate
```

No network is needed for those comparisons; hashes are checked before analysis. Import `comparisons/candidate/results.json` under Previous runs to review all 100 rows, including failures. Imported JSON restores review; retain snapshots for replay. The original baseline catalogs and the original source commit remain available independently.

## Verification and remaining limitations

- Baseline test suite: 113 passed, two browser tests skipped. Final suite: **147 passed, two browser tests skipped by default**. Ruff lint/format and mypy pass. Catalog regeneration preserves the frozen rule hash.
- JavaScript syntax and DOM checks pass for overview/detail rendering, source-mode deduplication, counts, filters, reference mismatches, partial-failure display, escaping and safe GitHub links. Two explicit Playwright tests were attempted but could not launch: Chromium installation returned invalid/truncated archives. Browser rendering, mobile layout and end-to-end visual verification therefore remain unverified; no passing browser result is claimed.
- The classifier remains a candidate heuristic system with substantial false negatives. Python 2 syntax failures and unsupported code languages are material coverage limits. R/Julia/MATLAB/shell masking is lexical, not a complete language parser; complex quoting, nested/block comments and shell heredocs can limit accuracy. Notebooks/binary documentation are not supported.
- Human labels were primarily documentation-derived, so code-only agreement has construct limits. Annotation-time commits and independently approved sampling/codebook provenance are unavailable; current captured commits may differ from annotation-time content. The formal publication workflow remains pending rather than manufacturing those approvals.
- Two acquisition failures, partial API recovery and mode-specific complete-case selection limit empirical claims. The 20-repository operational test subset is small and not independently blinded. No best-possible, external-generalization, scientific-validity or reproducibility claim is made.
- The separate upstream repository was not modified and no upstream code was copied.

## Version identifiers

- Exported workbook SHA256: `f47d9e85170b4b1db1c454bc3b7b9b033b6553cef001a7a518d3b3ded5c4b3ca`.
- Frozen candidate catalog SHA256: `c6bdd6f7b60e21b22bb1b41eac024f5b30a5aa428febf14366b01dde0a8a3380`.
- Baseline catalog SHA256: `9511dc1724fa7e713491f3c363d57774b50bd5e29964e1aa77a159ba3a7748d3`.
- Split SHA256: `49a197cd4eef49b4fd8b14165a6b184a4b41117977cbafe78b7e80db1616d58c`.
- Every captured repository commit and snapshot hash is recorded in the private acquisition manifest; every comparison records classifier Git state and implementation content hash. Execution occurred on the original base with local verified changes; source content hashes identify the implementation independently of the subsequent publication commit.

Commit links are supplied with the delivery. No token or authentication response body is included in the exports.
