# Research Lifecycle Mapper

Deterministic, explainable repository-level multi-label classification of six research lifecycle stages, in this order: **Collection, Processing, Method, Experimentation, Evaluation, Dissemination**.

This is a research implementation, not a web demo. The initial rules are **unadjudicated candidates**. The 100-repository human benchmark is **pending**; no human benchmark performance has been measured. Five explicitly synthetic repositories exercise the offline pipeline and its failure handling.

## Install and verify

Use Python **3.12.14** and uv **0.12.23**. The lockfile pins development dependencies; the classifier has no third-party runtime dependencies. Run from the repository root:

```bash
uv sync --frozen
mkdir -p local
uv run --frozen ruff check src tests scripts
uv run --frozen ruff format --check src tests scripts
uv run --frozen mypy
uv run --frozen pytest -q --basetemp local/pytest
```

If installing uv, use the official installer with an explicitly selected version. Initial dependency installation can require network access; classification replay and tests do not. A wheel can be installed with `python -m pip install --no-deps dist/research_lifecycle_mapper-0.2.0-py3-none-any.whl` after `uv build --wheel`.

## Analyze

Replay is the analysis default. Live acquisition is an explicit, separate command:

```bash
uv run --frozen python -m lifecycle_mapper acquire https://github.com/OWNER/REPO --ref COMMIT_OR_REF --snapshot local/snapshots/example
uv run --frozen python -m lifecycle_mapper analyze --snapshot local/snapshots/example --mode combined --output local/analysis.json
uv run --frozen python -m lifecycle_mapper analyze --snapshot local/snapshots/example --mode documentation-only
uv run --frozen python -m lifecycle_mapper analyze --snapshot local/snapshots/example --mode code-only
```

The acquisition resolves the ref once to an immutable commit and retrieves immutable Git blobs. It never executes repository code. `GITHUB_TOKEN` is optional, read from the environment, and excluded from all outputs. GitHub rate limits may require a token for large acquisitions.

Try the included offline snapshot:

```bash
uv run --frozen python -m lifecycle_mapper analyze --snapshot benchmark/synthetic/snapshots/docs-positive
```

Results retain exact matched conditions, rule IDs, source categories, content hashes, original line ranges, and commit-pinned evidence links. Synthetic evidence links illustrate the URL format and deliberately do not identify real GitHub repositories.

## Reproduce the synthetic benchmark

```bash
uv run --frozen python -m lifecycle_mapper benchmark run --config configs/synthetic.yaml --output local/runs/synthetic-check
uv run --frozen python -m lifecycle_mapper benchmark verify --config configs/synthetic.yaml --workspace local/reproduction --reference benchmark/results/synthetic-v2
```

Use new output directories for each command. Verification runs the same inputs twice and compares every canonical artifact, including both current execution manifests. It also compares semantic result artifacts with the committed synthetic reference; the reference's execution manifest retains its original producing checkout metadata.

## Human benchmark — Agreement Final is the candidate gold source

```bash
uv run --frozen python -m lifecycle_mapper benchmark import original.xlsx --config configs/agreement-final-import.yaml --output local/imports/final-v1
uv run --frozen python -m lifecycle_mapper benchmark run --config configs/benchmark.yaml
```

The import mapping is an unverified template; adapt it explicitly to the supplied workbook. Consensus stays candidate without an exact-workbook approval record. The second command currently exits with an explicit pending-input error. It requires approved consensus, provenance, sampling documentation, an approved codebook, and pinned snapshots. The importer preserves the source file and its checksum; proposed consensus is never used as gold.

See [benchmark import specification](benchmark/provenance/import_specification.md), [methodology](docs/methodology.md), [reproducibility](docs/reproducibility.md), [implementation audit](docs/implementation_provenance.md), and [limitations](docs/limitations.md).

## Portable snapshots

```bash
uv run --frozen python -m lifecycle_mapper snapshot pack --snapshot benchmark/synthetic/snapshots/docs-positive --output local/docs-positive.tar
uv run --frozen python -m lifecycle_mapper snapshot unpack --bundle local/docs-positive.tar --output local/replayed
```

Live snapshots default to `redistribution: not-reviewed`. After checking all relevant licenses and release policies, the snapshot custodian may explicitly set `approved-for-redistribution`, regenerate its canonical manifest, and record the new manifest hash. Unapproved live snapshots cannot be bundled. Manifests, pinned commits, and hashes can be shared independently where permitted, but later network reacquisition is not guaranteed to reproduce unavailable content.

## Research status

Implemented: versioned source-specific rules; deterministic classification; acquisition/replay; read-only CSV/XLSX import; gold/provenance gates; all three evaluation modes; confusion matrices and inspection tables; stable canonical reporting; snapshot bundles; CI and offline fixtures.

Pending scientific work: final Method interpretation and adjudicated codebook; actual 100 repositories and historical revisions; independent annotations and disagreement records; human consensus approval; verified sampling provenance; redistribution review; independent held-out protocol; multilingual/multi-language coverage; digest-pinned release environment. See the freeze checklist in [limitations](docs/limitations.md).

The upstream implementation was audited at commit `dfb22f9545860a99a57199975dd78a4d9cb80fea`. Its architecture and evidence concepts informed this independent implementation. No upstream code was copied because its inspected tree declares no license. The original repository and benchmark sheet were not modified.

## Documentation-primary protocol (v0.2.0)

Documentation-only is the default and primary classifier; documentation macro-F1 on development data is the selection metric. The catalog now contains 18 explicit/contextual/workflow documentation rules and six unchanged secondary Python rules. Every documentation candidate records activity, object, context, polarity, scope, heading and layer. Negation, future work, third-party scope and generic infrastructure are excluded. Combined remains logical OR.

See [Agreement Final ingestion](docs/agreement_final.md), [split/freeze protocol](docs/evaluation_protocol.md) and [rule-change workflow](docs/rule_change_protocol.md). Development runs select only development repositories. Final research runs require an approved split, frozen implementation/configuration and an execution ledger; later runs are reproduction-only. No human agreement improvement or final test performance is claimed.
