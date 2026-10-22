# Annotation questions and evidence scope

The paper's Table 1 describes the initial independent documentation-based review.
The questions below are the initial annotation questions reported in the paper. The final jointly
adjudicated labels are treated as mixed-source, consistent with the final reference
and evaluation interpretation; they must not be presented as independently established
source-code ground truth.

| Stage | Initial annotation question | Evidence examples |
|---|---|---|
| Collection | Does the documentation describe the acquisition or generation of research data or observations? | Data sources, collection procedures, dataset generation, acquisition instructions |
| Processing | Does the documentation describe how research data are prepared or transformed for analysis? | Cleaning, preprocessing, feature extraction, data transformations |
| Method | Does the documentation describe a scientific model, algorithm, or analytical technique implemented in the repository? | Architectures, scientific algorithms, analytical methods, methodological parameters |
| Experimentation | Does the documentation describe the execution of research experiments, trials, or parameter studies? | Procedures, trial conditions, parameter sweeps, execution commands |
| Evaluation | Does the documentation describe how research outcomes are assessed or validated? | Metrics, reference outcomes, baselines, comparative studies, ablations |
| Dissemination | Does the documentation describe the presentation, publication, or sharing of research outputs? | Results, figures, tables, publication links, exports, deposits |

Independent reviewer labels, initial agreement indicators and jointly adjudicated
labels are separate CSVs under `results/benchmark-100/workbook/`. No random sampling or
held-out test split is inferred. All 100 repositories informed heuristic development.
Human annotation questions, original LLM prompts and deterministic rules share stage
names but are not asserted to have identical operational thresholds. The exact final
rules are documented in [rules.md](rules.md); the initial questions do not replace them.
