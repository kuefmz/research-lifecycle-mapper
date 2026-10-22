# 3,211-repository corpus results

The complete population contains 3,211 unique GitHub repository identities, including
the 386 publication-associated repositories and the 100 annotated benchmark repositories.
`repositories.txt` records the population; its ordering and reconstruction provenance are
in `repository_list_provenance.json`.

## Stage-level results

Each cell is **positive / negative / unknown**, out of all 3,211 repositories. These
are detected-evidence counts, not validated prevalence of research activities.

| Stage | Documentation | Code | Combined |
|---|---:|---:|---:|
| Collection | 381 / 2317 / 513 | 33 / 2596 / 582 | 408 / 2219 / 584 |
| Processing | 1132 / 1599 / 480 | 236 / 2418 / 557 | 1219 / 1479 / 513 |
| Method | 693 / 2015 / 503 | 983 / 1714 / 514 | 1324 / 1373 / 514 |
| Experimentation | 1981 / 784 / 446 | 139 / 2499 / 573 | 2007 / 738 / 466 |
| Evaluation | 782 / 1935 / 494 | 782 / 1900 / 529 | 1237 / 1453 / 521 |
| Dissemination | 1828 / 923 / 460 | 881 / 1829 / 501 | 2024 / 719 / 468 |

Dissemination (2,024; 63.03%) and Experimentation (2,007; 62.50%) have the largest
combined positive counts; Collection has the smallest (408; 12.71%). Percentages use
all 3,211 repositories, including unknowns. Unknowns are reported separately and never
treated as negative labels.

Compared with documentation-only counts, combined evidence adds 631 Method positives
and 455 Evaluation positives. These are differences in detected stage counts; they do
not establish improved classification accuracy without full-corpus human labels.

## Reproduce

```bash
uv run --frozen python results/corpus-3211/reproduce_results.py
```

The benchmark [notebook](../benchmark-100/reproduce_paper.ipynb) also runs this calculation.

| File | Contents |
|---|---|
| `stage_counts.csv` | All 18 mode/stage counts and percentages, denominator 3,211 |
| `aggregate_summary.json` | Machine-readable full-corpus results and evidence scope |
| `paper_table.tex` | LaTeX table of positive/negative/unknown counts |
| `reproduce_results.py` | Standard-library reproduction from preserved source inputs |
| `source/execution.log.gz` | Losslessly compressed original execution log, including checkpoint repetitions |
| `source/provenance.json` | Input hashes and source scope |

## Source and verification scope

The calculation combines the supplied complete 386-corpus aggregate table with the
final console decision for every identity in the disjoint execution remainder. The
script verifies source hashes, deduplicates repeated checkpoint log entries by final
occurrence, verifies exact population membership and disjointness, and requires all
three modes and six stages for every logged identity. Every output triplet sums to 3,211.

The 386 aggregate input is [../corpus-386/stage_counts.csv](../corpus-386/stage_counts.csv).
Its original row-level export is still unavailable, so those base counts are supplied
results rather than independently reconstructed predictions. Log-derived decisions do
not provide the complete pinned commits, captured inputs and supporting evidence of
the original result JSON files. Complete pooled per-repository evidence exports remain
pending; aggregate reproducibility does not establish exact classifier replay.

Full-population repository/mode completeness cannot be recovered from per-stage base
aggregates because unknown stages may overlap in the same repositories. Consequently,
no full-corpus completed-scan total, precision, recall or F1 is inferred here.

The collection is experiment-mentioned software, not a representative sample of all
research software. Publication-associated selection applies to the nested 386 corpus,
not automatically to every repository in the full population. Repository-level
Dissemination findings are not automatically assigned from graph publication links.
