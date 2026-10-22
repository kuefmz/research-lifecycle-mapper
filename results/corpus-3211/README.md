# 3,211-repository corpus

`repositories.txt` contains the complete 3,211-repository population. Its normalized
identities are unique and contain the full 386 corpus and 100 benchmark. Ordering and
source-list reconstruction are recorded in `repository_list_provenance.json`.

Status: original complete pooled predictions and evidence are pending transfer.
The current inputs do not permit final per-repository results for this corpus to be
published. Execution logs and partial run metadata must not be treated as complete
results. No unavailable prediction is replaced with zero.

Once original files are supplied, this folder will contain one `predictions.csv`,
`repository_status.csv`, `evidence.csv`, `summary.json` and `provenance.json` for the
whole corpus. Execution subsets will not be separate result collections.
Full-corpus precision/recall/F1 require human reference labels and are not claimed.
See [../README.md](../README.md) and [../UPLOAD.md](../UPLOAD.md).
