# Annotation import and research manifest specification

## Workbook or CSV input

XLSX requires a worksheet named `annotations` with these exact headers in this order. CSV uses UTF-8 and the same schema:

```csv
repository,stage,reviewer2,reviewer1,proposed_consensus,approved_consensus,approval_reference
```

No actual annotation rows are included in this specification. `repository` is `owner/name`; stage is exactly one of Collection, Processing, Method, Experimentation, Evaluation, Dissemination. There must be one row per repository-stage, no duplicates, exactly 100 repositories/600 rows, and all six stages per repository. Independent labels are literal `0` or `1`. Proposed/approved consensus may be empty, `0` or `1`. Approved values require an explicit nonempty approval reference, and a reference without an approved label is rejected. Formulas are rejected rather than reading potentially stale cached values. A workbook in a different layout must first be explicitly mapped to this schema; retain its original checksum and the transformation provenance separately.

The importer computes independent disagreements from the supplied complete normalized table. An optional --expected-disagreements value checks a version-specific declared count; no count of 247 is hard-coded. The research validator compares the actual table count with provenance. Original missing cells must not be guessed. The source is read-only; imports go into new versioned directories.

## Research manifest

Provide `schema_version: 1`, `kind: research`, `status: approved`, `version`, `codebook_version`, the exact six-stage `stages` array, and these project-local references/checksums:

* `annotations`: path to normalized annotation CSV.
* `annotation_provenance` and `annotation_provenance_sha256`: imported provenance JSON and its SHA-256.
* `sampling_documentation`, `sampling_documentation_sha256`, `sampling_verified: true`: actual source, selection/inclusion procedure, restrictions and validation history; this field must not be asserted without review.
* `codebook`, `codebook_sha256`, `codebook_approval_reference`: approved versioned human codebook and decision reference.
* `repositories`: exactly 100 records with canonical `repository`, immutable 40-hex `commit`, `snapshot` directory, `snapshot_sha256` for its manifest, and `labels` mapping the six stages to literal JSON integers 0/1. Every label must agree with the approval-referenced normalized table.

Paths are relative to the manifest directory and must stay inside it. Place provenance/tables/snapshots under that directory; `..`, absolute paths and symlink escapes are rejected. The JSON manifest should be serialized canonically with sorted keys/UTF-8/LF. Copying existing snapshots requires no new acquisition.

For held-out evaluation, include `held_out_approval_reference` and `used_for_rule_development: false`; config must declare all development repository IDs. A benchmark used to refine rules must instead use `evaluation_role: exploratory`. The held-out declaration must be supported by real protocol records.

Import alone does not generate the research manifest because the repository revisions, approved sampling/codebook and release decisions are currently absent. The team must supply those facts explicitly; they cannot be inferred safely from the workbook or current GitHub branches.

## v0.2.0 protocol update

Documentation-only is primary, with development macro-F1 for model selection. Documentation uses explicit, contextual and demonstrated-workflow families with activity/object/scope/polarity records; wrapped prose and inherited Markdown/AsciiDoc/reStructuredText headings are supported. Production matching is deterministic and uses no gold labels or external models. Agreement Final is the required candidate consensus worksheet; independent labels remain separate provenance. See `agreement_final.md`, `evaluation_protocol.md` and `rule_change_protocol.md` for the current importer, split, freeze, mismatch and final-run procedures. Historical one-line rules and unsplit held-out declarations are superseded. This V2 paragraph is historical. The final documentation reference is now jointly adjudicated and observed operational comparisons exist; see docs/annotation_status_20261020.md and the V3 report. Sampling, human codebook mapping and blinded evaluation remain separate issues.
