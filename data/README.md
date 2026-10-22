# Research inputs and provenance

| File/group | Contents |
|---|---|
| `final_agreement.csv` | Jointly adjudicated 100-repository reference, 600 labels, supplied order |
| `annotations_independent.csv` | Original independent reviewer labels |
| `research_lifecycle_benchmark_100_msr27.xlsx` | Anonymous all-sheet source workbook, including archived LLM outputs |
| `annotation_audit_20261020.json` | Workbook-bound annotation audit |
| `final_agreement_correction.json` | Historical cross-format reference verification |
| `anonymity_audit.json` | Historical scoped audit; not a guarantee for later uploads |
| `corpus/benchmark_100.txt` | Annotated development cohort |
| `corpus/benchmark_386.txt`, `corpus/legacy_386.txt` | Historical repository identities, possibly different order |
| `corpus/legacy_386_source.json`, `corpus/legacy_paper_links.csv` | Supplied historical publication-association provenance |
| `runs/`, `reports/` | Original local research runs and assessments, to be uploaded |

The workbook separates reviewer1/reviewer2 independent decisions from final_agreement.
Archived chatgpt/heuristics mode sheets retain their original experimental conditions;
they are not new measurements from the final method. The final reference is treated as
mixed-source unless a source-specific audit establishes otherwise. Initial reviewer
agreement must be calculated from independent labels, not adjudicated consensus.

The original source associations do not establish an independently reproduced publication
filter. All 386 historical identities were reported as contained in the 3,211 experiment-
mentioned collection; reproduce and document membership using the extraction/subtraction
workflow in ../docs/data-generation.md. Different releases may produce different counts.

Do not overwrite source labels, source workbook cells or historical manifests. Redundant
normalized reference copies and unused exploratory text-association cohorts were removed
from the distribution; historical verification records may refer to those older copies.
The CSV and workbook remain checked against one another by tests.

Final exports and their metadata belong under ../results/ or original data/runs paths:
see ../docs/results.md. Annotation reuse terms are in LICENSE-annotations.md. Public
third-party repository identities remain research data; author identities and personal
source-workbook links must not be reintroduced into the anonymous distribution.
