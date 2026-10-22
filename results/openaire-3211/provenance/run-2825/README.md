# Operational provenance for the additional 2,825 repositories

These files contribute to the single full OpenAIRE 3,211-repository result collection;
this execution batch is not a separate published population.

Original `manifest.json`, `summary.json` and `progress.json` are preserved unchanged.
`failures.csv` extracts diagnostics for all 396 failures from the supplied stop records.
`provenance.json` records original input-file hashes, extraction scope and limitations.
The original progress log has repeated checkpoint entries; taking the final entry for
each repository yields 2,825 unique attempts, matching the supplied status totals.

| Outcome | Repositories |
|---|---:|
| Complete | 2,254 |
| Partial | 175 |
| Failed | 396 |
| Total | 2,825 |

Failures include 234 timeouts, 161 inaccessible main/master pairs and one ValueError.
Do not label inaccessible branches as deleted repositories without further evidence.
The run used hybrid acquisition, main then master, a 120-second deadline and a
10 MiB file cap. Original code/catalog hashes remain in the manifest; the source
checkout was dirty, so its commit alone does not reconstruct the executed checkout.

Session wall time was 71,676 seconds (19.91 hours). Resumed checkpoints prevent using
this as an unbiased mean processing time per repository. No full-population F1 is
claimed. Final prediction, completeness, commit and evidence exports await original
per-repository result JSON and checksum files. Failed/partial outcomes remain in the
population, and unknown decisions must not be converted to zero.
