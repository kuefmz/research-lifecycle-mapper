# Repository research-lifecycle evidence inventory

This table documents real evidence supporting inspection of this artifact. It is not a promised quality rating or an attempt to change classifier rules so the artifact obtains six positive labels.

| Stage | Inspectable evidence | Status and limit |
| --- | --- | --- |
| Collection | src/lifecycle_mapper/openaire.py streams software records; acquisition.py and git_acquisition.py collect immutable repository artifacts | Implemented and exercised by software tests and public acquisition smoke tests |
| Processing | GitHub URL normalization, canonical identity deduplication, checksummed snapshots and reference conversion | Implemented; extraction counts depend on the actual input archive |
| Method | analysis.py, documentation.py and versioned six-stage rules specify the classification method | Implemented; pattern evidence does not prove scientific execution |
| Experimentation | corpus.py, comparison.py, fixed development split and documented mode comparisons | Experimental workflow implemented; dated benchmark comparisons reported; full-corpus experiment not yet completed |
| Evaluation | corrected two-reviewer benchmark, reference audit, per-stage metrics and regression tests | Existing measurements have stated coverage and leakage limits; new-policy results must be regenerated |
| Dissemination | runnable source, all-sheet anonymous workbook, data/provenance inventory, reproduction instructions and data-availability plan | Repository distribution prepared; anonymous mirror and DOI must be verified when actually published |

A six-stage vector describes detectable stage evidence, not repository quality. Documentation should accurately explain what was implemented and measured. Do not state that a full-corpus experiment or DOI release has completed just to obtain another positive label.
