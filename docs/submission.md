# Anonymous submission package

This artifact supports reproduction of the heuristic analyses in the submitted MSR 2027
paper. Before freezing the review package:

1. Copy original local run exports and evidence into the locations described in results.md.
   Complete the experiment README for each result group, including failures and denominators.
2. Supply exact historical LLM prompts and inference configuration under prompts/ and
   results/llm/, or disclose their absence and restrict the corresponding paper claims.
3. Verify input/reference/rule hashes, cohort membership and compatibility before pooling runs.
4. Confirm the original human annotation instructions and final reference evidence scope.
5. Run tests and verify the final rule catalog, then stage the intended distribution files.
6. Create a history-free archive:

```bash
uv run --frozen python scripts/package_submission.py
```

The script packages tracked files, excludes Git history and workflow/agent metadata, and
writes `dist/submission.zip` plus its SHA-256. Untracked results are not included: inspect
`git status` and stage intended result files before packaging. Do not stage tokens or raw
multi-GB archives.

Extract and inspect the ZIP. The original host account and Git history identify its owner;
the working repository must not be used as the anonymous submission link. Publish the
archive contents through the chosen anonymous service. Check names, accounts, emails,
absolute paths, workbook XML/properties, logs, manifests and external links. A local scan:

```bash
uv run --frozen python scripts/audit_anonymity.py PATH_TO_EXTRACTED_PACKAGE \
  --forbid YOUR_NAME --forbid YOUR_EMAIL --forbid YOUR_ACCOUNT
```

Preserve original research results privately. If identifiable metadata requires removal,
create a separate sanitized derivative, document transformations and retain original hashes.
Never silently rewrite scientific manifests or remove required third-party attribution.
No automated scan guarantees anonymity against contextual inference.

Verify current venue requirements before submission. A review-ready package requires the
actual results and prompt materials, not just their placeholders. No artifact-review score
or archival DOI is promised. Add the persistent identifier after the preserved release is
deposited, using metadata compatible with the review stage.
