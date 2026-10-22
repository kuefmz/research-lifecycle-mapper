# Maintained file inventory

## Runtime

- acquisition / git_acquisition / execution / repository_worker / telemetry: inventory,
  retrieval, pacing, subprocess deadline and diagnostics.
- analysis / documentation / notebooks / brace_code / portable_code / legacy_python /
  source_languages / text_decoding: eligibility-aware evidence matching.
- language_catalog.json and its LICENSE: pinned language recognition data and attribution.
- corpus / batch / canonical / bundles: scalable corpus execution, canonical integrity,
  historical batch exports and snapshots.
- reference / annotations / consensus / comparison / assess / paper_summary: source
  annotations, observed reference agreement, diagnostics and paper exports.
- openaire: maintained software.tar extraction/filtering.
- demo: minimal advertised local UI; cli and __main__: entrypoints.

Compatibility modules remain because deleting them would break saved data, importers or
regression tests: benchmark / protocol / dataset provide earlier synthetic/formal workflows;
web / ui/index.html provide the older UI; publications / metadata_publications / funnel
provide exploratory association workflows. They are not additional maintained scientific
methods. Current method/evaluation documentation overrides older draft narratives.

## Data/configuration

The final profile and its exact catalog/checksums live in configs/consolidated-development-v5.4.
Other top-level config files support annotation imports and synthetic/protocol verification.
Root rules and packaged rules are exact final mirrors, verified automatically.
`tests/fixtures/legacy-profiles` holds historical test inputs only, not selectable paper methods.
`benchmark/synthetic`  are software test fixtures, not research results.
Other benchmark manifests/provenance are legacy formal workflow records.

`data/README.md` describes retained human/source data. Earlier annotation audits, source
workbook, independent labels and consensus remain separate; source data are not silently
rewritten. Older metadata-overlap artifacts are explicitly exploratory. Final local results
belong under results and/or their original data/runs paths as described in docs/results.md.

## Scripts

- select_repositories.py: ordered cohort subtraction and normalization audit.
- verify_final_profile.py: frozen catalog hashes and mirror identity.
- index_results.py: streamed content hashes after researcher result upload.
- package_submission.py: history-free distribution archive from tracked submission files.
- audit_anonymity.py: researcher-supplied forbidden-pattern audit including workbook XML.
- compare_repository_cohorts.py: older metadata candidate overlap reproduction.
- build_language_catalog.py: language-catalog maintenance, not required for ordinary reproduction.
- build_synthetic.py: synthetic-fixture maintenance, not human labels.
- test_ui_dom.cjs: legacy UI DOM verification helper.

Development builders, intermediate score exports and paper-writing notes were removed from
the active tree. cleanup-provenance.json inventories removals; the source commit retains them.
