# Notebook routing and live reference audit

This amendment supersedes the earlier assumption that final_agreement is a
strict documentation-only reference. The original six human labels are preserved.

## Implemented notebook policy

New snapshots use eligibility-2-notebook-cells. An eligible .ipynb is captured
once, checksum-verified, then parsed as notebook format 4. It is never executed.
Markdown cell sources enter documentation detectors; code cell sources enter
source-code detectors for the declared supported language. Cells are isolated:
conditions from different cells cannot be joined into a match. Outputs, metadata,
attachments and raw cells never enter either evidence stream. Markdown fenced
commands remain documentation, as in a README. Code comments/docstrings remain
inside the code channel and are masked by existing executable-code detectors.

Each finding retains the original notebook path, original blob SHA-256, 1-based
cell index/type/language, and cell-relative line numbers. Notebook URLs point to
the original notebook without misleading raw-JSON line anchors. Duplicate text
in different cells retains separate evidence identities.

Supported declared code languages: Python, R, Julia, MATLAB, bash/sh, subject to
existing detector coverage. No kernel is executed. Missing/unsupported languages,
malformed notebooks and unsupported magics make the affected channel incomplete.
The display-only %matplotlib inline/notebook/widget directive is masked while
preserving line positions; other magics are not silently treated as Python.
A code-channel problem does not invalidate successfully parsed Markdown cells.
Old eligibility-1 snapshots replay under their original policy; previously
excluded notebooks are NOT retroactively counted as scanned. A new acquisition
is necessary to capture them. The existing per-file size limit also applies to
notebooks, including stored outputs; oversized containers remain unavailable.

The two notebook files linked by the reference were inspected at their annotation
commits: one R notebook contains 8 Markdown + 9 code cells; one Python notebook
contains 17 Markdown + 50 code cells, including a display-only matplotlib magic.
Cell extraction was checked on both. This is parser verification, not benchmark
F1 verification or evidence that every stage is detectable by current rules.

## Live-reference audit results

Read all final_agreement cells A1:G101, including hyperlinks, at audit time.
All 600 labels match the committed workbook; no label was changed. No cell notes
were returned in those ranges. The anonymous audit records repository identities,
labels and evidence hyperlinks, not reviewer identities or the live sheet URL.

| Evidence hyperlink type | Positive labels | Negative labels |
|---|---:|---:|
| Documentation, including extensionless README | 86 | 75 |
| Source code | 79 | 0 |
| Mixed R Markdown | 4 | 0 |
| Jupyter notebook | 2 | 0 |
| Data/other artifact (excluded from scanning) | 0 | 1 |
| No hyperlink | 213 | 140 |
| Total | 384 | 216 |

Retrieved the 166 distinct linked non-data files, including the pinned commits,
and inspected linked passages. The one data-artifact link was not scanned.
A source-code link does not prove documentation elsewhere lacks the evidence.
Likewise, a negative label pointing at a README does not prove absence across the
repository. Link classification is not a second semantic adjudication. The 213
unlinked positive cells still need supporting passages or annotation rationale
before claiming a complete evidence-to-label reconstruction.

Because evidence rows for all 100 repositories have now been exposed, the old
operational grouping must not be described as an untouched holdout. Any subsequent
tuning on these cases is benchmark development; generalization needs a new set.

## Concrete corrections to the proposed rules

| Case | Final label and linked evidence | Consequence |
|---|---|---|
| simextargid | Dissemination=1; README explicitly says a software version is archived on Zenodo, beside a DOI badge | The previous blanket exclusion of software archival is too strict. Distinguish explicit archival of the research artifact from an unexplained DOI/badge. D-DIS-01 requires a codebook clarification. |
| count-vector-paper-experiments | Processing/Method/Evaluation=1 link to preprocessing, neural-network and result-reporting source files | These are mixed-source labels; failure to recover them from documentation alone is not automatically a documentation detector error. |
| code-datasets | Processing=1 links to a source header/docstring describing signature conversion | Pure executable detection intentionally masks this passage. Record source-comment evidence separately if the codebook accepts it; do not relabel it as notebook/README documentation. |
| ocd | Method=1 links into an R notebook's function definition | Route the code cell to R source analysis, never scan raw JSON as prose. |
| iclr20 | Dissemination=1 links to notebook code exporting a PDF | Route the code cell to code; the export still needs scientific-output context. |
| norms-cogsci19 | Processing/Method/Evaluation link into analysis.rmd; some are prose, others fenced R | Jupyter support does not yet solve R Markdown; a separate fence-aware parser remains pending. |
| bidding-at-risk-experiment | Collection=0 although README instructs downloading the research dataset | D-COL-01's broad acquisition definition does not universally reproduce this label. Clarify original acquisition versus instructions to reuse external data. Do not silently change the label. |
| autoencoders_dictionaries | Collection=0 though README describes simulations over synthetic datasets | Synthetic research observations versus internal simulation inputs need an explicit boundary; do not assign Collection from synthetic/data vocabulary alone. |

These are interpretation issues to reconcile with the human codebook, not
permission to add repository-name exceptions. Link excerpts may be narrower than
the complete evidence the reviewers considered. No claim of inconsistent humans
or unreachable accuracy follows solely from these examples.

## What is and is not ready

Notebook routing is implemented. New tests check mode isolation, output/raw-cell
exclusion, cell-relative provenance, no cross-cell matches, duplicate-cell IDs,
malformed input, unsupported syntax/languages and safe display-magic masking.
The full proposed v6 rule catalogue is still a design; this change does not
implement all 30 proposed rules. No new 100-repository score has been measured.

Next: resolve the specific coding boundaries above, implement the frozen rule
conditions, acquire missing notebook inputs under the new eligibility policy,
and replay all 100. Report per-stage errors, precision/recall/F1, exact match,
coverage and trivial baselines. Do not promise near-100% agreement before this
measurement, or describe benchmark-tuned performance as independent validation.
