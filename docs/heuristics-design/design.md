# Proposed heuristic design: source-isolated, evidence-first research lifecycle mapping

Status: design for review, not an implemented replacement for v5. No executable
matcher, production rule catalog, workbook label or saved prediction was changed
in this design task. The design aims to explain generalizable stage evidence,
not memorize the 100 reference labels or guarantee a target score.

## 1. What the reference actually establishes

The corrected workbook's final_agreement sheet contains 100 repositories and 600
binary decisions. Positive counts are Collection 36, Processing 44, Method 71,
Experimentation 88, Evaluation 66, Dissemination 79. The jointly adjudicated labels
are the reference; their original per-decision rationales, exact annotation-time
commits and a versioned operational codebook have not been supplied.

Captured documentation is available here for 72 complete development repositories.
It is not available here for the other 28. The 600-row traceability CSV inventories
every label and marks those missing inputs. Existing v5 matches are explicitly
labelled automated candidates, not human-verified annotation explanations. No
match does not prove absence. Selected passages were examined manually below;
this is not a manual verification of all 600 decisions. Operational-holdout errors
were not used to formulate these rules.

The methodological target is evidence of a repository supporting/describing a
research stage, not proof that a research activity actually ran, succeeded, was
scientifically valid, or was reproducible.

## 2. Route files before any stage detector

Use an explicit, versioned source classifier, then send DOC only to documentation
rules and CODE only to implementation rules. Keep OTHER/UNSUPPORTED separate.
Classification is case-insensitive. Skip symlinks, submodules, vendored/generated
folders and administrative license files before content matching, recording why.

| Input | Proposed routing | Interpretation |
|---|---|---|
| .md, .rst, .adoc | DOC | Prose, headings, tables and examples remain documentation |
| .txt | DOC candidate | Require prose/usage/annotation; pure numeric/tabular data is OTHER, not stage evidence |
| README / README.* with recognized text form | DOC | Include extensionless README; do not infer a stage from its existence |
| .py | CODE, Python AST | Code comments/docstrings are not documentation-source evidence |
| .r, .jl, .sh | CODE, declared lexical coverage | Mark parser/rule limitations explicitly |
| .m | CODE candidate | Disambiguate MATLAB from other .m languages before claiming coverage |
| .js, .ts, .java, .go, .rs, C/C++ etc. | CODE, support status tracked | File extension recognition is not implemented stage-detection coverage |
| .ipynb, .rmd, .qmd | MIXED/UNSUPPORTED initially | Only split markdown/code cells after a separately tested parser exists |
| .pdf, binary data, model weights | OTHER/UNSUPPORTED | No indirect stage inference from their filenames |
| .json, .yaml, .toml, CITATION.cff | OTHER metadata initially | Optional future evidence policy, not silently counted as DOC or CODE |

A Python command inside README.md is DOC evidence. The referenced .py file is a
separate CODE input if captured. Neither source's match is copied into the other.
The OpenAIRE description used for corpus selection is not repository DOC evidence.

Changing this eligibility policy requires a new policy version. Preserve old
manifests and explain which newly eligible files were absent from old captures.
An offline replay cannot recover a previously uncaptured extensionless README,
PDF, notebook or oversized file. New retrieval should use the same pinned commit
where possible; do not silently combine annotation-era and new branch contents.

## 3. A good rule has an operational contract

Each rule in rule_catalog.csv / rule_specification.json has one ID, one stage,
one source, required evidence, explicit nonqualifying cases, a synthetic example
and review status. There are 18 proposed DOC rules and 12 proposed CODE rules.
They are not regex lists intended to match any research-looking word.

For a documentation match establish:

1. Actor: the repository/project or its documented user workflow, not a cited tool.
2. Activity: an operation, supported capability, or documented protocol.
3. Object: research inputs, a scientific technique, trial condition, assessment
   target or communicated research output appropriate to that stage.
4. Relation: the project performs/provides/instructs it, rather than merely citing
   it, depending on it, or mentioning its subject matter.
5. Polarity/time: currently supported or documented execution, not explicitly
   unavailable or merely planned.
6. Traceability: exact original file and contiguous lines, commit and content hash.

Two conjunctive patterns must identify distinct evidence roles. The same word
cannot satisfy both activity and object requirements. Broad research context by
itself never identifies a stage. A paper link must not imply all six stages.

Recognize affirmative instructions as documented capabilities: “Run command X to
calculate error” counts even if the wording says the command “will calculate” it.
Reject “we will implement error calculation in future.” A word such as not/will
in an unrelated sentence must not veto an otherwise valid claim.

## 4. Documentation units and evidence strength

Parse Markdown/RST/AsciiDoc headings, prose clauses/paragraphs, lists, tables,
fenced/indented commands, links and HTML comments. Preserve an original-offset map
through normalization. Normalize case, Unicode and presentation markup; do not
remove the information needed to distinguish an external citation from own work.

Allow activity/object evidence in one clause, or a directly connected heading,
explanation and command. Use at most 12 contiguous source lines per evidence
unit as an initial declared bound; do not borrow features across unrelated
sections. A distant section heading may constrain exclusion scope, but cannot
appear as an invented positive phrase inside the excerpt. File-level research
context is background, not a substitute for local stage evidence.

Record three types separately:

- ACCEPTED_DIRECT: explicit claim or description meeting the rule contract.
- ACCEPTED_WORKFLOW: documented command/protocol with its scientific purpose.
- REVIEW_ONLY: plausible clue, filename, paper association with unresolved meaning,
  or an inference needing information not present in the captured documentation.

A stage is positive from at least one accepted match. Review-only clues do not
become positives merely to improve F1. On a complete scan with only review clues,
retain the ordinary no-detection prediction and a review flag; do not remove
these difficult cases from the scored denominator. Missing/incomplete content
may produce unknown decisions and must be reported with coverage.

## 5. One-to-one documentation rule contracts

| ID | Stage and accepted evidence | Not sufficient |
|---|---|---|
| D-COL-01 | Project acquires/downloads/collects identified research inputs | Download dependency; dataset name alone |
| D-COL-02 | Project generates/measures/records research observations | Model prediction or generic log merely called data |
| D-COL-03 | Documented original collected data with subjects/sensor/process provenance | Bundled raw files without collection provenance |
| D-PRO-01 | Cleaning/filtering/normalization/tokenization of research inputs | Generic parsing; installation; unspecified analysis |
| D-PRO-02 | Feature extraction/encoding/merging/resampling/splitting of research data | Pre-existing features merely listed |
| D-PRO-03 | Data-preparation command with purpose and input/output role | clean.py filename or tar extraction alone |
| D-MET-01 | Local implementation of an identified scientific model/algorithm | Algorithm named in a dependency or bibliography |
| D-MET-02 | Local fitting/training/inference/optimization of a scientific model | train.py name without a documented role |
| D-MET-03 | Described local routine performing a scientific computational method | An analysis/src directory without explanation |
| D-EXP-01 | Runnable procedure for a stated research experiment/reproduction | Background experiment discussion; application launch |
| D-EXP-02 | Repeated/controlled seeds, conditions, parameter studies or ablations | Arbitrary loop or unit tests |
| D-EXP-03 | Experimental script/protocol connects conditions to research outputs | Only plotting pre-existing results |
| D-EVA-01 | Scientific outcome metric or uncertainty assessment | Result word; isolated metric name; test pass rate |
| D-EVA-02 | Scientific comparison against labels/baselines/methods/conditions | Uncontextualized timing/logging |
| D-EVA-03 | Evaluation workflow/table/figure identifies assessed quantity and criterion | Figure generation alone or Evaluation heading alone |
| D-DIS-01 | Explicit distribution/deposit of identified research outputs | Software DOI, badge, license or repo existence alone |
| D-DIS-02 | Creation/export of scientific figures/tables/report for communication | Generic plot or software documentation |
| D-DIS-03 | Paper/citation association, stored as its own evidence attribute | REVIEW ONLY until its mapping to Dissemination is resolved |

D-COL-01 currently proposes that research-dataset download is acquisition. If
humans intended Collection to mean original observation collection only, change
this contract before implementation, rather than adding dataset-specific vetoes.
D-PRO-03 deliberately leaves archive unpacking unresolved as a coding boundary.
D-MET does not imply novelty: implementation/instantiation of an existing scientific
method may count, but dependency installation alone does not. If the human codebook
intended novel-method contribution only, that is a different contract.

## 6. One-to-one source-code rule contracts

Read executable structure, not comments, filenames, directory names or imports
alone. Never execute repository code. Python uses AST/call/argument relations;
other languages need explicit parser/lexical support and corresponding tests.
AST literal resource paths can supply acquisition/export provenance, but scientific
keywords in arbitrary strings must not establish a code stage.

| ID | Stage and executable evidence | Not sufficient |
|---|---|---|
| C-COL-01 | Acquisition call linked to research inputs and downstream storage/use | HTTP call by itself |
| C-COL-02 | Observation generation/recording feeding research data | Generic logging or model predictions |
| C-PRO-01 | Data preparation operation on identified research inputs | Generic config/string handling |
| C-PRO-02 | Feature/representation building or scientific data splitting | Imports, directory or file names |
| C-MET-01 | Scientific computation with identifiable computational operations | Function name or comment alone |
| C-MET-02 | Fitting/training/inference/optimization on research inputs | Model import or generic application call |
| C-EXP-01 | Research trial runner over conditions with scientific call/outcomes | An arbitrary for loop |
| C-EXP-02 | Actual research parameter/ablation study with evaluation | Parameter-search import alone |
| C-EVA-01 | Metric/statistical operation with outcomes and reference/criterion | accuracy variable or software assertion |
| C-EVA-02 | Research comparison/uncertainty/hypothesis test linked to results | Timer/logger alone |
| C-DIS-01 | Scientific figure/table/report export traced to research results | savefig without research context |
| C-DIS-02 | Research-output deposit/publication operation and payload | URL literal or software-release function alone |

Use same-function/statement or a bounded, explicitly described data-flow relation
for operation+object evidence; do not insist on names such as
fit_statistical_model. Scientific scripts may live under tests; identify software
unit/integration-test context rather than automatically treating every tests path
as unrelated research. Importing a library is not the same as using it to perform
a research operation. These executable contracts are not implemented changes yet.

## 7. Aggregation and missingness

For each stage/source: accepted match => 1; complete supported scan with no match
=> 0 (not detected); incomplete/inaccessible/unsupported relevant content with no
positive => unknown. Keep artifact acquisition completeness and detector language
coverage separate. “File downloaded” must not imply “language analyzed.”

Combined uses three-valued OR: any 1 => 1; 0 OR 0 => 0; otherwise unknown.
For example DOC=0 and CODE=unknown does not establish combined absence. Combined
is not an average, vote, learned confidence score or a replacement for the
documentation-only annotation target.

Preserve missing decisions in reports for all 100 repositories. Score complete
cases using disclosed denominators and also report per-label available/unknown
counts. Do not select a more favorable denominator after seeing scores. Compare
modes on the same complete cohort as well as their individual coverage.

## 8. What the inspected reference examples show

These examples are evidence/coding-boundary checks, not repository-specific rules.
Repository identities are only audit keys and must never enter a matcher.

| Captured documentation | final_agreement observation | Design implication |
|---|---|---|
| count-vector-paper-experiments README line 3: code and data used in a linked paper | Dissemination=0 | Paper association alone cannot be assumed equivalent to the human stage |
| nv-adaptive README line 3: accompanies paper, provides data and code; lines 9/26 describe generated figures | Collection=1, Method=1, Evaluation=1, Dissemination=1 | Figure/data presence has several plausible roles; do not infer all stages from the paper relation |
| count-vector README lines 11–19: unzip data; reproduce laboratory setup results; train.py command | Collection/Processing/Method/Experimentation/Evaluation=1 | Some labels may use artifact/workflow inferences; the exact rationale is absent |
| norms-cogsci19 README line 12: anonymized data collected from 200 workers | Collection=1 | Direct observation provenance can support D-COL-03 |
| pbesstategraph README line 35: transformations applied to a research representation | Processing=1 | Research objects are not always named dataset; preserve domain-object roles |
| eusipco2017 README line 6: code for preprocessing, training and evaluation; lines 35–40 evaluation command | Processing/Method/Evaluation=1, Experimentation=0 | Training and the word experiments must not automatically activate Experimentation |
| compression-experiments README line 11: compression ratio measured across input sizes, tables exported | Method=0, Experimentation/Evaluation/Dissemination=1 | Measurement and communication evidence are distinct from implementing a scientific method |
| unbiasedpathsampling README lines 3–7: estimators implemented; scripts reproduce report figures | Method/Experimentation/Dissemination=1, Evaluation=0 | Reproducing figures must not automatically mean scientific evaluation |
| processingctrdata README lines 4–9: process/analyse/plot experimental data, bootstrap errors | Collection/Processing/Method/Evaluation=1, Experimentation/Dissemination=0 | Plotting and experiments in background are not sufficient; original collection and dissemination boundaries need rationale |

The differences do not establish that final labels are wrong. They may reflect
unstated coding distinctions, annotation-time documentation different from current
main/master, or incomplete captures. A deterministic content-only rule can match
the reference exactly only if the distinguishing evidence and definitions are
available. Do not invent provenance or memorize exceptions to attain a score.

## 9. Evidence record and audit record

Every match records rule ID/version, source class, evidence type, repository
commit, file, original lines/excerpt, content hash, activity/object/actor/relation,
polarity, accepted/review/excluded decision and explicit exclusion reasons. Keep
paper_association and research_output_communication as separate evidence attributes.

Every reference audit decision records final label, available annotation rationale,
annotation snapshot (unknown when unknown), captured evidence, source mismatch or
history uncertainty, proposed rule, reviewer interpretation and unresolved question.
A zero label does not require proving scientific absence. A positive without a
traceable excerpt is unresolved, not a license to fabricate a positive.

## 10. Validation before the overnight run

Freeze source-routing policy, definitions, DOC/CODE catalogs and rule versions.
For each proposed rule add a synthetic positive and negative cases for negation,
future work, third-party activity, installation, generic operations, source leakage
and overlapping stage concepts. Include realistic varied wording, not copied
repository-specific phrases. No automatic label matching or target-score loop.

Replay baseline and candidate on identical pinned captures. Preserve all results.
Inspect development confusion matrices and evidence precision, not F1 alone.
Report micro/macro F1, per-stage precision/recall, exact match, per-label accuracy,
coverage and constant baselines. Existing 80/20 partitions are operational after
aggregate inspection and cannot be marketed as an independent blinded test.
Source/combined correctness needs separately reviewed source/combined reference
labels; documentation labels support only cross-scope agreement diagnostics.

Only after design choices are settled: implement new eligibility with compatibility,
wire --rules-dir into live corpus run, bind its hash to checkpoints, and freeze
before acquisition. Do not silently run old default v3 when intending v5/v6.
The larger input's previous verified counts are 3,876 software-to-GitHub links
and 3,211 unique repositories. Measure any new list's count; do not force 3,878.

## 11. Four decisions required to map this design to the final labels

1. Collection: original observations only, or acquisition of external datasets
   too? Is an included dataset evidence without an acquisition statement?
2. Processing: does unpacking/loading raw data count, or only substantive data
   transformations? Does generic analysis count, or belong to Method/Evaluation?
3. Method/Experimentation/Evaluation: are implemented/instantiated methods counted
   regardless of novelty, and what separates training, reproducing outputs and
   actual comparative assessment? Figure generation alone should not imply all.
4. Dissemination: does associated-paper citation count, or only repository
   preparation/distribution of research outputs? What explains the reviewed
   paper-associated positive/negative cases?

Answers must be recorded as the human operational codebook. Exact agreement is
not a valid design requirement when these distinctions cannot be recovered from
the available input. The valid requirement is transparent, testable, general rules
that faithfully implement the agreed coding definitions.
