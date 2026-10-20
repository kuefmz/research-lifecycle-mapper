# Inspect publication-association evidence using software.tar only

This offline route needs no relation archives, network access or token. It reuses
the experiment/GitHub candidate extraction and scans the exact same software TAR.
It saves metadata evidence for review rather than asserting that references are
verified publication relations. No target count (including 386) is imposed.

After active analyses finish, update main, then:

```bash
git pull --ff-only
uv sync --frozen
uv run --frozen python -m lifecycle_mapper.publications \
  --candidates data/corpus/openaire-experiments \
  --software-tar data/raw/software.tar \
  --source-record https://zenodo.org/records/20428976 \
  --output data/corpus/openaire-experiments-metadata
cat data/corpus/openaire-experiments-metadata/funnel.md
```

Use a new output directory. The TAR hash and release must match the candidate
manifest; candidate file hashes are also verified. Do not combine --software-tar
with relation/archive/name flags. The historical relation-based route remains
available but is not required for this metadata audit.

The detector reads description(s), source(s) and documentationUrls, retaining
external DOI references near paper/study/article/publication/preprint mentions,
arXiv references, and explicitly quoted paper/study/article/publication titles.
A DOI present among the software's own top-level/instance PIDs or DOI original IDs
is excluded. Citation counts, publication dates, publisher fields, generic paper
mentions and "paper-ready" text do not qualify on their own. Obvious nearby
negative/future wording is excluded. This English lexical detector can miss real
associations and can match unrelated references; every match remains unreviewed.
DOI targets are not resolved or confirmed to be papers. Arbitrary metadata fields
and full repository contents are not searched. Experimental-context selection
remains the existing whole-word description rule; no historical field expansion
is guessed.

Outputs:

- funnel.md / funnel.csv: source record, context, GitHub and metadata-evidence
  counts, explicitly distinguishing records, links and deduplicated repositories.
- summary.json: upstream counts, selected/unresolved counts, field inventory,
  selection rule, source/input/output hashes and limitations.
- publication_evidence.csv: software ID, archive location, field, evidence type,
  reference and excerpt, with unreviewed status.
- metadata_audit.csv: every candidate software-record occurrence, including
  unresolved cases. Unresolved is not evidence that a publication does not exist.
- repositories.csv / repositories.txt: repositories with metadata association
  candidates; this is not an eligibility-certified four-criterion cohort.
- software_links.csv: only supporting candidate software records, joined before
  repository deduplication. A repository can have multiple linked software records.

To reconcile these candidates with the original cohort, run lifecycle_mapper.funnel
with --publication-extraction data/corpus/openaire-experiments-metadata and the
original --full-extraction, --filtered-extraction, --legacy-repositories and
--output arguments. The report labels these as metadata_association_candidates;
it leaves verified publication linkage unknown. Add --run PATH for actual
checkpoint coverage. No second study is implied: this is an eligibility evidence
audit for the same intended four-criterion selection.

To claim the fourth criterion or an exact historical reproduction, review the
references and recover the original collection query/field/relation policy. The
three inspected example records support only a metadata association for the first
example; software-deposit DOIs and citation counts are not substitutes for paper
links. Do not choose or tune a filter merely to reproduce a count of 386.
