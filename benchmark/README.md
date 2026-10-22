# Verification fixtures and legacy formal manifests

The current human reference is ../data/final_agreement.csv. Evaluate observed saved runs
with lifecycle_mapper.assess as described in ../docs/results.md.

This directory retains:

- synthetic/: five small artificial snapshot fixtures and their manifest.
- versions/baseline-rules/: explicit baseline used by configs/synthetic.yaml, and an older
  split record for compatibility. A split file does not establish an untouched holdout.
- manifest.json, annotations/, manifests/, snapshots/, provenance/: legacy formal
  benchmark manifest/import workflow records. Their pending declarations must not be
  filled with fabricated approvals, commits or human protocol history.

The maintained method and final local research results are documented elsewhere. Do not
report synthetic fixture accuracy as empirical accuracy on research repositories.
