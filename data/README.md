# Research inputs and provenance

| Input | Purpose |
|---|---|
| `final_agreement.csv` | Authoritative adjudicated 100-repository reference in supplied order |
| `annotations_independent.csv` | Independent Reviewer 1 and Reviewer 2 labels |
| `corpus/benchmark_100.txt` | 100-repository development input |
| `corpus/benchmark_386.txt` | Full 386-repository corpus input |
| `corpus/benchmark_3211.txt` | Complete 3,211-repository corpus input; identical to the released population list |
| `corpus/publication_associations.json` | Original supplied OpenAIRE software/publication association metadata for the 386 repositories |

Released worksheet CSVs, assessment records and the executed notebook are under
[results/benchmark-100](../results/benchmark-100/README.md). The association JSON
preserves source metadata for the publication-associated collection. Third-party
titles and identifiers retain their original terms.

Final consensus is a mixed-source adjudicated reference. Initial independent review
and the original guideline questions concerned documentation. Do not calculate initial
agreement from final consensus or infer a random sample or reproduced publication query.

Source: [OpenAIRE Graph Dataset, record 20428976](https://zenodo.org/records/20428976).
Use `software.tar` as described in [data generation](../docs/data-generation.md).
The archive is not committed. Full population lists/results are in [../results/](../results/README.md).
Annotation terms are in [LICENSE-annotations.md](LICENSE-annotations.md).

## Google Sheet CSV exports

The ten worksheet CSVs are in **[results/benchmark-100/workbook/](../results/benchmark-100/workbook/README.md)**:
`reviewer1.csv`, `reviewer2.csv`, `agreement.csv`, `final_agreement.csv`,
`llm_documentation.csv`, `llm_code.csv`, `llm_combined.csv`,
`heuristics_documentation.csv`, `heuristics_code.csv` and `heuristics_combined.csv`.
Each has one header plus 100 repository rows and seven columns.

The three execution input lists are together under `data/corpus/`: `benchmark_100.txt`,
`benchmark_386.txt` and `benchmark_3211.txt`. The full 3,211 list uses the same identities
and order as `results/corpus-3211/repositories.txt`; its source reconstruction provenance
remains in that result folder.
