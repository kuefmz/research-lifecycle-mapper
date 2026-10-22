# Research results

This page documents the results used in the MSR 2027 paper. Benchmark values below are recalculated from saved predictions and the adjudicated reference. Paper comparisons include the author-confirmed Table 6 rounding and Table 7 corrections. The original draft hash and correction provenance are recorded in [paper_claims.json](benchmark-100/paper_claims.json); the corrected PDF has not been supplied.

## Collections and availability

| Collection | Repository list | Results available |
|---|---|---|
| Annotated 100 | [benchmark-100/repositories.txt](benchmark-100/repositories.txt) | Human/LLM/heuristic tables, original assessment and executed reproduction notebook |
| Publication-associated 386 | [corpus-386/repositories.txt](corpus-386/repositories.txt) | Paper-reported stage counts below; original pooled evidence export pending |
| OpenAIRE 3,211 | [openaire-3211/repositories.txt](openaire-3211/repositories.txt) | Complete population reconstructed; 2,825-run operational metadata received; pooled predictions pending |

The populations are nested: 100 ⊆ 386 ⊆ 3,211. Execution used disjoint batches of 100, 286 and 2,825. These batches are acquisition provenance, not additional scientific populations. The full 3,211 list is reconstructed from the verified disjoint 386 list and final log entries; the original OpenAIRE input is still requested for direct comparison.

## Annotation agreement (paper Table 3)

The two reviewers initially agreed on **354/600 decisions (59%)** and disagreed on **246/600 (41%)**. The jointly adjudicated reference has **384 positive and 216 negative labels**, with 12 repositories positive for all six stages. Initial agreement indicators and final labels are separate data.

| Stage | Agreement | Disagreement | Final positive labels |
|---|---:|---:|---:|
| Collection | 53 | 47 | 36 |
| Processing | 55 | 45 | 44 |
| Method | 53 | 47 | 71 |
| Experimentation | 72 | 28 | 88 |
| Evaluation | 53 | 47 | 66 |
| Dissemination | 68 | 32 | 79 |

## Benchmark performance (paper Tables 4 and 6)

Metrics are rounded to three decimal places. Precision and recall are micro-averaged. Coverage is eligible repositories / 100; exact match requires agreement on all six stages.

| Approach | Input | Eligible | Coverage | Precision | Recall | Micro-F1 | Macro-F1 | Label agreement | Exact match |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Heuristics | Documentation | 96 | 0.960 | 0.865 | 0.591 | 0.702 | 0.620 | 0.679 | 0.115 |
| Heuristics | Code | 95 | 0.950 | 0.821 | 0.277 | 0.414 | 0.353 | 0.498 | 0.011 |
| Heuristics | Combined | 95 | 0.950 | 0.830 | 0.696 | 0.757 | 0.683 | 0.714 | 0.168 |
| LLM | Documentation | 98 | 0.980 | 0.779 | 0.886 | 0.829 | 0.810 | 0.765 | 0.194 |
| LLM | Code | 63 | 0.630 | 0.663 | 0.979 | 0.791 | 0.767 | 0.669 | 0.159 |
| LLM | Combined | 99 | 0.990 | 0.661 | 0.995 | 0.795 | 0.777 | 0.670 | 0.131 |

Heuristic cohorts use the original per-mode scan-completeness flags: **96/95/95**. Restoring 58 zero-filled unknowns to `?` and rendering six existing blanks as `?` preserved all genuine binary labels and original row order. Known positives remain positive even in incomplete scans; incomplete scans do not enter complete-scan metrics. The source workbook was not edited. LLM cohorts require determinate predictions for all six stages: **98/63/99**.

The heuristic combined mode is a logical union of documentation/code evidence, not an average. Its recall is higher than either individual mode on the respective eligible cohorts. The reference is adjudicated and mixed-source; source-specific agreement is not independent evidence-source accuracy. All 100 repositories informed heuristic development. The different denominators prevent interpreting these rows as a controlled same-cohort comparison; common-cohort metrics and always-positive/negative baselines are available in [analysis/reproduction.json](benchmark-100/analysis/reproduction.json).

The combined LLM micro-F1 is **0.79454927**, correctly rounded to **0.795**.

### Confusion totals for the corrected paper Table 7

| Approach | Input | False negatives | False positives |
|---|---|---:|---:|
| Heuristics | Documentation | 151 | 34 |
| Heuristics | Code | 264 | 22 |
| Heuristics | Combined | 111 | 52 |
| LLM | Documentation | 43 | 95 |
| LLM | Code | 5 | 120 |
| LLM | Combined | 2 | 194 |

## 386-repository corpus (paper Table 5)

**Source status:** these counts were supplied from the pooled 100 + 286 export and agree with the paper’s positive totals. The pooled CSV and original per-repository results have not yet been uploaded, so this page reports them explicitly as supplied results, not as independently recalculated outputs.

Each cell below is **positive / negative / unknown**, out of 386. Unknowns are not negatives.

| Stage | Documentation | Code | Combined |
|---|---:|---:|---:|
| Collection | 30 / 313 / 43 | 3 / 336 / 47 | 33 / 304 / 49 |
| Processing | 116 / 234 / 36 | 33 / 308 / 45 | 131 / 217 / 38 |
| Method | 85 / 262 / 39 | 143 / 205 / 38 | 176 / 172 / 38 |
| Experimentation | 244 / 108 / 34 | 23 / 319 / 44 | 247 / 102 / 37 |
| Evaluation | 66 / 278 / 42 | 93 / 250 / 43 | 131 / 212 / 43 |
| Dissemination | 212 / 138 / 36 | 69 / 275 / 42 | 226 / 123 / 37 |

These counts describe detected repository evidence, not whether lifecycle activities were actually performed. There are no reference labels for all 386, so no full-corpus accuracy or F1 is claimed. Publication-associated selection may enrich Dissemination evidence: this corpus should not be treated as representative of all research software.

## OpenAIRE 3,211-repository collection

The 386-repository corpus and the additional 2,825 log identities are disjoint and have a union of exactly **3,211**. The additional run’s summary, progress and final log statuses agree:

| Additional-run outcome | Count | Percentage of 2,825 |
|---|---:|---:|
| Complete | 2,254 | 79.79% |
| Partial | 175 | 6.19% |
| Failed | 396 | 14.02% |
| **Attempted** | **2,825** | **100.00%** |

Of the 396 failures, **234 timed out**, **161 had neither main nor master accessible**, and **one raised a ValueError**. An inaccessible branch pair does not establish that a repository was deleted. The run used main then master, hybrid acquisition, a 120-second repository deadline and a 10 MiB file cap. Original configuration and code/catalog hashes are retained in [run provenance](openaire-3211/provenance/run-2825/README.md). The source checkout reported uncommitted changes, so its commit alone does not fully identify the executed code.

Session wall time was **71,676 seconds (19.91 hours)**. The log contains resumed checkpoints, so dividing this session time by 2,825 is not a reliable mean per-repository processing time. Repository-level complete/partial status is also distinct from mode-specific completeness.

**Pending:** full 3,211 stage totals, merged outcome totals and per-mode coverage require the original detailed results for all batches. The 2,825 outcomes above must not be presented as outcomes for all 3,211. No full-corpus F1 is supported without additional human labels.

## Reproduce and complete the archive

From the repository root:

```bash
uv run --frozen python results/benchmark-100/reproduce_paper.py
```

The executed [notebook](benchmark-100/reproduce_paper.ipynb), full-precision [metrics](benchmark-100/analysis/reproduction.json), [paper comparison](benchmark-100/analysis/paper_comparison.csv), and [original assessment](benchmark-100/assessment/README.md) document the benchmark calculations. LLM prompts and shared conversation references are in [../prompts/](../prompts/).

Follow [UPLOAD.md](UPLOAD.md) to transfer the original run outputs. After hash, identity and configuration checks, complete prediction/status/evidence tables and anonymous provenance will be published in the three collection folders. Keep original checkpoints intact; see [result schemas](../docs/results.md). `python scripts/index_results.py` creates a content inventory after uploads; it does not certify scientific compatibility.
