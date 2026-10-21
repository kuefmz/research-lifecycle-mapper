# Consolidated development v5.4

105 conjunctive rules. Rebuild with `python scripts/build_consolidated_profile.py`. `rule_catalog.csv` documents every exact runtime rule; earlier profiles remain unchanged. Freeze this profile and its implementation commit for the next run. Later changes require a new version and fresh run directory.

## Changes motivated by the supplied 61-repository log

1. Acquisition policy 6 excludes *.min.js, *.min.css, their source maps and *.js.map/*.css.map before download. Ordinary readable JavaScript remains eligible. Explicit parallel-corpus names data_pseudo/data_val/data_train/data_test and polyglot variants with .e/.f suffixes are excluded only under data/other_data/polyglot_data/train/test directory components. Ordinary Fortran remains eligible. These are filename/path proxies and may miss other datasets; exclusions remain inventoried.
2. The two-minute wall-clock deadline, 10 MiB command-line cap, immediate-folder TXT threshold and lossless recorded legacy decoding remain in place. Previous snapshot policies retain their eligibility/decoding behavior.
3. Portable scanning computes file-context eligibility once per rule/file rather than once per statement. Newline lookup uses precomputed positions. This avoids repeated full-file scans without changing ordinary matching semantics.
4. Wolfram .nb/.wl/.wls files use a linear nested-comment/string masker, retaining offsets and physical lines. Serialized notebook BoxData/RowBox expressions are not reconstructed: those code scans explicitly remain incomplete. This avoids both slow generic lexing and a false claim of semantic notebook coverage. Malformed Wolfram text is likewise an explicit coverage gap.
5. Unavailable notebook/file reasons propagate into mode coverage_issues and progress logs rather than an unexplained partial status.
6. Collection distinguishes actual acquisition/recording provenance from downloading an existing dataset or hypothetical collection discussed as background. Broad Collection workflow matching is sentence-scoped and requires local affirmative scope.
7. Documentation Method recognizes explicit scientific implementation objects and numerical capabilities. Merely accompanying a paper or training an unspecified model remains insufficient. Research train/test/evaluation commands, reported numeric metrics and linked research artifacts gain explicit rule families.
8. Code gains ODE solvers and configured ODE simulation runs, scientific-library fit calls, numerical optimization/estimation calls, statistical comparison and cross-validation calls. These require actual call syntax and argument/context evidence; imports, comments and strings alone do not qualify. File-level library context is co-occurrence, not interprocedural data-flow proof.

## Validation and limits

`data/reports/consolidated-v54-development-audit.json` includes all 61 supplied run records, denominators, baseline comparisons, and before/after root-README evidence review for 56 complete repositories. The paired README check improves micro-F1 from 0.6686 to 0.7115. Those are root-README development comparisons, not full-repository results or an independent test. The original logged full-scan documentation F1 was 0.6902; those inputs differ and must not be compared as a controlled before/after result.

No repository-specific exceptions or reference-label inputs exist in the classifier. No promise of 80–90% F1 is made. Under-specified references and evidence-scope disagreements remain listed for review rather than silently changing labels. Collection restrictions may lower recall; remaining Method/Evaluation gaps must be disclosed. Source-only positives may validly disagree with documentation labels.

After the active baseline run finishes, use this profile in a fresh directory with the same 100 repositories, exact supplied order, main/master branch policy and resource limits. Run export/assess without replay for final metrics. Preserve both runs; report complete/partial/failed coverage and baselines alongside F1. Do not pool results across profiles or present development scores as held-out performance.
