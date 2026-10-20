# Benchmark inputs and status

Current reference: the corrected anonymous workbook has 600 valid independent decisions, 354 agreements, 246 disagreements and no missing values. reviewer1 and reviewer2 jointly adjudicated final_agreement. See docs/annotation_status_20261020.md and data/annotation_audit_20261020.json. Live acquisitions use main, otherwise master, pinned to an immutable commit. Historical protocol descriptions below retain their original context.


The 100-repository human benchmark is **not available** in this repository. Its manifest is pending and the research command fails explicitly. Do not replace it with synthetic labels or upstream heuristic caches.

The research brief reports independent labeling by reviewer2 and reviewer1, 600 repository-stage pairs and 247 initial disagreements. These counts are not yet verified from original data. Human adjudication and approval are required before final gold labels can be evaluated.

Available inputs: a five-repository synthetic benchmark, original test-content snapshots, synthetic labels, configuration and generated synthetic reference artifacts. Synthetic SHA-shaped revisions and repository identifiers are explicitly fabricated fixture identities, not historical research revisions. Their evidence links are format examples, not live evidence locations.

Missing research inputs: original workbook/checksum; actual sample identities and revisions; sampling frame/selection documentation; independent rows/disagreement records; approved codebook and final consensus; input snapshots; publication/distribution permissions. See `provenance/import_specification.md` and `provenance/annotation_provenance.md`.

Keep source workbooks immutable. Import to a new versioned directory and record the checksum. Private annotation notes remain outside the public release. `annotations/`, `manifests/` and `snapshots/` currently contain status documents rather than invented data.
