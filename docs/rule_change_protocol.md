# Generalizable rule changes and mismatch review

1. Inspect only `documentation_errors.csv` from the development partition. Its rows record the human label, documentation prediction, rule IDs, original excerpts, paths/lines, excluded candidates, a mechanical error category and an **unreviewed hypothesis**. A mismatch does not establish that the human label is wrong. False negatives have no invented positive evidence.
2. Create a separate private review ledger keyed by repository/stage. Record reviewer, codebook version, observed documentation availability, hypothesis (missing documentation, insufficient heuristic, codebook ambiguity or other), decision reference and whether the interpretation is resolved. Never edit canonical result artifacts or source workbook rows to erase errors.
3. Propose a general linguistic/activity-object-scope change, its conceptual justification, expected precision/recall tradeoff, rule IDs/version and the development examples used. Do not check repository owner, URL, identity or unique benchmark phrases. The production matcher receives document content/rules only; repository metadata is added after matching for evidence provenance.
4. Add an affirmative synthetic example and counterexamples covering negation, future scope, third-party/delegated functionality, infrastructure, and source isolation. Every changed rule needs positive/negative regression tests. Update the catalog changelog, rule-to-concept justification, package copy and documentation.
5. Rerun development evaluation; compare documentation macro-F1 and all per-stage precision/recall/F1 values, retaining earlier versions and unfavorable results. Record the choice and rationale independently of test labels. Freeze rules/configuration before the custodian releases the final test execution.

Model selection remains a researcher decision using explicit development metrics; no automated heuristic optimizer or opaque learned threshold is implemented. The current rule families are candidates and have not been aligned empirically to the unavailable human codebook.

## Observed development changes (v5)

The supplied documentation error-review export allowed a bounded paragraph and
heading/command candidate to be tested. The matcher still receives only document
content and versioned rules. The operational holdout error attachment was not
inspected to revise rules. v5 remains opt-in and below the requested 0.80/0.90
F1 targets; on the 70 available development error-review texts it also remains
below always-positive micro-F1. Full original-capture replay is required because
two complete, error-free development repositories were omitted from that export.
No old predictions, reference labels, denominators or incomplete flags were changed.
