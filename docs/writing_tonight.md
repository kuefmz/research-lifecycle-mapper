# Write tonight while the results run

Protect the validated documentation study from dependence on an unfinished full-corpus job. The primary contribution is a traceable six-stage documentation classifier evaluated against jointly adjudicated human labels. Separately review source-code evidence that may reveal documentation omissions.

## Six-hour writing sequence

| Relative block | Write or review | Concrete output |
| --- | --- | --- |
| First 30 minutes | Launch the benchmark; freeze RQs, branch policy and claim boundaries | Outline and claim-to-evidence table |
| Next 75 minutes | Method and datasets | Six definitions; documentation-only scope; exact OpenAIRE release/filtering; main/master commit policy; reviewer procedure |
| Next 60 minutes | Related work | Compare SOMEF, scholarly AST extraction and README classification; distinguish FAIRsoft/RepoScore and AI Scientist |
| Next 45 minutes | Introduction | One practical use case, the research gap, three precise contributions |
| Next 60 minutes | Evaluation/results scaffolding and evidence review | Metric definitions and baselines; fill actual tables when available; review code-only candidates using a separate rubric |
| Next 45 minutes | Discussion and threats | Implications, revision drift, initial disagreement, development leakage, acquisition/language limitations |
| Final 45 minutes | Abstract, conclusion, availability and PDF checks | Claims use actual N; ten-page IEEE PDF; anonymous links; no unfilled numerical placeholders |

The schedule is relative so it remains useful whenever execution begins. If a result is unavailable, narrow the corresponding claim rather than writing a promised number. Freeze tables with time left for supervisor review.

## Research questions

1. How accurately do documentation heuristics recover the agreed six-stage documentation labels?
2. What source-evidence candidates are confirmed through independent human review, and what types of information are missing from documentation?
3. Conditional on a completed larger run: what detected evidence patterns and acquisition limitations appear in the OpenAIRE-derived corpus?

## Exact ten-page budget

| Section | Pages |
| --- | ---: |
| Abstract | 0.25 |
| Introduction | 0.85 |
| Related work | 1.00 |
| Method and stage definitions | 1.50 |
| Datasets and annotation | 1.25 |
| Evaluation design | 1.00 |
| Results | 2.00 |
| Discussion | 0.80 |
| Threats to validity | 0.90 |
| Conclusion and data availability | 0.45 |
| Total main text, including figures/tables/appendices | 10.00 |

Use at most two additional pages containing references only. The 2027 call uses IEEE conference format. Keep the full rules, exhaustive mismatches, file inventories and extra confusion matrices in the artifact.

## Facts that can be written now

- The benchmark contains 100 repositories and 600 final documentation labels, agreed after joint adjudication.
- The corrected independent annotations contain 354 agreements and 246 disagreements over 600 valid pairs, with no missing values. Report per-stage kappa and the adjudication procedure; consensus does not erase initial disagreement.
- Main is preferred, master is the only fallback. The selected commit is pinned. This standardizes analysis; it does not prove that final publication artifacts live on that branch.
- The classifier is deterministic and returns traceable evidence. Static evidence does not prove execution, reproducibility or scientific validity.

## Tables to finish when data arrive

1. Sampling/acquisition flow: source records, links, unique requested repositories, main/master selection, inaccessible repositories, analyzed and complete cohorts. Verify 386/100 overlap rather than assuming nesting.
2. Documentation-only per-stage support, precision, recall and F1; macro/micro F1, baseline results, repository-level uncertainty, evaluated N and coverage. No unknown scans converted into negatives.
3. Additional-evidence candidates: repository-stage counts, reviewed counts, confirmed omissions, false positives and ambiguous cases. Multiple occurrences do not create independent discoveries.
4. One commit-pinned worked example linking the documentation label/prediction and reviewed source evidence.

If comparing documentation/code/combined agreement, use identical commits and common cohorts and label the construct mismatch: documentation labels are not validated code labels. A documentation-positive/classifier-negative/code-positive case remains a documentation detector miss.

## Keep out

No guaranteed six-stage quality score for this artifact, no unverified first-of-its-kind claim, no true population prevalence inferred from conservative matches, no unrun 105k findings, no promised DOI presented as already deposited, and no named author/project links in the anonymous paper. The 386 run is exploratory unless independently annotated; full-corpus scale is optional.

## Last review pass

Check the exact main-text page count, table denominators, citation attributions, anonymous downloadable workbook, selected-branch counts, real artifact URLs and preserved-release status. Run the documented commands from a fresh checkout. Replace any availability promise with the release's actual status. Submit before the deadline with a safety margin.
