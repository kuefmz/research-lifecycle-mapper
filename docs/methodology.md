# Research methodology and implementation status

Current reference: the corrected anonymous workbook has 600 valid independent decisions, 354 agreements, 246 disagreements and no missing values. reviewer1 and reviewer2 jointly adjudicated final_agreement. See docs/annotation_status_20261020.md and data/annotation_audit_20261020.json. Live acquisitions use main, otherwise master, pinned to an immutable commit. Historical protocol descriptions below retain their original context.


## Task and evidence

The unit of prediction is a GitHub software repository at one immutable commit. The output is a six-bit multi-label vector ordered Collection, Processing, Method, Experimentation, Evaluation, Dissemination. Zero positive labels is allowed. Stage definitions in `codebook.md` are candidates, not approved human definitions.

Three separate prediction modes use eligible documentation, eligible implementation artifacts, or their logical union. Eligibility policy `eligibility-1` recognizes textual documentation suffixes and common code suffixes, excludes vendored/generated/fixture directories, and treats symlinks and submodules as excluded inventory entries. Binary/unsupported artifacts remain inventoried. Initial code rules are Python-only; notebook, configuration, dependency and data artifacts cannot qualify a stage. Plain .txt documentation is eligible, but dependency lines alone match no activity rule.

## Rule design and aggregation

The classifier is deterministic and uses no learned model, embeddings, LLM calls or stochastic scoring. Versioned rules require explicit activity plus qualifying research context or a concrete operation. Machine-readable justifications connect each rule to a conceptual definition. Exclusions distinguish future plans, negation, software tests and synthetic/example-only claims from qualifying evidence. Generic indicators have no independent classification power.

Rules and evidence are evaluated with fixed ordering. Qualifying file evidence is aggregated as an ordered repository-level union. Combined predictions are the union of source-specific qualifying evidence. Rules never inspect gold labels. No result cache is keyed solely by a repository URL.

## Human benchmark construction

reviewer2 and reviewer1 independently annotated 100 repositories over six stages and then reviewed the annotations together to create final_agreement, which both agree with (researcher confirmation, 2026-10-20). The final table is complete: 100 repositories, 600 binary labels. It is a documentation-only reference, not a source-code reference. See annotation_status_20261020.md for live verification, the still-visible original independent-cell discrepancy, and the distinction between initial reliability and final adjudication.

The exact relationship among the OpenAIRE frame, 386 candidates and 100 annotated repositories still requires selection/overlap provenance. The older upstream frame identifies release 12819872, while a later researcher link identifies 20428976; use the archive actually downloaded and record its checksum. Historical annotation-time commits remain unknown.

Importers preserve source data and separate original independent labels from final adjudication. The researcher's explicit confirmation establishes final-label consensus; machine-readable checksums bind an imported version. Separate sampling and human codebook provenance must not be inferred from consensus. The legacy formal publication workflow requires complete normalized independent labels and supporting manifests; the observed comparison route can evaluate complete final labels without filling a historical blank.

## Evaluation

Evaluation produces all three modes separately. Per-stage TP/FP/TN/FN, precision, recall, F1 and support are computed on completely analyzed repositories for that mode. Micro metrics pool decisions; macro metrics average the six stage metrics equally, including stages of zero support. Exact-match accuracy requires equality of the complete vector. Hamming loss is erroneous stage decisions divided by six times the evaluated repository count.

Undefined ratios use zero consistently. Empty evaluated sets are flagged by `repository_count=0`. Floats are rounded to eight decimal places before serialization. Coverage is completely analyzed repositories divided by total benchmark repositories; analysis failure rate is its complement. Partial positive predictions are retained for inspection but incomplete repositories do not contribute to confusion matrices or accuracy. Therefore differing eligible denominators across modes must be reported and considered when comparing them.

False-positive and false-negative rows include supporting rule IDs and pinned URLs when a predicted label exists. False negatives have no invented classifier evidence. Acquisition/parse failures are separate error types. Confusion matrices are provided as tables and a deterministic SVG figure.

`exploratory`, `held-out` and `synthetic` roles are explicit. Synthetic fixtures can only use the synthetic role. Held-out research evaluation requires approval of the split, a declaration that the examples were not used for rule development, and no intersection with declared development repositories. These guards enforce supplied declarations; they cannot reconstruct undisclosed researcher behavior. Tuning on the same 100 repositories precludes calling their performance unbiased held-out performance.

## Reproducibility and validity

Acquisition resolves a ref once, traverses immutable Git trees and downloads blobs by object SHA. Snapshots store inventories, unavailable/excluded statuses and raw-content hashes. Replay checks canonical manifests and hashes without network use. Execution manifests record implementation revision/dirty status/source hash, catalog hash, benchmark identity/hash, snapshot hashes, config, Python version and lock hash. Stable result artifacts contain no wall-clock timestamps or absolute paths. Platform/machine details are isolated in environment.json.

Threats include incomplete retrieval, conservative rule false negatives, documentation overclaims, static dead code, non-English documentation, narrow Python naming assumptions, inaccessible historical commits, sample selection bias, disagreement/adjudication choices, codebook drift and benchmark-driven tuning. A detected activity is evidence that the repository supports that activity, not proof of scientific correctness. No-match is not proof of activity absence.

Implemented software behavior is exercised by synthetic tests. The final documentation reference is jointly adjudicated and has been inspected. Sampling/codebook documentation, an independently blinded evaluation, release packaging and container digest pinning remain distinct outstanding tasks. No human performance results have been fabricated.

## v0.2.0 protocol update

Documentation-only is primary, with development macro-F1 for model selection. Documentation uses explicit, contextual and demonstrated-workflow families with activity/object/scope/polarity records; wrapped prose and inherited Markdown/AsciiDoc/reStructuredText headings are supported. Production matching is deterministic and uses no gold labels or external models. Both the verified `final_agreement` mapping and legacy `Agreement Final` mapping are supported; independent labels remain separate provenance. See `agreement_final.md`, `evaluation_protocol.md` and `rule_change_protocol.md` for the current importer, split, freeze, mismatch and final-run procedures. Historical one-line rules and unsplit held-out declarations are superseded. This describes the historical V2 protocol. The original workbook has now been audited and observed reference comparisons have been run; see [the V3 implementation report](implementation_report_20261015.md) for actual measurements and their limits.
