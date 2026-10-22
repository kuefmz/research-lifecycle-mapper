# Simulation and evidence-role development v5.3

91 rules; rebuild with `python scripts/build_simulation_profile.py`. Exact specifications are in rule_catalog.csv. Prior profiles remain unchanged.

## Executable evidence

- Physical-equation Method: assignment to an identified physical/statistical quantity, multiplicative/divisive arithmetic with variables, and a nonlinear numerical operation in the same source file. File context is a lexical safeguard, not data-flow proof.
- Agent-decision Method: compute an agent decision and dispatch the action to a simulated environment within the same executable brace block.
- Agent Experimentation: execute agent updates inside a bounded simulated-time loop and explicitly advance time. Generic loops do not qualify.
- Factorial Experimentation: apply an experimental function across explicit design rows. Generic mapping does not qualify.

Comments/string contents remain masked; file extension alone never creates a positive label. Ordinary arithmetic, constants, declarations, unrelated functions, generic software loops and commented examples are negative regression cases. Test/vendor/data-content exclusions remain unchanged. No source code is executed.

## Documentation evidence roles

- Supplied/sample measured observations support Collection. Generating simulator logs or merely obtaining an existing dataset does not activate the broad Collection workflow proxy.
- Explicit research-input subsetting supports Processing. A path containing filter or a tutorial filtering software-log lines does not activate the broad Processing proxy.
- Archived research data/results support Dissemination, not automatically Experimentation or Evaluation. The word performance is not the execution verb perform.
- Evaluation workflow proxies require concrete metric, validation, or performance-measurement evidence beyond a title containing benchmark/evaluation.
- Plot/report workflow proxies require an actual output artifact with publication/export purpose; a URL ending .html or a script reporting HTTP status is insufficient.
- Named statistical experimental-design implementations and documented agent interaction mechanisms support Method.
- Licence/copyright/bibliography text is excluded from documentation stage evidence.

## Checked examples and limits

`data/reports/development-four-v53.json` records file hashes, upstream tree identities where retrieved, before/after labels and matched rule/line attribution for the four reported cases. It is a targeted development review of fetched files, not a completed full-repository benchmark. The inspected READMEs for forhytm, atom and all-versus-one match the supplied reference; doe-sparql retains one Dissemination disagreement because it explicitly describes published study code. This is retained for codebook review rather than overridden by repository identity. Rules never consume labels or repository names.

Inspected R/Java files now detect physical model equations, agent decisions, simulated time execution and experimental-design runs. No claim is made that every stage is implemented or detectable. No eligible source files is explicitly logged; code zeros then mean no available implementation evidence. A completed scan still means only that the selected heuristics ran.

Use this profile with a fresh corpus output directory. Main then master only, exact supplied repository order, separate notebook Markdown/code cells, uncapped file sizes and the 300-second wall-clock deadline remain unchanged. Benchmarks used to revise these rules are development data; full agreement/F1 and coverage must be measured and reported without a held-out-performance claim.
