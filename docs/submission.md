# Anonymous submission and release status

The maintained tree supplies the final deterministic method, data-generation tools,
human reference, minimal UI, tests and documented destinations for results/prompts.
It is **not yet a complete research release**: exact historical LLM prompts/configuration
and original local research outputs still need to be supplied. Do not claim those are
bundled because placeholder directories exist. No artifact score or DOI is promised.

## Before submission

1. Upload original runs/exports and fill each results README (docs/results.md).
2. Supply exact historical LLM prompts and inference manifests, or disclose nonavailability
   and narrow the paper claims (prompts/README.md).
3. Verify source archive/reference hashes, cohort membership and pooled-run compatibility.
4. Confirm original human annotation instructions and reference evidence scope. The
   implementation's codebook is not retroactive proof of the original reviewer protocol.
5. Build an anonymous distribution with `python scripts/package_submission.py`.
6. Audit that distribution, including workbook metadata, logs, manifests and paths.
7. Check actual venue anonymity/artifact instructions and page limits before submission.
8. Record the final archive hash; obtain and document an archival DOI when deposited.

## Identity handling

This working repository's hosting account and Git history identify its owner. A clone
of that history is not anonymous even if README names are removed. The packaging script
creates a history-free ZIP, excludes local/transient state and transient state,
and does not claim to remove all identities. Publish its contents through the chosen
anonymous service. Never rewrite the original Git history or raw result manifests to
hide provenance. If raw paths/metadata identify researchers, retain originals privately
and document a separately sanitized distribution and hashes. Preserve third-party
citations, dataset repository identities and required license attribution.

The existing audit script accepts forbidden patterns without hardcoding private names:

```bash
uv run --frozen python scripts/audit_anonymity.py PATH_TO_EXTRACTED_PACKAGE \
 --forbid YOUR_NAME --forbid YOUR_EMAIL --forbid YOUR_ACCOUNT
```

Inspect matches manually; legitimate third-party names are not automatically leaks.
No scanner can guarantee anonymity against searchable data or methodological fingerprints.
