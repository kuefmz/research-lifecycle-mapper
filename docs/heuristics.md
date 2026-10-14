# Implemented heuristic semantics

Rules are evaluated in fixed stage/source/ID order. Each catalog lists a stable ID, source, activity description, at least two required positive patterns, optional supporting patterns, explicit exclusions, required evidence fields, version, candidate status, evidence-window length and conceptual justification.

Documentation rules now use sentence-scoped wrapped prose and purpose-plus-command workflow units, bounded to 12 physical lines. Python rules require all positives within an eight-line window, with a research-specific function declaration and an operation inside that same function's AST span. Comments and string literals are masked without shifting line positions. A valid Python parse is required; parse errors are analysis failures. No inspected program is executed. Code in software-test paths is vetoed. Other implementation languages remain inventoried but have no positive code rules in this candidate version.

All positives must match. Supporting conditions cannot qualify a label. Any matching exclusion in the evidence window vetoes the candidate. Excluded candidates are emitted separately. Generic engineering behavior and ambiguous evidence produce no positive label; they are not silently upgraded using a score. Files without matches remain in the snapshot inventory even though the evidence report contains only matched/vetoed candidates.

Evidence reports preserve each condition's exact text and the smallest inclusive physical-line span containing the matches. Repeated window matches with the same rule and span are deduplicated. URLs encode exact case-sensitive paths and pin the immutable commit. Actual excerpts come from original content, not masked text.

Repository labels are the ordered set union of qualifying evidence. Documentation-only filters eligible source artifacts before matching; code-only applies the corresponding independent filter. Combined matches both and takes their logical union. No scores or indicators cross modes.

The candidate function names are intentionally very restrictive. They are sufficient testable initial conditions, not an empirically validated vocabulary. Broadening them using the human benchmark makes that benchmark development data and requires exploratory reporting or a separately approved held-out split.

## v0.2.0 protocol update

Documentation-only is primary, with development macro-F1 for model selection. Documentation uses explicit, contextual and demonstrated-workflow families with activity/object/scope/polarity records; wrapped prose and inherited Markdown/AsciiDoc/reStructuredText headings are supported. Production matching is deterministic and uses no gold labels or external models. Agreement Final is the required candidate consensus worksheet; independent labels remain separate provenance. See `agreement_final.md`, `evaluation_protocol.md` and `rule_change_protocol.md` for the current importer, split, freeze, mismatch and final-run procedures. Historical one-line rules and unsplit held-out declarations are superseded. Human inputs are still missing; no human tuning or held-out run was performed.
