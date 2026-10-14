# Agreement Final ingestion and approval

The supplied brief identifies `Agreement Final` as the final reconciled worksheet, but the workbook is not attached. This implementation selects that exact sheet and does not substitute the independent annotation sheet. Its actual layout and approval status remain unverified.

`configs/agreement-final-import.yaml` is an **unverified mapping template**, not a statement of the real workbook layout. Inspect the supplied workbook, identify its header row, repository URL and original row-ID columns, and map the six stage columns explicitly. `expected_headers` must match every mapped column. Only wide rows are currently supported. If the real sheet uses long rows, merged multirow headers, hyperlinks without literal URLs or a different schema, a reviewed mapping extension is required; never guess which columns are gold.

```bash
uv run --frozen python -m lifecycle_mapper benchmark import original.xlsx --config configs/agreement-final-import.yaml --output local/imports/final-v1
```

This reads the original unchanged, validates 100 unique repositories and six literal/mapped binary labels per repository, and records original URLs, row IDs, physical worksheet rows, cell addresses, raw labels, normalized labels, source checksum, exact import config/checksum and benchmark version. Missing/ambiguous labels, duplicates, mapped formulas/errors, changed headers and invalid URLs fail. No private notes/unmapped columns are exported. A real count correction requires a documented researcher reference; research evaluation still follows the approved 100/600/247 protocol until that protocol is explicitly revised.

The import is candidate by default even if the sheet is named Final. An externally approved JSON record must contain `status: approved`, `worksheet: Agreement Final`, the exact `workbook_sha256`, the exact `import_config_sha256` (including label normalization), and a nonempty actual `approval_reference`. Pass it through `--approval PATH`. Provisional or unresolved rows cannot be promoted by title, agreement between annotators or classifier predictions. The software verifies the supplied record's integrity and consistency, not whether an approval was genuinely granted.

Output: canonical `benchmark.csv`, `provenance.json`, and a candidate `manifest.json`. That manifest remains pending until revisions, snapshots, sampling, codebook and independent-label provenance are supplied. It contains no fabricated commits. The legacy `annotations import` command separately preserves independent labels and disagreements; it is not the gold source. Research validation now additionally requires `consensus_provenance`, `consensus_provenance_sha256`, and `consensus_table`, validates that the approved source is Agreement Final, and checks every gold value against its exact table. Independent-label and consensus tables must agree through explicitly reviewed normalization; no automatic adjudication is performed.

## Eventual publication export

After consensus approval, provide a separate release JSON with `status: approved`, exact `consensus_table_sha256` and an actual `release_reference`:

```bash
uv run --frozen python -m lifecycle_mapper benchmark export --imported local/imports/final-v1 --release-approval local/release.json --output local/public-benchmark-v1
```

The clean export includes repository, stage and approved label only, plus checksums/release provenance. Private notes, original row IDs, annotator names and workbook metadata are excluded. Repository identities can still reveal projects/authors; publication/anonymity review remains mandatory. The command prepares local files and does not publish them. No real benchmark import, consensus approval or public benchmark export has occurred.
