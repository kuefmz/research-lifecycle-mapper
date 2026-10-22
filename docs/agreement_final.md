# Human reference and annotation provenance

`data/final_agreement.csv` is the authoritative supplied table: 100 repository identities,
six binary labels each, in the supplied row order. Use it with corpus --reference and
assess --reference. It is a comparison/display input, never a classifier feature.

The corrected workbook has distinct Reviewer 1/Reviewer 2 independent annotations and a
jointly adjudicated final_agreement sheet. Preserve both. Consensus does not mean the
initial reviewers agreed independently; initial reliability must be computed from their
original cells. `data/annotation_audit_20261020.json` records the earlier machine audit;
verify its bound workbook before reusing statistics. `data/final_agreement_correction.json`
records CSV/workbook/JSON agreement at import.

The procedure was intended to focus on documentation, but the final evidence audit
includes mixed sources. Do not advertise a verified documentation-only ground truth or
independent source-code ground truth without further source-specific adjudication.
The human codebook's original version and annotation-time repository commits remain
separate provenance questions. All 100 repositories informed rule development.

The legacy formal import config is retained for old manifests; the current CSV route does
not require fabricated custodian approvals. See results.md for exact observed evaluation.
