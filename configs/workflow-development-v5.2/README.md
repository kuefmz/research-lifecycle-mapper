# Workflow development v5.2

82 rules, built reproducibly with `python scripts/build_workflow_profile.py` from v5.1. Prior profiles remain unchanged.

## Documentation change

Remove MET_DOC_WORKFLOW_V5_1 and MET_DOC_WORKFLOW_V5_2: generic model/training terminology and code accompanying research are insufficient Method evidence. Replace them with explicit implementation/derivation of a research method, or a documented multistep computational mechanism with named scientific operations. Other documentation rules are unchanged. This is a targeted precision correction; broad benchmark improvement has not yet been measured.

## Code changes

Add executable evidence rules for shell preparation commands with input/options, evaluation commands with arguments or redirected output, gradient updates, numerical optimizer calls, repeated scientific calls, held-out prediction differences, and standard metric calls. Comments and string contents remain masked. Repeated scientific calls require an executable loop context elsewhere in the same file; this is file-level co-occurrence, not interprocedural data-flow proof. Excerpts identify the invocation; the complete pinned source supplies loop context.

`rule_catalog.csv` records every exact rule specification. All new rules are development candidates. No repository-specific exceptions or reference labels enter matching. Existing data/vendor exclusions, main/master policy, notebook separation, no size caps and 300-second deadline remain unchanged.

## Targeted source replay

The reported autoencoder README now predicts Experimentation and Dissemination only, matching its final agreement. Its inspected MATLAB files additionally yield Method, Experimentation and Evaluation evidence. That code finding is not a documentation false positive: source activities may be undocumented. The reported cross-validation shell evaluation invocation is now detected, and the multistep reranker description supplies Method evidence. These checks do not establish full-benchmark F1 or independent validation. Development on this benchmark must be disclosed.

Use `--rules-dir configs/workflow-development-v5.2` with a fresh output directory and the final-agreement workbook supplied via `--reference` for display only. See docs/run-benchmark-100.md.
