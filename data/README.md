# Research data inventory

| File/group | Role |
|---|---|
| final_agreement.csv | Authoritative supplied 100-repository, 600-label joint consensus; original order |
| annotations_independent.csv | Original independent reviewer labels; never substitute consensus for reliability |
| research_lifecycle_benchmark_100_msr27.xlsx | Anonymous derivative workbook with all source sheets |
| research_lifecycle_benchmark_100_msr27.json | Normalized workbook/reference representation |
| final_documentation_labels.csv | Earlier named consensus derivative; filename does not establish source-pure labels |
| annotation_audit_20261020.json | Historical workbook-bound audit, not a new evaluation |
| final_agreement_correction.json | Verification that supplied CSV agrees with existing reference labels |
| anonymity_audit.json | Historical scoped scan; not a guarantee for the current release |
| LICENSE-annotations.md | Annotation reuse terms |
| corpus/benchmark_100.txt | Annotated development cohort in supplied order |
| corpus/benchmark_386.txt, legacy_386.txt | Historical identities, possibly different order |
| corpus/legacy_386_source.json, legacy_paper_links.csv | Original supplied association provenance |
| corpus/metadata_association_repositories.txt, overlap_legacy_metadata/ | Older exploratory text-association candidates/overlap; not the 3,211 selection |
| runs/ | Original researcher-local corpus checkpoints and exported files, to be uploaded |
| reports/ | Original researcher-local final assessments, to be uploaded |

Workbook sheets reviewer1/reviewer2 are independent annotations; final_agreement is joint
consensus. chatgpt_documentation/code/combined and heuristics_documentation/code/combined
are archived model/heuristic outputs under their original conditions, not new final-method
measurements. The final reference is currently interpreted as mixed-source. The original
human instruction version and annotation-time commits require separate provenance.

Source workbook URLs and personal identities were removed in the anonymous derivative;
third-party repository IDs remain research data. Do not overwrite workbook contents or
silently change cached formulas. Never publish an unredacted source workbook.

The old metadata candidate comparison (36 shared, 350 historical-only, 286 candidate-only)
is about 322 exploratory candidates, **not** the current 3,211. The researcher separately
verified all 386 historical identities within the 3,211 description-filtered collection.
The historical query/publication criterion has not been exactly reproduced.

See ../docs/data-generation.md for software.tar provenance and regeneration;
../docs/results.md for final exports and ../results/README.md for upload requirements.
No local results or exact LLM prompts are represented as uploaded before they are supplied.
