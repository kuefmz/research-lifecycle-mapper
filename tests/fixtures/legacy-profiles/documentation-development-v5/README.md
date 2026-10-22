# Development profile v5: documented research workflows

This opt-in profile preserves v4 and adds activity/artifact rules for documented
scientific workflows. It was developed after inspecting the supplied development
mismatches, not the operational holdout errors. No repository name, URL, label,
unique dataset identifier or project-specific vocabulary is a matching feature.
The unchanged source-code rules remain separate.

Changes: bounded paragraph units, nearby headings and commands as one evidence
range; Markdown presentation normalization with original excerpts retained;
file-local research scope for terse instructions; bibliography/infrastructure/
third-party/future/negation exclusions; broader general wording for data processing,
statistical methods, research experiments and scientific result communication.
A file's research context does not itself assert that any stage is present: a
stage still requires its two configured positive patterns in a local unit.

All v5 evidence uses contiguous original-document ranges of at most twelve lines.
Inherited headings provide exclusion context; only headings inside that range can
supply positive features. Code mentioned or fenced inside documentation remains
documentation evidence; implementation files never enter documentation-only mode.
The rule families are hypotheses needing a versioned human codebook check.

Measured on the 70 supplied, complete **development error-review** repositories:

- Old documentation micro-F1 0.4082; v5 0.7480.
- Old documentation macro-F1 0.3743; v5 0.7029.
- V5 micro precision 0.7724 and recall 0.7252.
- Always-positive micro-F1 on the same subset is 0.7683. V5 has higher precision
  and specificity but has NOT surpassed that F1 baseline or the requested 0.80.
- Combined cross-scope reference agreement on the 48 available complete
  development cases rises from micro-F1 0.4896 to 0.7596 with unchanged code.
  This is not validation against source-code ground truth or the requested 0.90.

These are development results, not a score for the full 100 or an independent
test. Two error-free complete development repositories were absent from the
review export and were not assumed unchanged. Nine incomplete documentation
scans also cannot be made complete by changing rules. Preserve the original
human labels and snapshots. Full offline replay on the user's original captures
is required to measure all available cases.

See docs/development_v5.md for commands, limitations and input/result hashes.
