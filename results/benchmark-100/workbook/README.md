# Benchmark worksheet exports

These ten CSVs reproduce the selected **A1:G101** ranges from the user-supplied workbook
snapshot: one header row, 100 repositories, seven columns per file. Source workbook and
CSV SHA-256 hashes are recorded in `manifest.json`. The original Google Sheet and attached
workbook were not edited. The ten selected ranges were also checked against the exact
live Google Sheet on 2026-10-22: no value differences after treating numeric 0/1 and
0.0/1.0 as equivalent. Human and LLM CSVs preserve the attached values. The three heuristic CSVs restore unknown decisions from the original assessment, as described below. This is not continuous live sync.

| CSV | Source worksheet | Meaning |
|---|---|---|
| reviewer1.csv | research_lifecycle_benchmark_10 | Independent Reviewer 1 labels |
| reviewer2.csv | Hoja 10 | Independent Reviewer 2 labels |
| agreement.csv | agreement | Initial agreement indicators, not adjudicated labels |
| final_agreement.csv | final_agreement | Jointly adjudicated reference |
| llm_documentation.csv | Hoja 11 | Documentation-only ChatGPT predictions |
| llm_code.csv | Hoja 12 | Code-only ChatGPT predictions |
| llm_combined.csv | Hoja 13 | Combined-input ChatGPT predictions |
| heuristics_documentation.csv | benchmark_100_heuristics_doc_la | Explicitly named latest documentation heuristic export |
| heuristics_code.csv | benchmark_100_heuristics_code_l | Explicitly named latest code heuristic export |
| heuristics_combined.csv | benchmark_100_heuristics_both_l | Explicitly named latest combined heuristic export |

The three named latest heuristic tabs supersede Hoja 14, Hoja 15 and Hoja 16. Those older
tables are omitted. Excel does not supply reliable per-tab modification times: selection
uses the explicit latest-tab names, not a guessed timestamp or highest sheet number.
Reviewer numbering was verified against all 600 labels per reviewer in the existing
independent annotation CSV. Personal names, out-of-range notes, styling and hyperlinks
are not included in the seven-column exports.

Cell text is preserved: numeric `0.0`/`1.0` values are not relabeled, and blank and
`Unverified` cells stay distinct from zero. The agreement sheet exports cached formula
results. Its summary row 102 and the conversation links in H1 are deliberately outside
the CSV range. Missing cached formula values cause export to fail rather than invent data.

## Shared LLM conversations and exact prompts

| Mode | Shared conversation | Original user prompt |
|---|---|---|
| Documentation | https://chatgpt.com/share/6ac48c78-b374-83ed-9cb1-4645974cbda0 | [documentation.txt](../../../prompts/documentation.txt) |
| Code | https://chatgpt.com/share/6ac6c2cf-af50-83eb-988d-bf818eedc329 | [code.txt](../../../prompts/code.txt) |
| Combined | https://chatgpt.com/share/6ac6c262-f110-83ed-8f46-2e6f06c6d93e | [combined.txt](../../../prompts/combined.txt) |

The three URLs come from H1 of their respective source sheets. The original prompts
were recovered from the public shared pages. Every output label in the three public
conversation tables was checked against these CSVs: **1,800/1,800 labels match**.
Prompt hashes and retrieval provenance are in [prompts/provenance.json](../../../prompts/provenance.json).
Review the shared pages for suitability before publishing an anonymous review artifact.

## Reproduce and compare with the draft

Run [the notebook](../reproduce_paper.ipynb) or its standard-library Python equivalent:

```bash
uv run --frozen python results/benchmark-100/reproduce_paper.py
```

The heuristic CSVs restore **58 zero-filled unknown decisions** to `?` and render six
existing blanks as `?`. All genuine binary decisions and the supplied repository order
are unchanged. Original assessment predictions and independent scan-completeness flags
are retained in `../assessment/`; its correction log lists every changed cell.
`manifest.json` records both the original source-export and corrected CSV hashes.
The source workbook and live Google Sheet were not changed.

Evaluation uses the original scan-completeness flags: **96 documentation, 95 code,
95 combined repositories**, reproducing Table 4. A known positive remains 1 even if
its scan is incomplete; incomplete scans are excluded from complete-scan metrics.

The LLM sheets reproduce Table 6 to the printed precision including the author-confirmed correction: combined micro-F1
is 0.79454927, which rounds to **0.795**.

Re-export from the exact supplied workbook:

```bash
uv run --frozen python scripts/export_workbook_results.py \
  --workbook /path/to/the/source-workbook.xlsx \
  --output /path/to/raw-workbook-export
```

The source mapping and workbook hash must be reviewed when the input changes. This
command regenerates the uncorrected source snapshot in a separate directory. It does not
restore uncertainty; do not overwrite the corrected submission CSVs with raw exports.
