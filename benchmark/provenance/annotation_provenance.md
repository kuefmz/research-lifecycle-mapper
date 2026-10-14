# Human annotation provenance — pending verification

According to the supplied research brief, Jenifer and Esteban independently classified the same 100 repositories against six lifecycle stages. This yields 600 repository-stage annotation pairs. The reported independent disagreement count is 247. The original workbook and annotation codebook have not been supplied; these numbers are therefore recorded as user-provided claims, not verified computation.

Benchmark construction consists of independent human labeling followed by disagreement adjudication. Original independent labels must remain immutable normalized columns. Proposed consensus remains provisional. Human adjudicators must resolve conflicts using a versioned codebook and approve every final label with a reference to the decision or approved release. Do not automatically use agreement rows, majority votes, classifier predictions or proposed consensus as gold.

The actual sampling frame/selection strategy and historical revisions remain pending. The inspected upstream documents a corpus compiled from OpenAIRE/Zenodo record 12819872; no evidence yet establishes that the human sample was selected by its default random command. Annotator expertise, assignment procedure, blinding, selection seed, inclusion/exclusion criteria, adjudicator identity/roles and release restrictions must be supplied by the research team.

The importer produces `annotations.csv`, `disagreements.csv` and `provenance.json`. The source checksum, original filename, version, pair counts, disagreements and gold status are preserved. Importing is not approval. The original Google Sheet/source workbook is never written by this implementation.
