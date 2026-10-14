# Benchmark protocol

The executable research benchmark lives in `benchmark/manifest.json` and is currently explicitly pending. The human workbook, repository list, pinned revisions, approved codebook, final labels and original sampling procedure are absent. Synthetic data is located under `benchmark/synthetic/` and its outputs under `benchmark/results/synthetic-v1/`.

Required research manifest fields are described in `benchmark/provenance/import_specification.md`. Config paths are relative to the project root; configs must live directly in `<project>/configs/`. Snapshot/provenance paths are relative to the manifest directory. Traversal outside these roots is rejected; place input files under the benchmark directory instead of using `..` paths. Outputs are new directories and never overwrite existing runs.

Research runs require a clean committed checkout and a lockfile. Put local acquired/imported private material and runs under ignored directories while preparing the release, then review approved input manifests/snapshots before committing them. A separately prepared complete research benchmark directory can be supplied via a new config in the project's configs directory. Do not publish annotation notes or private workbook copies automatically.

All 100 research repositories need explicit immutable commits and six literal binary approved labels. The label table checksum must match the annotation provenance, the provenance hash must match the benchmark manifest, and manifest labels must match approval-referenced table rows. Both independent labels and the 247 original disagreements remain preserved independently of gold. The human codebook and sampling documentation each require content checksums, and the codebook requires an approval reference.

Exploratory evaluation is the default research config role. A held-out role is only allowed with a documented split approval and no declared development overlap. A held-out declaration cannot erase prior use of the benchmark to tune rules. Final paper results require an approved protocol and frozen classifier; software validation alone is not scientific approval.
