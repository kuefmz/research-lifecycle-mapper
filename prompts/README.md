# LLM analysis prompts and provenance

**Status: original prompts not present in the tracked repository at cleanup.**
The workbook contains archived `chatgpt_documentation`, `chatgpt_code`, and
`chatgpt_combined` outputs. Those outputs are not evidence of an exact original prompt,
model version or input-selection procedure. No reconstructed prompt is presented as used.

Copy the exact historical prompts here as `documentation.txt`, `code.txt`, and
`combined.txt`; preserve system/developer/user messages and interpolation templates.
If modes shared one template, retain it once and document mode-specific substitutions.
Record SHA-256 hashes and source evidence (original export, API script or retained chat).
If unavailable, disclose the gap instead of inventing a replacement.

For each original experiment complete this record:

| Field | Required content |
|---|---|
| Prompt files/hashes | Exact original text and message ordering |
| Source provenance | Where exact text was recovered; experiment date |
| Model | Provider, exact model identifier/version/date |
| Parameters | Temperature, top-p, seed if used, output limits, tools |
| Input preparation | Included files, ordering, branch/commit, truncation, notebook handling |
| Retrieval/context | Selection algorithm, context limit, chunking/aggregation |
| Output handling | Schema, retries, parsing failures, unverified decisions |
| Evidence validation | Whether paths/snippets were independently checked |
| Evaluation | Reference hash, repository identities and eligible cohort |

Place raw model outputs and inference manifests in `results/llm/`. The deterministic
heuristic pipeline does not depend on these missing LLM materials. The LLM experiment
cannot yet be reproduced from this repository alone.
