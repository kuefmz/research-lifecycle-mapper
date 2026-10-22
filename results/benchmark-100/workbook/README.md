# Benchmark worksheet exports

These ten CSVs contain the released annotation and prediction tables for the
100-repository benchmark: one header row, 100 repositories and seven columns per file.
`manifest.json` records source mapping and SHA-256 checksums.

| CSV | Source worksheet | Meaning |
|---|---|---|
| reviewer1.csv | research_lifecycle_benchmark_10 | Independent Reviewer 1 labels |
| reviewer2.csv | Hoja 10 | Independent Reviewer 2 labels |
| agreement.csv | agreement | Initial agreement indicators, not adjudicated labels |
| final_agreement.csv | final_agreement | Jointly adjudicated reference |
| llm_documentation.csv | Hoja 11 | Documentation-only ChatGPT predictions |
| llm_code.csv | Hoja 12 | Code-only ChatGPT predictions |
| llm_combined.csv | Hoja 13 | Combined-input ChatGPT predictions |
| heuristics_documentation.csv | benchmark_100_heuristics_doc_la | Documentation-only heuristic predictions |
| heuristics_code.csv | benchmark_100_heuristics_code_l | Code-only heuristic predictions |
| heuristics_combined.csv | benchmark_100_heuristics_both_l | Combined heuristic predictions |

The four annotation tables distinguish independent reviewer decisions, initial
agreement and jointly adjudicated reference labels. The six prediction tables separate
LLM and heuristic results for documentation, code and combined evidence. Numeric
0/1 labels are binary; `?`, blank and `Unverified` values denote unknown predictions.

## Where are the worksheet CSVs?

There are **10 distinct current worksheet exports**, each 101 rows by seven columns:

1. [reviewer1.csv](reviewer1.csv)
2. [reviewer2.csv](reviewer2.csv)
3. [agreement.csv](agreement.csv)
4. [final_agreement.csv](final_agreement.csv)
5. [llm_documentation.csv](llm_documentation.csv)
6. [llm_code.csv](llm_code.csv)
7. [llm_combined.csv](llm_combined.csv)
8. [heuristics_documentation.csv](heuristics_documentation.csv)
9. [heuristics_code.csv](heuristics_code.csv)
10. [heuristics_combined.csv](heuristics_combined.csv)

The consolidated [../predictions.csv](../predictions.csv) additionally includes
heuristic commit IDs, mode identifiers and scan-completeness flags.

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

## Reproduce the paper results

Run [the notebook](../reproduce_paper.ipynb) or its standard-library Python equivalent:

```bash
uv run --frozen python results/benchmark-100/reproduce_paper.py
```

Evaluation uses independent scan-completeness flags: **96 documentation, 95 code,
95 combined repositories**. Known positives are retained in incomplete scans;
complete-scan metrics exclude those scans. LLM evaluation uses **98/63/99** repositories
with determinate six-stage predictions. The combined LLM micro-F1 is 0.79454927,
reported as **0.795** to three decimal places.
