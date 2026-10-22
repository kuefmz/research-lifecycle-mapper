# Research inputs and provenance

| Input | Purpose |
|---|---|
| `final_agreement.csv` | Authoritative adjudicated 100-repository reference in supplied order |
| `annotations_independent.csv` | Independent Reviewer 1 and Reviewer 2 labels |
| `corpus/benchmark_100.txt` | 100-repository development input |
| `corpus/benchmark_386.txt` | Full 386-repository corpus input |
| `corpus/publication_associations.json` | Original supplied OpenAIRE software/publication association metadata for the 386 repositories |

Current worksheet CSVs, restored unknowns, original assessment and the executed notebook
are under [results/benchmark-100](../results/benchmark-100/README.md). The superseded
workbook, duplicate 386 list, derived paper-link CSV and outdated audits were removed
to avoid conflicting sources. The association JSON is retained as source provenance,
not an alternative prediction dataset. Third-party titles and identifiers retain their
original terms.

Final consensus is a mixed-source adjudicated reference. Initial independent review
and the original guideline questions concerned documentation. Do not calculate initial
agreement from final consensus or infer a random sample or reproduced publication query.

Source: [OpenAIRE Graph Dataset, record 20428976](https://zenodo.org/records/20428976).
Use `software.tar` as described in [data generation](../docs/data-generation.md).
The archive is not committed. Full population lists/results are in [../results/](../results/README.md).
Annotation terms are in [LICENSE-annotations.md](LICENSE-annotations.md).
