# Rule catalog changelog

## 0.1.0-candidate

Twelve independently authored, source-isolated, conjunctive candidate rules: one documentation and one Python implementation rule per stage. No source path, dependency, README presence, unit test, or isolated generic keyword can trigger a label. Supporting conditions are recorded but never qualify a stage on their own. Exclusion conditions veto a match.

Method is scoped to scientific models/algorithms/analytical methods, not the upstream Implementation category. This interpretation is provisional until the human codebook is supplied and adjudicated. All rules retain machine-readable conceptual justifications and `unadjudicated-candidate` status.

Catalog files use JSON syntax, a subset of YAML. The packaged catalog under `src/lifecycle_mapper/rules/` must be byte-identical to the research catalog. `scripts/build_catalog.py` contains the initial authoring definitions; after any change regenerate both copies, update the version and this changelog, and test.

## 0.2.0-candidate

Documentation is primary. Replaced six narrow documentation V1 rules with 18 V2 explicit/contextual/workflow rules, each requiring affirmative repository scope plus activity/object evidence. Added wrapped sentences, heading inheritance, negation/future/third-party exclusions and structured dimensions. Six code V1 rules are unchanged. Changes use synthetic examples and supplied provisional definitions; no human benchmark labels were inspected or optimized.

## 0.3.0-candidate

Retains all 24 V1/V2 rules and adds 18 V3 rules: six repository-scoped documentation activity/object families, six Python operation/context families, and six conservative R/Julia/MATLAB/shell families. Documentation accepts ordinary disciplinary wording without requiring the literal word “research”; associated linked-paper descriptions support dissemination. Negation/future/delegation and installation/dependency exclusions remain. Python statement rules require both matches within one AST statement; function rules retain their function boundary. Strings/comments and software-test paths cannot trigger implementation evidence.

Each new family has affirmative and negative fixtures. Rule status remains `unadjudicated-candidate`: empirical agreement does not approve the human codebook. Baseline catalogs are preserved at `benchmark/versions/baseline-rules`; the fixed split and measured report accompany the change. V3 catalogs are authoritative authoring definitions. `scripts/build_catalog.py` preserves them while rebuilding legacy definitions and synchronizing the packaged copy.
