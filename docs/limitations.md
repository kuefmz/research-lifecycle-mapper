# Limitations and paper freeze decisions

The initial implementation is executable research infrastructure, not a validated scientific classifier. The 12 rules are intentionally narrow, English/Python candidates and will miss many legitimate research repositories. Research-specific function names plus operations are static syntactic evidence; they cannot establish execution, causality, intent or scientific validity. Dead code can qualify. Documentation may overclaim and simple exclusion patterns do not understand every negation or hypothetical statement.

Other implementation languages are inventoried but currently have no code rules. Notebooks, configuration files, publication PDFs, data artifacts, generated outputs, symlinks, submodules and vendored content do not qualify. These choices are explicit in policy `eligibility-1`. Unit-test paths are conservatively vetoed even if a project keeps real scientific evaluations there. Sentence/workflow-scoped documentation matching and eight-line Python windows impose recall limits. The Method interpretation awaits the human codebook.

The XLSX importers require explicit literal-value schemas; it is not an automatic interpreter of arbitrary workbook layouts or formulas. Historical benchmark revisions cannot be inferred from current default branches. Importing approved consensus requires references to actual approval; the software does not certify a human decision's authenticity. Split leakage guards rely on truthful, complete development-use declarations.

The upstream source lacks a licensing grant in its audited tree, so its code was not copied. Reusing literal code remains blocked until permission/license is established. API/demo functionality and the large OpenAIRE corpus are not bundled. Original sampling provenance remains unknown; the audited corpus is a documented candidate frame, not verified human-sample provenance.

Live GitHub acquisition is tested using a mocked API; no full external repository scan has been executed from this restricted environment. API rate limits/errors are surfaced, but automatic backoff/resume and LFS/submodule expansion are not implemented. Snapshots may be incomplete. The container is a version-tagged convenience recipe, not a verified digest-pinned release; Docker/remote CI execution must be checked separately.

Before a paper freeze:

1. Supply and checksum the original workbook, repository list and source sampling documentation; verify 600 independent pairs and 247 disagreements.
2. Supply historical commits or document that they cannot be recovered; capture, integrity-check and review release rights for snapshots.
3. Adjudicate disagreements, approve all final labels, and freeze the six-stage codebook with explicit Method semantics.
4. Adjudicate the rule-to-concept mappings and evidence eligibility policy; version all approved changes.
5. Record any tuning examples, choose exploratory versus independent held-out reporting, and approve the evaluation protocol.
6. Freeze a clean classifier commit, runtime/dependency lock and verified environment image/action digests; run full reproduction from distributed inputs.
7. Audit the anonymous artifact and its metadata manually, preserve all applicable licensing notices, and review venue policy before release.

## v0.2.0 protocol update

Documentation-only is primary, with development macro-F1 for model selection. Documentation uses explicit, contextual and demonstrated-workflow families with activity/object/scope/polarity records; wrapped prose and inherited Markdown/AsciiDoc/reStructuredText headings are supported. Production matching is deterministic and uses no gold labels or external models. Agreement Final is the required candidate consensus worksheet; independent labels remain separate provenance. See `agreement_final.md`, `evaluation_protocol.md` and `rule_change_protocol.md` for the current importer, split, freeze, mismatch and final-run procedures. Historical one-line rules and unsplit held-out declarations are superseded. Human inputs are still missing; no human tuning or held-out run was performed.
