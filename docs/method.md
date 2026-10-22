# Final method (release 1.0)

## Task and evidence

The prediction unit is a public GitHub repository at a resolved immutable commit.
Six independent labels are ordered Collection, Processing, Method, Experimentation,
Evaluation, Dissemination. The classifier is deterministic; it makes no LLM calls.

| Stage | Target activity | Insufficient on its own |
|---|---|---|
| Collection | Acquisition, measurement, recording or generation of research inputs | An arbitrary file read or existing dataset download |
| Processing | Preparing, cleaning, transforming or deriving research inputs | Loading a file without preparation |
| Method | Scientific models, numerical methods or research algorithms | Generic program functionality or an unspecified model mention |
| Experimentation | Research trials, configured simulations or systematic experimental runs | Arbitrary program execution or unit tests |
| Evaluation | Assessment of research outcomes through metrics, validation or comparisons | Software test success |
| Dissemination | Communicating or exporting research results, papers or research outputs | An arbitrary print statement |

These definitions describe targets; exact operational predicates are in the rule catalog.
No-match can reflect rule limitations, naming variation, unsupported material or ambiguity.

Documentation-only and code-only findings are computed separately. A combined positive
is their logical OR. A negative is supported only when the relevant scan is complete;
otherwise the stage is unknown. A positive remains known even if other evidence is
unavailable. Mode completeness and known stage values must therefore be reported
separately. No eligible code is explicitly recorded; zeros then mean no available
implementation evidence, not proof that the activity was not performed.

## Acquisition and eligibility

The paper corpus runner resolves `main`, falling back to `master` only, and records the
selected branch, commit, inventory, exclusions and captured-byte hashes. Other default
branches are outside scope. This is an operational restriction, not a universal claim
that main is the authoritative scientific version. Historical annotation-time commits
may differ from acquired commits.

Hybrid transport uses unauthenticated raw-content requests and necessary authenticated
REST metadata/tree requests; it reduces REST use but does not eliminate network costs.
Rate-limit waits count toward the 120-second repository deadline. A guarded subprocess
is terminated at the deadline and records stop diagnostics. Paper commands and the UI
use a 10 MiB (10,485,760-byte) per-file cap. The corpus CLI's default is unlimited bytes;
always record the actual command and manifest.

Current eligibility policy is `eligibility-7-bundled-data-test-exclusions`. Inventoried
exclusions include symlinks/submodules, unsupported and binary artifacts, data formats,
vendor/generated/fixture material, minified assets/source maps, known bundled jQuery
basenames, identified parallel-corpus artifacts, and software-test source paths.
Non-README TXT data artifacts under named data directories are excluded. More than five
regular `.txt` files in an immediate folder excludes all TXT files there; nested folders
are counted independently. See `source_kind` and `txt_folder_counts` in acquisition.py
for exact predicates. Exclusions bound the observable scope; they are not unknowns
caused by network failure and should still be disclosed.

Data-file contents (including CSV and TTL) and nonempty data folders do not independently
qualify a stage. Documentation is selected by implemented suffixes; do not assume every
possible documentation format is covered. Notebook Markdown cells are documentation,
code cells are source, and stored outputs are ignored. Serialized Wolfram notebook
boxes are not reconstructed and can leave code scans incomplete.

## Rule execution

105 source-specific conjunctive rules use positive predicates, contextual constraints,
exclusions and bounded windows. Documentation matching handles prose/heading context and
workflow units. Code uses Python syntax analysis where supported and language-specific
or portable lexical masking elsewhere. Comments and strings alone must not establish
executable evidence. Imports and declarations alone are insufficient for operation rules.
File-level context means co-occurrence, not interprocedural data flow. Language detection
uses a bundled Linguist-derived catalog with its original license; broad recognition
is not comprehensive semantic analysis.

Text decoding tries strict UTF-8, followed by a controlled Windows-1252 fallback with
binary/control checks and exact byte round-tripping. No replacement/ignored bytes are
used to manufacture successful scans. Encoding decisions are recorded; the fallback
is a hypothesis, not universal encoding detection.

Evidence retains rule IDs, excerpts, source type, paths, line/cell information and pinned
links where available. Predictions never read final human labels. Reference input to
the runner is for display/comparison only.

## Research interpretation

The 100 repositories informed rule development. Report their scores as development
reference agreement, not held-out generalization. The final adjudicated reference is
currently treated as mixed-source: the initial documentation-focused annotation intent
must not be confused with a verified source-specific ground truth. Independent reviewer
labels and final consensus are different data products. Code/combined agreement does
not independently validate code evidence. Compare modes on the common complete cohort
and include matching-cohort trivial baselines. No result establishes scientific quality,
methodological completeness or successful reproduction.
