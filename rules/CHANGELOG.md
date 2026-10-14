# Rule catalog changelog

## 0.1.0-candidate

Twelve independently authored, source-isolated, conjunctive candidate rules: one documentation and one Python implementation rule per stage. No source path, dependency, README presence, unit test, or isolated generic keyword can trigger a label. Supporting conditions are recorded but never qualify a stage on their own. Exclusion conditions veto a match.

Method is scoped to scientific models/algorithms/analytical methods, not the upstream Implementation category. This interpretation is provisional until the human codebook is supplied and adjudicated. All rules retain machine-readable conceptual justifications and `unadjudicated-candidate` status.

Catalog files use JSON syntax, a subset of YAML. The packaged catalog under `src/lifecycle_mapper/rules/` must be byte-identical to the research catalog. `scripts/build_catalog.py` contains the initial authoring definitions; after any change regenerate both copies, update the version and this changelog, and test.
