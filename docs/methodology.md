# Research methodology and implementation status

## Task and evidence

The unit of prediction is a GitHub software repository at one immutable commit. The output is a six-bit multi-label vector ordered Collection, Processing, Method, Experimentation, Evaluation, Dissemination. Zero positive labels is allowed. Stage definitions in `codebook.md` are candidates, not approved human definitions.

Three separate prediction modes use eligible documentation, eligible implementation artifacts, or their logical union. Eligibility policy `eligibility-1` recognizes textual documentation suffixes and common code suffixes, excludes vendored/generated/fixture directories, and treats symlinks and submodules as excluded inventory entries. Binary/unsupported artifacts remain inventoried. Initial code rules are Python-only; notebook, configuration, dependency and data artifacts cannot qualify a stage. Plain .txt documentation is eligible, but dependency lines alone match no activity rule.

## Rule design and aggregation

The classifier is deterministic and uses no learned model, embeddings, LLM calls or stochastic scoring. Versioned rules require explicit activity plus qualifying research context or a concrete operation. Machine-readable justifications connect each rule to a conceptual definition. Exclusions distinguish future plans, negation, software tests and synthetic/example-only claims from qualifying evidence. Generic indicators have no independent classification power.

Rules and evidence are evaluated with fixed ordering. Qualifying file evidence is aggregated as an ordered repository-level union. Combined predictions are the union of source-specific qualifying evidence. Rules never inspect gold labels. No result cache is keyed solely by a repository URL.

## Human benchmark construction

The research brief reports two independent annotators, Jenifer and Esteban, each labeling the same 100 repositories over six stages: 600 repository-stage pairs and 247 initial disagreements. These are user-supplied provenance claims awaiting verification against the source workbook, not computed findings. Independent labels do not constitute adjudicated gold.

The audited source repository documents an OpenAIRE/Zenodo-derived GitHub corpus. Its exact relationship to the human sample, selection procedure, inclusion/exclusion criteria and historical analyzed revisions are not available. No sample or revision is inferred from cached classifier results or the upstream default random-batch command.

The importer reads a provided workbook or normalized CSV without modifying it, stores its original checksum, preserves both independent labels and proposed consensus, and enumerates disagreements. Approval references are required for approved labels. Human adjudicators must resolve disagreements and approve the codebook and final labels. The benchmark validator verifies annotation counts/checksums, per-stage approved-label agreement with the manifest, sampling/codebook documentation and snapshot identities before research evaluation.

## Evaluation

Evaluation produces all three modes separately. Per-stage TP/FP/TN/FN, precision, recall, F1 and support are computed on completely analyzed repositories for that mode. Micro metrics pool decisions; macro metrics average the six stage metrics equally, including stages of zero support. Exact-match accuracy requires equality of the complete vector. Hamming loss is erroneous stage decisions divided by six times the evaluated repository count.

Undefined ratios use zero consistently. Empty evaluated sets are flagged by `repository_count=0`. Floats are rounded to eight decimal places before serialization. Coverage is completely analyzed repositories divided by total benchmark repositories; analysis failure rate is its complement. Partial positive predictions are retained for inspection but incomplete repositories do not contribute to confusion matrices or accuracy. Therefore differing eligible denominators across modes must be reported and considered when comparing them.

False-positive and false-negative rows include supporting rule IDs and pinned URLs when a predicted label exists. False negatives have no invented classifier evidence. Acquisition/parse failures are separate error types. Confusion matrices are provided as tables and a deterministic SVG figure.

`exploratory`, `held-out` and `synthetic` roles are explicit. Synthetic fixtures can only use the synthetic role. Held-out research evaluation requires approval of the split, a declaration that the examples were not used for rule development, and no intersection with declared development repositories. These guards enforce supplied declarations; they cannot reconstruct undisclosed researcher behavior. Tuning on the same 100 repositories precludes calling their performance unbiased held-out performance.

## Reproducibility and validity

Acquisition resolves a ref once, traverses immutable Git trees and downloads blobs by object SHA. Snapshots store inventories, unavailable/excluded statuses and raw-content hashes. Replay checks canonical manifests and hashes without network use. Execution manifests record implementation revision/dirty status/source hash, catalog hash, benchmark identity/hash, snapshot hashes, config, Python version and lock hash. Stable result artifacts contain no wall-clock timestamps or absolute paths. Platform/machine details are isolated in environment.json.

Threats include incomplete retrieval, conservative rule false negatives, documentation overclaims, static dead code, non-English documentation, narrow Python naming assumptions, inaccessible historical commits, sample selection bias, disagreement/adjudication choices, codebook drift and benchmark-driven tuning. A detected activity is evidence that the repository supports that activity, not proof of scientific correctness. No-match is not proof of activity absence.

Implemented software behavior is exercised by synthetic tests. Human benchmark import, final gold approval, experimental protocol freeze, release permissions, container digest pinning and scientific validation remain planned work. No human performance results have been fabricated.
