# Original LLM analysis prompts

The exact user prompts used for the three shared ChatGPT assessments are included:

| Mode | Prompt | Shared conversation |
|---|---|---|
| Documentation-only | [documentation.txt](documentation.txt) | https://chatgpt.com/share/6ac48c78-b374-83ed-9cb1-4645974cbda0 |
| Code-only | [code.txt](code.txt) | https://chatgpt.com/share/6ac6c2cf-af50-83eb-988d-bf818eedc329 |
| Combined documentation/code | [combined.txt](combined.txt) | https://chatgpt.com/share/6ac6c262-f110-83ed-8f46-2e6f06c6d93e |

The links were supplied in H1 of the workbook's LLM sheets. Prompts were recovered from
the public shared conversation messages on 2026-10-22 and are preserved verbatim, including
original Markdown escaping, backslash-newline sequences, and the complete repository
lists. They are concrete original messages, not newly designed templates. No system or
developer prompt has been invented or represented as recovered.

`provenance.json` records prompt hashes, source links, public-page response hashes and
verification of all 100 output rows per mode against the exported worksheet. All 1,800
stage labels match the conversation tables. Full HTML/session/account configuration
payloads are not distributed.

The public pages report `gpt-6.1-sol-wm` in `model_slug` metadata. This is an observed
service identifier, not a parameter count, model-weight identifier, or guarantee that
ChatGPT will execute an identical model in a future replay. Temperature, seed, context
limits, hidden system instructions, exact repository snapshots and complete inference
configuration are not established by these user prompts alone.

The prompts ask ChatGPT to inspect repositories through available tools and output one
label table, without displaying its evidence. Matching tables verify transcription,
not whether every repository was adequately reviewed or every label is correct. The
notebook reproduces metrics from the saved tables; it does not rerun ChatGPT or certify
its evidence. Original LLM results are under results/benchmark-100/workbook/llm_*.csv.
Review the shared links themselves before anonymous distribution.

The six stage names are shared with the heuristic taxonomy, but the original prompt
wording and operational thresholds are not asserted to be identical to the final
heuristic rules. For example, the code prompt explicitly includes loading identified
research inputs as Collection evidence. Keep these original definitions visible when
interpreting comparisons; no prompt was retuned during this export.
