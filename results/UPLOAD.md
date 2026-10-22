# Transfer original local results

The submission publishes three complete populations, not the execution subsets:

| Population | Destination | Components |
|---|---|---|
| Annotated 100 | `results/benchmark-100/` | Original 100 run |
| 386-repository corpus | `results/corpus-386/` | 100 + 286 |
| OpenAIRE 3,211 | `results/openaire-3211/` | 100 + 286 + 2,825 |

The 100 and 386 repository lists are already included. The full 3,211 list must come
from `data/corpus/openaire-experiments/repositories.txt`, not a remaining-subset list.
The corrected benchmark workbook CSVs and original assessment already in the repository
remain separate from the pending raw-run upload.

## Prepare the private transfer ZIP

From the local repository, pull the preparation script and identify the last run:

```bash
git pull --ff-only
uv run --frozen python - <<'PY'
import json
from pathlib import Path
for path in sorted(Path('data/runs').glob('*/summary.json')):
    value = json.loads(path.read_text())
    if value.get('repository_count') == 2825:
        print(path.parent, '| finished=', value.get('finished'),
              '| complete=', value.get('complete'),
              '| partial=', value.get('partial'), '| failed=', value.get('failed'))
PY
```

Use the path of the completed 2,825-repository run printed above as the third `--run`:

```bash
uv run --frozen python scripts/prepare_results_upload.py \
  --run data/runs/YOUR_EXISTING_100_RUN \
  --run data/runs/YOUR_EXISTING_286_RUN \
  --run /path/to/the/completed-2825-run \
  --openaire-list data/corpus/openaire-experiments/repositories.txt \
  --output local/results-upload.zip
```

Replace the first two placeholders with the existing local 100 and 286 run directories. Do not rename or modify original run manifests.
The ZIP uses neutral batch folder names. Upload `local/results-upload.zip` in the
conversation; it is a private transfer input, not a GitHub deliverable. If the last run
is still running, send the first two runs now (omit the third `--run`) and send the
2,825 run later in a separate ZIP with a different output filename.

The script includes only:

- Original run manifest, summary/progress and stopped-repository diagnostics, when present.
- Existing prediction, status, reference-comparison and additional-evidence CSV exports.
- Every original `repositories/*/result.json` and its verified `result.sha256`.
- Full 100, 386 and 3,211 input lists, plus a checksum inventory.

It excludes source snapshots, downloaded repositories, Git folders, environment files,
tokens stored in separate files, software archives and terminal logs. No export or
reanalysis is needed first: original result JSON files are authoritative and exports
can be regenerated from them. Manifests/results can contain local paths or historical
metadata; they will be reviewed before anonymous publication. Do not add credentials
to JSON metadata or send any token.

## Verification and publication after transfer

1. Verify transfer hashes, original result hashes and population identities. Require
   exactly 100, 386 and 3,211 unique input repositories and the declared inclusion
   relations. Preserve each full list's order.
2. Verify 100 and 286 are disjoint, with their union equal to the 386-repository list;
   verify the 2,825 batch is disjoint and the union equals the full OpenAIRE list.
3. Compare rule/implementation hashes, branch policy, modes and limits. Preserve
   original provenance. A renamed profile is not automatically a changed
   experiment; compare actual rules. Report material incompatibility before pooling.
4. Retain all attempts, failures, partial scans, known positives and unknowns. A missing
   checkpoint is an explicit unprocessed row, never an all-zero prediction. Preserve
   per-mode scan completeness independently of the six predictions.
5. Generate each collection's complete repository list, long-form `predictions.csv`
   (18 rows per repository), `repository_status.csv`, `evidence.csv`, `summary.json`,
   and anonymous `provenance.json`. Evidence includes rule/file/line references and
   pinned commits where available. No duplicate subset population is published.
6. Review local paths, identifying metadata, evidence excerpts and redistribution
   scope. Preserve original checksums in provenance while documenting any publication
   transformation; never represent rewritten JSON as the unchanged original.
7. Recheck benchmark predictions against the original assessment and reproduce Table 4.
   Extend the notebook with verified 386/3,211 positive/negative/unknown stage counts,
   coverage, failures and explicitly scoped timing statistics. Full-corpus F1 requires
   ground truth and must not be inferred from the 100 labels.

The small private ZIP enables verification and evidence inspection. Full source
snapshots are unnecessary for aggregate reproduction; exact offline classifier replay
requires separately archived acquired inputs. Retain those locally for later archival.
