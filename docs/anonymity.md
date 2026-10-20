# Anonymous review artifact

Current public files use reviewer1 and reviewer2, anonymous contributor metadata and relative project links. The all-sheet workbook is an anonymous derivative with a new checksum. Personal source-workbook URLs and author-owned project/upstream links are omitted from the distributed files. Third-party repository identities remain scientific data and are not replaced merely because they name their developers.

The original hosting account, commit author metadata and prior history remain identifying. Do not cite the personal GitHub URL in the submission or expose its history through the review artifact. Use the anonymous repository service or a clean source archive without .git. This update does not rewrite existing history or claim to anonymize the hosting account.

Run scripts/audit_anonymity.py against the source tree with private --forbid patterns supplied in the local terminal; pattern text is never written into its JSON report. The scan checks filenames, text and XML inside ZIP/XLSX archives. Supply author names, usernames, emails and original workbook IDs. Inspect notes, properties, screenshots, logs, evidence URLs and exported datasets as well. A zero-match scan is a scoped mechanical check, not proof that identity cannot be inferred from research context.

Before submission, inspect the actual anonymous mirror (including binary downloads) and keep the version stable. Do not expose a named Zenodo record through the review copy. A submission-time DOI must point to an anonymous record with anonymous metadata; otherwise release the identified record after review. Preserve exact artifact/data versions and checksums.
