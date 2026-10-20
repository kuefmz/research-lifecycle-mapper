# MSR 2027 paper plan — documentation validation and additional repository evidence

The main contribution is an evidence-preserving method for identifying six research-lifecycle stages in repository documentation, validated against jointly adjudicated human documentation labels, plus a separately reviewed study of additional source evidence. Scale is a secondary descriptive contribution conditional on completed acquisition.

## Research questions

- RQ1: How accurately do documentation heuristics identify the six stages against the agreed documentation reference?
- RQ2: What stage evidence does source inspection add beyond documentation, and what fraction of proposed additions are confirmed by human review?
- RQ3 (conditional): What stage-evidence patterns and coverage limitations appear in the larger OpenAIRE-derived corpus?

Describe original independent annotations and joint adjudication in Methods. Initial agreement is a measure of independent reliability; final consensus is the evaluation reference. Do not substitute final 100% consensus for initial inter-rater reliability. Correct initial counts only from the actual corrected source/version.

## Ten-page budget

| Section | Pages | Essential content |
| --- | ---: | --- |
| Abstract | 0.25 | Problem, method, actual evaluated N, strongest verified findings and limits |
| Introduction | 0.85 | SE/MSR motivation, gap, use case, RQs and contributions |
| Related work | 1.00 | Metadata extraction, scholarly code analysis, README classification, FAIR/quality tools |
| Method and stage operationalization | 1.50 | Six definitions, evidence boundary, rules, provenance and incomplete-scan semantics |
| Datasets and annotation | 1.25 | Exact OpenAIRE release, 105k/386/100 relationships, documentation scope, independent annotation/adjudication |
| Evaluation design | 1.00 | Baselines, development history, common cohorts, metrics, uncertainty and manual review sampling |
| Results | 2.00 | Documentation accuracy; reviewed code additions; larger corpus only if completed |
| Discussion and practical implications | 0.80 | What can be discovered and why it helps repository understanding |
| Threats to validity | 0.90 | Scope, low initial agreement if still observed, leakage, revisions, acquisition and language bias |
| Conclusion and data availability | 0.45 | Supported conclusions, anonymous artifact and reproduction |
| Total main text | 10.00 | Includes all figures/tables/appendices |

Use at most two additional pages containing references only. Main-text figures and captions consume the budgets above. Use the 2027 IEEE conference template; do not budget an appendix outside the ten pages.

## Essential tables and figures

1. Six-stage definitions and positive/counterexample evidence (Method).
2. Corpus/filtering flow with counts for actual source records, links, deduplicated repositories, accessible/analyzed/complete cohorts; show overlap between 386 and 100 rather than assuming nesting.
3. Compact primary accuracy table: per-stage support/P/R/F1 and macro/micro F1 with repository-level bootstrap intervals, complete N and coverage. Include constant and simple keyword baselines.
4. Additional-evidence table: candidate repository-stage pairs, manually reviewed pairs, confirmed additions, false positives and ambiguous cases by stage. Use explicit denominators; occurrences are not independent repository-stage discoveries.
5. One commit-pinned worked example contrasting human documentation label, documentation prediction and manually validated source evidence. A small pipeline diagram can share this space.

Keep full rules, all confusion matrices, all mismatches, source excerpts, acquisition inventories and software UI details in the replication artifact.

## Analysis and claim rules

Primary metrics compare documentation-only predictions with final_agreement. Preserve false positives/false negatives even if code supports a stage. Report unknowns and failures separately. If comparing source modes, use identical repository revisions and common evaluated cohorts; code-only/combined agreement against documentation labels is a construct-mismatched descriptive analysis, not validated code accuracy.

For RQ2, prioritize human-documentation-negative, documentation-prediction-negative, code-positive pairs. Review source evidence and the entire defined documentation scope to confirm an omission. Separately report documentation-positive/classifier-negative/code-positive cases as detector misses. Review evidence with a code-specific rubric; record both reviewers and adjudication. If sampling candidates, select before review, state design/seed/stage coverage and report uncertainty without treating all unreviewed detections as true discoveries.

Freeze detector rules now. Do not tune on reviewed candidate outcomes and then claim an independent evaluation on the same examples. If prior full labels were available during development, disclose the existing operational held-out split's limits. Bootstrap repositories, not six independent stage decisions.

## Related work priorities

Closest: Haris, Stocker and Auer, Scholarly Knowledge Extraction from Published Software Packages (ICADL 2022; DOI 10.1007/978-3-031-21756-2_24), which uses metadata, Python ASTs and linked articles; SOMEF / A framework for creating knowledge graphs of scientific software metadata (DOI 10.1162/qss_a_00167); Prana et al., Categorizing the content of GitHub README files (DOI 10.1007/s10664-018-9660-3).

Adjacent: FAIR4RS (DOI 10.1038/s41597-022-01710-x), FAIRsoft (DOI 10.1093/bioinformatics/btae464) and RepoScore for quality/FAIRness distinctions. The AI Scientist Nature paper (DOI 10.1038/s41586-026-10265-5) is motivation for scientific workflows, not a direct stage-classification baseline. Verify every final citation and attributed finding from the paper itself.

## Include only if supported

- The 386 run as an exploratory extension after documenting selection and overlap. Without labels it is not external accuracy validation.
- The 105k run as descriptive scale analysis only if completed and audited. If unfinished, report the corpus construction and a clearly scoped pilot, or omit scale results entirely. A running job is not a result.
- Tool UI as a small evidence-inspection example, not a separate contribution unless usability is evaluated.

## Exclude

No broad reproducibility/scientific-validity claims; no unverified "first" claim; no combined-versus-documentation accuracy headline using a documentation-only gold standard; no claim all additional files/languages are analyzed; no inferred true prevalence from conservative detector matches; no post-consensus agreement presented as independent reliability; no invented sampling seed or historical revisions; no unfinished full-corpus result placeholders.

## Three-day execution

20 October: register abstract; finalize scope and annotation account; freeze rules; extract the local archive and launch fresh 200-repository pilot; rerun documentation evaluation and prepare candidate-review table.
21 October: finish 100 evaluation, baseline/uncertainty calculations and paired evidence review; run the 386; decide whether full corpus can finish with sufficient time for audit.
22 October: freeze tables and manuscript findings, complete related work/limitations and anonymous replication package; supervisor reviews the claim-evidence mapping.
23 October: final PDF/template/anonymity/source checks and submit with margin.

Confidence: 0.9 in this scope and prioritization; runtime confidence remains low until the user's machine/network pilot. No acceptance probability is implied.
