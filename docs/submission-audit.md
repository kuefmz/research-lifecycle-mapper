# Submission audit

Audit date: 2026-10-22. Scope: current distributed files, the supplied paper draft and
author-confirmed corrections, original assessment tables, supplied run metadata,
repository populations, rules, documentation, funnel, and a history-free review package.

**Outcome: benchmark reproduction is verified; complete corpus/evidence reproduction
is not yet established.** This is a partial archive awaiting original result uploads,
not a claim that every paper result has been independently regenerated.

## 1. Paper-to-artifact coverage

| Paper element | Artifact | Status |
|---|---|---|
| Data source and Figure 1 funnel | `docs/data-generation.md`, `figures/`, `scripts/create_openaire_funnel.py` | Editable figure and source/count provenance included; membership verified; archive extraction counts reported, not rerun here |
| Table 1 annotation questions | `docs/annotation-guidelines.md` | Initial documentation questions transcribed; final mixed-source reference distinguished |
| Table 2 stage evidence and rules | `docs/method.md`, `docs/rules.md`, `configs/heuristics/` | 105 final rules verified against packaged defaults; runtime restrictions documented |
| Table 3 initial annotation agreement | Ten worksheet CSVs and reproduction notebook | 354 agreements, 246 disagreements across 600 decisions; per-stage totals match |
| Table 4 heuristic evaluation | Original assessment, corrected prediction CSVs, notebook | All 24 printed values match: 96/95/95 eligible repositories |
| Table 5 386-repository stage totals | `results/README.md` | Supplied pooled positive/negative/unknown counts recorded; original pooled export still required for independent computation |
| Table 6 LLM evaluation | Exact prompts, saved outputs, notebook | Printed values match the author-confirmed correction to combined micro-F1 0.795 |
| Corrected Table 7 summary | `results/README.md`, original confusion totals | Heuristic FN 151/264/111 and FP 34/22/52; LLM FN 43/5/2 and FP 95/120/194 |
| Full 3,211-repository results | Complete population list | Full population reconstructed; full pooled stage totals, evidence and mode coverage pending original uploads |
| Minimal UI, installation and CLI | Main README, `demo.py`, tests | Maintained; no extra UI implementation retained |

The corrected PDF was not attached after the author confirmed the LaTeX corrections.
Therefore paper alignment means the attached draft plus those explicit corrections;
it does not certify unseen revisions to the final PDF.

## 2. Data and funnel findings

- Source verified against the public OpenAIRE deposition: release 11.1.1,
  [Zenodo record 20428976](https://zenodo.org/records/20428976), published 2026-06-08.
  The deposition confirms 730,346 software records and describes `software.tar` as
  research-software metadata. The exact archive SHA-256 is documented.
- Description matching uses case-insensitive whole words experiment/experiments,
  before repository deduplication. Links are syntax-normalized, not availability-verified
  at extraction. The reported intersection is 3,876 links and 3,211 unique repositories.
- The 386 association source records cover exactly the maintained 386 repository
  identities and contain 1,732 supplied `related_to` entries. These entries were not
  independently resolved and publication-type-checked. They preserve collection evidence,
  not a reproduced OpenAIRE relationship query.
- The 100 identities are contained in 386. The 2,825 final log identities are disjoint
  from 386 and their union has exactly 3,211. The reconstructed full-list ordering is
  documented; it is not represented as a byte-identical original extraction list.
- The supplied figure's obsolete release label and unverified-membership warning were
  corrected. The missing publication-selection query remains explicitly disclosed.
- Publication-associated selection can enrich Dissemination evidence; metadata association
  is not automatically a positive repository-level label and the population is not
  representative of all research software.

## 3. Cleanup performed

Removed the duplicate normalized 386 list (same identities after URL normalization),
derived paper-link CSV, superseded workbook with older predictions, outdated annotation/
anonymity audits, empty extra LLM result placeholder, and unused Docker files.
Renamed the original association JSON to `data/corpus/publication_associations.json`;
retained it because it is the source evidence for the publication-associated collection.
Updated documentation and tests to use the current CSV exports.

Required copies were retained deliberately: `data/final_agreement.csv` is the CLI
reference, the worksheet copy is provenance-bound, input lists support execution, result
lists document released populations, and packaged rule mirrors support installed usage.
`python_compat.py` supports Python 2 source syntax; it is active analysis code, not
obsolete experimental data. The classifier rules were not modified by this cleanup.

## 4. Numerical and implementation checks

- Original assessment predictions match all 1,800 restored heuristic decisions.
  Exactly 58 zero-filled unknowns across five repositories were restored to `?` across
  three modes; six pre-existing blanks were rendered as `?`. Genuine 0/1 values and
  repository order were preserved. Unknowns are never scored as negative labels.
- Table 4 micro-F1: documentation 0.70209340, code 0.41393443, combined 0.75707899.
- Table 6 micro-F1: documentation 0.82878412, code 0.79061977, combined 0.79454927.
  The latter rounds to 0.795. Different eligible cohorts must remain visible.
- All six notebook cells are rerun; saved outputs are checked against the current
  source calculations. Complete-scan flags remain independent of positive evidence.
- Full test suite, Ruff formatting/lint, mypy and the 105-rule checksum verifier are run.
  The optional browser smoke test is separate from the default offline suite. Its
  explicit run was blocked because the Playwright Chromium executable is not installed
  in this environment. HTTP/UI integration tests pass; browser rendering is not claimed
  verified here. Install Chromium with `uv run --frozen playwright install chromium`
  before running the opt-in browser test.
- The generated PDF is rendered and visually inspected; editable SVG, count JSON and
  pinned Matplotlib command are included. Figure rendering does not rerun the archive.

## 5. Anonymous distribution checks

The content scan checks author names/accounts, original personal source identifiers,
credential-like strings, personal absolute paths and archive metadata. No identifying
source workbook is distributed. The figure PDF has no author/date metadata. Public
third-party repository identities and source attributions remain scientific data.

The default `scripts/package_submission.py` creates a review derivative that excludes
Git history, workflow and agent metadata. It withholds externally traceable shared
conversation URLs and this artifact's development commit identifiers, retaining original
file hashes in `ANONYMOUS_PACKAGE.json`. Scientific rules, prompts, labels and analyzed
repository commit IDs remain intact; derivative checksum maps are refreshed as needed.
The extracted package is scanned and its benchmark reproduction rerun independently.

The development GitHub hosting account and Git history still identify its owner: do
not submit that URL as an anonymous artifact. Use the extracted review package with the
chosen anonymous service. No text scan guarantees anonymity against contextual inference.
The source repository retains shared conversations; the review package withholds their
links while preserving the exact prompts and saved labels.

## 6. Remaining inputs before a complete reproduction claim

1. Original per-repository result JSON/checksum files and run manifests for the 100,
   286 and 2,825 execution batches, preferably using `results/UPLOAD.md`. They are needed
   for pooled evidence exports, pinned commits, completeness and independent Table 5
   and full-3,211 aggregate computation. Received batch metadata is retained privately for later merging, not published
   as a separate result population or as totals for all 3,211.
2. Original full OpenAIRE repository list and extraction summaries to verify source-input
   hashes and reported funnel counts. The multi-GB software archive stays outside Git;
   independent reproduction requires downloading the documented exact release.
3. Original publication-selection query/script or an explicit disclosure that the 386
   are a supplied corpus with preserved association metadata, rather than an exactly
   reproduced fourth-stage extraction. Do not invent a replacement query to force 386.
4. Original captured repository inputs for exact offline classifier replay. Reacquiring
   main/master today can change the content and does not reproduce annotation-time state.
5. Remaining original LLM tool/retrieval/model settings, if available. Current saved
   outputs reproduce metrics; exact prompts alone do not reproduce nondeterministic
   hosted-model behavior. No fabricated inference settings are supplied.
6. The corrected final paper PDF for a final page/table/caption cross-check, including
   the corrected funnel caption. No artifact-review score or DOI is guaranteed.

## Recorded check outcome

- Offline suite: **228 passed, 1 optional browser test skipped**.
- Ruff lint/format: passed. Mypy: passed for 28 source modules.
- Final rule integrity: 105 rules and installed/default copies match.
- Original and extracted-review notebook executions: benchmark paper checks match.
- Extracted review content scan: zero matches for the six supplied identity/path patterns;
  no actual shared-conversation UUID URLs remain in distributed data/docs.
- Generated PDF: one page, no author/date metadata, visually checked after rendering.
- Opt-in browser smoke test: blocked by missing browser installation, as noted above.

## Second audit: simplified corpus presentation

- Result populations are only `benchmark-100`, `corpus-386` and `corpus-3211`.
  No `openaire-3211`, extra LLM result placeholder, batch result folder, obsolete
  workbook/audit, duplicate 386 list or legacy dataset filename remains.
- Received batch operational files were retained privately under local working storage;
  they are not discarded, mislabeled as whole-corpus results or presented separately.
- The benchmark now also has a consolidated `predictions.csv`: 100 identities, all
  three modes and all six stages, with original commit and scan-completeness fields.
- Exactly ten current worksheet CSVs are indexed individually in the workbook README.
  The source snapshot contains 13 tabs, three of which are superseded heuristic tabs.
  An eleventh current worksheet is not established by the supplied snapshot.
- The new `docs/rule-guide.md` explains the execution pipeline and every one of the
  105 maintained rules, including exact positives, exclusions, gates and scope.
- `python_compat.py` is maintained Python 2 source-reading support; its old module
  filename was renamed without removing compatibility functionality.
- Full original row-level results for the additional 286 remain unavailable. Therefore
  complete 386 and 3,211 pooled predictions cannot yet be generated or certified.
  Only metadata and aggregate tables are insufficient to recover these missing rows.
