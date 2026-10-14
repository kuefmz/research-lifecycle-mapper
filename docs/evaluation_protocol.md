# Documentation-primary development and frozen evaluation

The primary classifier is documentation-only. The primary model-selection metric is its six-stage macro-F1 **on development data only**. Per-stage precision/recall/F1 and secondary code-only/OR-combined results remain mandatory; unfavorable results are not suppressed. Combined deltas are accompanied by an explicit same-evaluated-cohort flag because partial scans can change denominators.

No actual workbook or human labels have been inspected during this implementation. Rule revisions were based on the supplied operational definitions and independently authored synthetic examples. There has been no human development evaluation or final held-out evaluation. Thus no human agreement improvement is claimed.

## Custodian creates the split before tuning

After approving the full research manifest, a benchmark custodian executes:

```bash
uv run --frozen python -m lifecycle_mapper benchmark split --manifest benchmark/manifest.json --output local/splits/v1 --test-fraction 0.2 --seed rlm-split-v1
```

The deterministic algorithm preserves whole repositories and greedily minimizes squared deviations from the requested test-set marginal label counts, normalized by population stage support. Hashes of the seed and repository identifiers break ties. It uses no predictions. It approximately stratifies six marginal labels; exact rare-label/pairwise balance is not guaranteed. The split records the population manifest checksum, algorithm, seed and all assignments. A split output cannot be overwritten. It exports **development labels only**, never test labels.

The custodian must retain the original complete benchmark separately with restricted access. The software is an operational guard, not an operating-system access-control system. A developer who can read the original workbook can still inspect test labels; the team must prevent this organizationally. The evaluator reads complete provenance for validation but emits/analyzes only the selected partition. Give rule developers the development export and development snapshots, never the original complete labels or test error reports.

Configure development runs with `evaluation_role: exploratory`, `partition: development`, `split_manifest` relative to the project root, and its exact `split_manifest_sha256`. Run `benchmark run` with that config. Test selection under an exploratory role is rejected. Do not tune using full-benchmark exploratory results if the same population is intended as final held-out evaluation.

## Freeze after development

Prepare an ignored `configs/local-heldout.yaml` identifying the test partition, frozen split checksum, all development repository IDs, rules path, benchmark path, new ignored output directory, and `evaluation_role: held-out`. The complete benchmark must include a held-out approval reference, `test_used_for_rule_development: false`, and `test_labels_inspected_during_tuning: false`. These are researcher attestations, not inferred facts.

Initially include `frozen_manifest: local/frozen/protocol.json` with no checksum. With a clean committed classifier:

```bash
uv run --frozen python -m lifecycle_mapper benchmark freeze --config configs/local-heldout.yaml --output local/frozen/protocol.json --approval-reference ACTUAL_PROTOCOL_APPROVAL
```

The freeze records classifier Git commit/source hash, catalog hash, complete input hash, exact config hash (excluding output/freeze-reference fields), lockfile hash and the primary selection metric. Add the frozen JSON's SHA-256 as `frozen_manifest_sha256` in the ignored config. Keep the source checkout unchanged. Inputs/config/protocol under ignored local paths permit this preparation without changing the frozen Git commit; archive all exact files with the approved release.

```bash
uv run --frozen python -m lifecycle_mapper benchmark run --config configs/local-heldout.yaml
uv run --frozen python -m lifecycle_mapper benchmark verify --config configs/local-heldout.yaml --workspace local/final-reproduction
```

The first successful final run writes a canonical-hash evaluation ledger next to the frozen protocol. A second ordinary final run is rejected. Verification permits reruns only after that initial ledger exists and requires every canonical output to match it exactly. Changed rules, config, commit, inputs or dependencies fail the frozen guard. Preserve this ledger in the research release. This does not prevent deliberate deletion or concealment of evaluations; researcher integrity and custodian controls remain necessary.

If the full benchmark was inspected during tuning, disclose it and obtain a new independent sample for confirmatory claims. Cross-validation and automated rule selection are not implemented; do not label repeated test inspection as cross-validation.
