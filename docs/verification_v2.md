> Historical V2 verification record. Superseded current status and measured reference comparisons: [V3 report](implementation_report_20261015.md).

# Executed v0.2.0 verification and unfinished research gates

Producing implementation commit: `4fbf34205e59834995cacd0968eb30ecfd834633`.

Executed in Python 3.12.14, uv 0.12.23 with frozen dependencies:

* 105 pytest tests passed, covering all six stages, every documentation rule/layer's affirmative and negative examples, secondary code counterexamples, negation/third-party/roadmap scope, wrapped line provenance, mode isolation and canonical reruns.
* Synthetic Agreement Final workbook tests verify 100 repositories/600 pairs, exact sheet selection, original workbook integrity, original URLs/row IDs/cells, missing/ambiguous/duplicate labels, exact-workbook/import-mapping approval, candidate status and clean release export.
* Whole-repository splitting tests verify deterministic order-independent assignments, approximate marginal stratification, development-only label export, and actual development runs that never analyze test snapshots. Frozen-guard tests reject modified rules and repeat final runs while permitting reproduction-only access.
* Ruff lint and formatting checks passed. Mypy passed for all 12 source modules.
* Built the v0.2.0 wheel, installed it with no dependencies in a separate environment, and ran isolated Python (`-I`) documentation-only analysis successfully using its packaged catalogs.
* Generated `benchmark/results/synthetic-v2` from a clean checkout of the producing commit. Its manifest records the source revision, catalog/input hashes, runtime and lock hash. Version 1 reference artifacts remain unchanged.
* Two offline benchmark reruns matched all 14 canonical artifacts byte-for-byte. Semantic artifacts also matched the new reference. Platform/machine metadata is outside canonical comparisons. Original producing-manifest provenance is retained.

The fixture dataset remains synthetic-v1; synthetic-v2 names its new classifier/report reference run. Documentation, code and combined fixture metrics are software regression results, not human agreement estimates. No test-set model selection was performed.

The revised software workflow is verified. The publication-quality **human research artifact is still incomplete**: no real workbook imported, no human consensus verified, no approved codebook provided, no actual sampling/historical revisions established, no human development evaluation performed, and no final held-out run executed. Therefore agreement improvements and human benchmark performance cannot be reported. Full live acquisition, Docker build/digest freeze and anonymous release remain unexecuted.

Current one-command offline regression reproduction:

```bash
uv run --frozen python -m lifecycle_mapper benchmark verify --config configs/synthetic.yaml --workspace local/reproduction-v2-check --reference benchmark/results/synthetic-v2
```

Use a new workspace directory. For actual frozen research inputs, use the analogous `benchmark verify --config configs/local-heldout.yaml` command after the single approved final run and preserve its frozen protocol and evaluation ledger. See evaluation_protocol.md for the complete custodian/development/freeze procedure.
