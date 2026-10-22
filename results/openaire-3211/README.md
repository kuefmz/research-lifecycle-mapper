# OpenAIRE 3,211-repository collection

Status: complete repository population reconstructed and validated; operational metadata
received for the 2,825-repository batch. Detailed pooled results pending upload.

This population combines the 386-repository corpus and the remaining 2,825 repositories:
100 + 286 + 2,825 = 3,211. The collection inclusion relation has been verified by
normalized repository identity; detailed results await merging. All three execution batches contribute
to one final population; subset lists are not published as standalone collections.

After verification, this folder will contain the full `repositories.txt`,
`predictions.csv`, `repository_status.csv`, `evidence.csv`, `summary.json`, and
`provenance.json`. Preserve unknowns, failures, mode completeness and pinned commits.
Reference-based accuracy is not claimed for this unannotated population.
See [upload instructions](../UPLOAD.md).

`repositories.txt` now contains all 3,211 unique identities: the verified disjoint union
of the 386 list and 2,825 final log entries. Its ordering and reconstruction provenance
are documented in `repository_list_provenance.json`; the original OpenAIRE list is
still requested for direct comparison. Operational metadata and failure diagnostics
are retained under `provenance/run-2825/`. This is not yet a complete evidence export.
