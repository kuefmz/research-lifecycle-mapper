# Candidate codebook — not human-adjudicated

The final adjudicated codebook has not been supplied. These operational candidates support software testing and exploratory work only. Stage order is fixed.

| Stage | Candidate conceptual definition | Insufficient evidence |
| --- | --- | --- |
| Collection | Acquisition or generation of raw research observations | HTTP call, API client or downloading a dependency alone |
| Processing | Preparation of research data for analysis | Generic parsing or application configuration handling |
| Method | Implementation of a scientific model, algorithm or analytical technique | src directory, packaging, entry point, software tests |
| Experimentation | Controlled execution of research trials, conditions or parameter studies | run.py, application launch or generic configuration |
| Evaluation | Scientific assessment against reference outcomes, baselines or ablations | Software unit tests, isolated metric names or performance instrumentation |
| Dissemination | Preparation, presentation, export or external communication/deposition of research outputs for reuse (candidate expansion; approval pending) | README presence, generic documentation or software release alone |

Unresolved decisions include whether metadata-only scholarly citation qualifies Dissemination; how to treat research benchmarks located under tests; whether analytical scripts count as Method without an explicit model; and whether config files, notebooks, generated scientific data and publication PDFs should become eligible evidence. No provisional resolution is represented as annotator-approved.

The catalog's `justification` field is the machine-readable mapping from rule IDs to conceptual claims. Human approval must version this document, approve that mapping, and reconcile any departures from the supplied codebook before a paper release.
