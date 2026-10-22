# How the final heuristics work

This guide explains the actual maintained 105-rule profile, not an alternative rule set. The [exact specification](rules.md) preserves every runtime object; the [CSV catalog](../configs/heuristics/rule_catalog.csv) supports inspection. Rules and predictions are unchanged by this documentation.

## From repository files to six stage decisions

1. Resolve main, otherwise master, and record the immutable commit. Apply the documented eligibility policy, deadline and file cap. Inventory exclusions and acquisition failures separately.
2. Classify eligible material into documentation or code before matching. Notebook Markdown cells are documentation, code cells are code, and stored outputs are ignored. Data contents (including CSV/TTL), binaries, tests, vendor/generated/minified artifacts are not positive research evidence. A nonempty data directory alone is insufficient.
3. Documentation is segmented into prose and documented workflow units. All positive predicates of one rule must match its eligible unit; exclusions, heading scope and repository scope then determine whether the candidate is accepted. A workflow-layer rule also requires its command pattern. Rules with the documented-workflow unit policy can use their specified document-level scope fallback.
4. Code comments and strings are masked. Python syntax, brace-block or portable lexical detectors restrict candidates to their implemented code units. Portable file-context patterns must all match the masked file, then every positive predicate must match a bounded statement window. This is lexical co-occurrence, not execution or data-flow analysis. Extension-specific native rules apply only to their specified languages; portable recognition broadens coverage but does not make all languages semantically equivalent.
5. Any accepted rule yields positive evidence for its stage and source. A stage is 0 only when its relevant eligible scan is complete and no rule qualifies; otherwise a missing finding is unknown. Known positives survive an incomplete scan. Combined evidence is the union, not an average or a third independently tuned classifier.
6. Record rule ID, source, path, line/cell, content hash, matched conditions and pinned commit link where available. Rule metadata such as status/justification is descriptive; it is not a probability or independent human approval. Reference labels are never classifier inputs.

## Reading a rule

| Field | Operational meaning |
|---|---|
| `positive` | All listed regex conditions must match the implemented local unit/window; conditions are AND, not OR |
| `exclusions` | Any matching negative condition rejects that local candidate |
| `window_lines` | Bound for code sliding windows (1–12 lines); documentation uses its segmentation/unit policy rather than a generic whole-file keyword search |
| `file_context_patterns` | For portable code rules, all patterns must also match the masked file |
| `context_pattern` | Documentation repository scope, or header context for applicable brace rules |
| `heading_exclusions`, `scope_exclusions` | Reject excluded document sections and third-party/ambiguous scope |
| `layer`, `unit_policy`, `command_pattern` | Select documentation units and enforce demonstrated commands for workflow-layer matches |
| `extensions`, `detector`, `scope` | Select applicable code language and syntax/lexical unit |
| `supporting` | Additional context recorded by applicable detectors; not a substitute for required positives |
| `required_evidence_fields` | Provenance contract for evidence records |
| `id`, `version`, `status`, `justification` | Stable provenance metadata, not additional releases or independent validity scores |

The suffixes in rule IDs are stable identifiers retained so saved evidence remains traceable. They do not select older profiles. Only `configs/heuristics/` is maintained. Some stored descriptions retain conservative research-candidate terminology; their presence does not disable a rule. See the loader and detectors for operational fields.

## Coverage by stage

| Stage | Documentation rules | Code rules |
|---|---:|---:|
| Collection | 8 | 5 |
| Processing | 8 | 6 |
| Method | 11 | 14 |
| Experimentation | 8 | 9 |
| Evaluation | 9 | 12 |
| Dissemination | 9 | 6 |

The following descriptions are one-to-one with the frozen rule objects. Patterns are shown verbatim, so synonyms or alternative spellings count only if the regex actually covers them. These are detection rules, not proof that an activity succeeded.

## Collection

### COL_CODE_ACTIVITY_V1

Acquire or generate raw observations for research.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** A declared raw research acquisition activity plus an acquisition operation; HTTP alone is insufficient.

**All required positive patterns:**

```regex
^\s*def\s+(?:collect|acquire|record)_(?:research_data|sensor_observations|participant_responses)\s*\(
\b(?:requests\.get|sensor\.read|survey\.responses)\s*\(
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

### COL_DOC_EXPLICIT_V2

Acquire or generate raw observations for research.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** A declared raw research acquisition activity plus an acquisition operation; HTTP alone is insufficient. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(collect(?:s|ed|ing)?|acquir(?:e|es|ed|ing)|record(?:s|ed|ing)?)\b
\b(raw (?:research )?data|research dataset|sensor observations|participant responses)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### COL_DOC_CONTEXTUAL_V2

Acquire or generate raw observations for research.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** A declared raw research acquisition activity plus an acquisition operation; HTTP alone is insufficient. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:download(?:s|ed|ing)?|collect(?:s|ed|ing)?|acquir(?:e|es|ed|ing)|harvest(?:s|ed|ing)?|generat(?:e|es|ed|ing)|record(?:s|ed|ing)?)\b
\b(?:research (?:data(?:sets?)?|observations|inputs)|raw (?:research )?data|experimental measurements|sensor (?:data|observations)|participant responses|scientific datasets?)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### COL_DOC_WORKFLOW_V2

Acquire or generate raw observations for research.

**Source:** documentation. **Detector/layer:** workflow. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** A declared raw research acquisition activity plus an acquisition operation; HTTP alone is insufficient. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:download(?:s|ed|ing)?|collect(?:s|ed|ing)?|acquir(?:e|es|ed|ing)|harvest(?:s|ed|ing)?|generat(?:e|es|ed|ing)|record(?:s|ed|ing)?)\b
\b(?:research (?:data(?:sets?)?|observations|inputs)|raw (?:research )?data|experimental measurements|sensor (?:data|observations)|participant responses|scientific datasets?)\b
```

**Local scope/header pattern:**

```regex
\b(?:run|use|execute)\s+(?:this|the|our)\s+(?:command|workflow|tutorial)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### COL_DOC_RESEARCH_V3

Repository-scoped research activity and object using common disciplinary wording.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object conjunction; supports instructional and passive repository descriptions without requiring the literal word research.

**All required positive patterns:**

```regex
\b(?:collect(?:s|ed|ing)?|acquir(?:e|es|ed|ing)|record(?:s|ed|ing)?|gather(?:s|ed|ing)?|recruit(?:s|ed|ing)?)\b
(?<![-_./])\b(?:data(?:sets?)?|corpus|corpora|measurements|observations|samples|responses)\b
\b(?:raw|sensor|participants?|patients?|responses|observations|measurements|survey|corpus\s+construct\w*)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|run|python|available|download|paper|publication|cite|citation)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
\b(?:could|would|might|hypothetically|in principle)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### COL_CODE_RESEARCH_V3

Research-specific implementation operation with a contextual identifier.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive operation and contextual identifier in the same Python function; comments and strings masked. No repository identity or human label is a feature.

**All required positive patterns:**

```regex
^\s*def\s+(?:download|fetch|collect|scrape|acquire)_(?:data(?:set)?|corpus|observations|measurements)\w*\s*\(
\b(?:requests\.get|urlretrieve|urlopen|download\.file|read_sensor)\s*\(
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

### COL_CODE_MULTILANG_V3

Conjunctive research operation and contextual identifier in R, Julia, MATLAB or shell.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 6 lines (subject to detector unit policy).

**Why this rule exists:** Lexically masked comments and strings cannot provide either condition; matched executable statements are evidence, without asserting scientific validity. Function/call context for method; research repetitions for experimentation.

**All required positive patterns:**

```regex
\b(?:download\.file|Downloads\.download|wget|curl)\b
\b(?:destfile|dataset|corpus|data_url|raw_data)\b
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

**scope:** `statement`.

**extensions:** `['.r', '.jl', '.m', '.sh']`.

### COL_DOC_EXTENDED_V4

Candidate extended wording for collection.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object wording from the conceptual stage definition; no benchmark identity, labels or unique repository phrase used. Synthetic tests only; empirical benefit unverified.

**All required positive patterns:**

```regex
\b(?:generat(?:e|es|ed|ing)|simulat(?:e|es|ed|ing)|sampl(?:e|es|ed|ing))\b
\b(?:synthetic|simulated|raw|experimental)\s+(?:data(?:sets?)?|observations|measurements|samples)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this\s+(?:tool|package|software|repository|code|library|implementation)|the\s+(?:tool|package|software|repository|code|library))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### COL_DOC_WORKFLOW_V5_1

Development candidate: documentation-described collection activities and artifacts.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General heading/paragraph/workflow evidence motivated by development-only error review; no repository identity or label enters matching. Stage proxies need codebook review; not an independent evaluation.

**All required positive patterns:**

```regex
(?<![\w./-])(?:collect\w*|acquir\w*|gather\w*|record\w*|survey\w*|recruit\w*)\b
\b(?:data(?:sets?)?|corpus|corpora|observations|measurements|samples|responses|participants|subjects)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this (?:study|repository|software|experiment)|collected (?:data|responses)|recorded (?:data|responses))\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not supported|not implemented|does not|do not|cannot|doesn.t|don.t|never|future work|planned|todo|hypothetical|example only)\b
\b(?:could|would|might|hypothetically|in principle)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:unit|integration|software) tests?\b
```

**unit_policy:** `sentence-scope-final`.

### COL_DOC_WORKFLOW_V5_2

Development candidate: documentation-described collection activities and artifacts.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General heading/paragraph/workflow evidence motivated by development-only error review; no repository identity or label enters matching. Stage proxies need codebook review; not an independent evaluation.

**All required positive patterns:**

```regex
\b(?:raw data|data collected|collected data|participant responses|survey responses)\b
\b(?:contain\w*|provid\w*|includ\w*|collect\w*|record\w*|from|stored|files?)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|package|library|run|python|Rscript|MATLAB|notebook|paper|publication|cite|citation|download)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not supported|not implemented|does not|do not|cannot|doesn.t|don.t|never|future work|planned|todo|hypothetical|example only)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:unit|integration|software) tests?\b
```

**unit_policy:** `documented-workflow-v5`.

### COL_CODE_BRACE_ACQUIRE_V51

Acquire research inputs with a research-data identifier in the same executable block.

**Source:** code. **Detector/layer:** brace-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Acquire research inputs with a research-data identifier in the same executable block. Comments/literals are masked and all matching conditions must occur inside one executable brace block, excluding declarations and software-test paths. Lexical candidate evidence, not semantic proof.

**All required positive patterns:**

```regex
\b(?:curl_easy_perform|curl_exec|fetch|readSensor|read_sensor|downloadData|downloadDataset|downloadCorpus)\s*\(
\b(?:dataset|corpus|observations|measurements|raw_data|dataUrl|datasetUrl|research_data)\b
```

**scope:** `lexical-block`.

**extensions:** `['.c', '.cpp', '.cc', '.h', '.hpp', '.java', '.js', '.ts', '.go', '.rs', '.scala']`.

### COL_CODE_PORTABLE_ACQUIRE_V51

Acquire identified research inputs.

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Acquire identified research inputs. All conditions must occur within one lexical statement. Comments and literals are masked. This is a language-neutral candidate heuristic, not a semantic proof.

**All required positive patterns:**

```regex
\b(?:fetch|download(?:\.file|[_-]?(?:data|dataset|corpus))?|curl_easy_perform|read[_-]?sensor|acquire[_-]?data)\b\s*(?:\(|[A-Za-z_$])
\b(?:dataset|corpus|observations|measurements|raw_data|dataUrl|datasetUrl|research_data)\b
```

**scope:** `portable-statement`.

### COL_DOC_PROVIDED_MEASUREMENTS_V53

Documentation explicitly describes supplied/sample measured research observations.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Supplied measured observations are Collection evidence; generic generated examples or a data folder alone do not satisfy this rule.

**All required positive patterns:**

```regex
\b(?:sample\s+(?:data|dataset)|(?:data|dataset)\s+(?:contains?|includes?))\b
\b(?:measured|observed|recorded|collected)\b
\b(?:meteorological|temperature|precipitation|humidity|wind|radiation|sensor|participants?|patients?|survey)\b
```

**Local scope/header pattern:**

```regex
\b(?:sample|data|dataset|our|we|provided|contains)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

## Processing

### PRO_CODE_ACTIVITY_V1

Prepare research data through cleaning or transformation.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** A preparation operation scoped to research observations; generic parsing is insufficient.

**All required positive patterns:**

```regex
^\s*def\s+(?:clean|preprocess|normalize)_(?:research_dataset|sensor_observations|experimental_measurements)\s*\(
\.(?:dropna|fillna|transform|fit_transform)\s*\(
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

### PRO_DOC_EXPLICIT_V2

Prepare research data through cleaning or transformation.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** A preparation operation scoped to research observations; generic parsing is insufficient. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(clean(?:s|ed|ing)?|preprocess(?:es|ed|ing)?|normaliz(?:e|es|ed|ing))\b
\b(research dataset|raw research data|sensor observations|experimental measurements)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### PRO_DOC_CONTEXTUAL_V2

Prepare research data through cleaning or transformation.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** A preparation operation scoped to research observations; generic parsing is insufficient. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:clean(?:s|ed|ing)?|filter(?:s|ed|ing)?|transform(?:s|ed|ing)?|normaliz(?:e|es|ed|ing)|preprocess(?:es|ed|ing)?|prepar(?:e|es|ed|ing)|extract(?:s|ed|ing)?\s+features)\b
\b(?:research data(?:sets?)?|raw (?:research )?data|scientific datasets?|experimental measurements|sensor observations|features from research data)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### PRO_DOC_WORKFLOW_V2

Prepare research data through cleaning or transformation.

**Source:** documentation. **Detector/layer:** workflow. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** A preparation operation scoped to research observations; generic parsing is insufficient. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:clean(?:s|ed|ing)?|filter(?:s|ed|ing)?|transform(?:s|ed|ing)?|normaliz(?:e|es|ed|ing)|preprocess(?:es|ed|ing)?|prepar(?:e|es|ed|ing)|extract(?:s|ed|ing)?\s+features)\b
\b(?:research data(?:sets?)?|raw (?:research )?data|scientific datasets?|experimental measurements|sensor observations|features from research data)\b
```

**Local scope/header pattern:**

```regex
\b(?:run|use|execute)\s+(?:this|the|our)\s+(?:command|workflow|tutorial)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### PRO_DOC_RESEARCH_V3

Repository-scoped research activity and object using common disciplinary wording.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object conjunction; supports instructional and passive repository descriptions without requiring the literal word research.

**All required positive patterns:**

```regex
(?<![-_./])\b(?:preprocess(?:es|ed|ing)?|tokeniz(?:e|es|ed|ing)|normaliz(?:e|es|ed|ing)|clean(?:s|ed|ing)?|filter(?:s|ed|ing)?|extract(?:s|ed|ing)?|convert(?:s|ed|ing)?|transform(?:s|ed|ing)?)\b
(?<![-_./])\b(?:data(?:sets?)?|corpus|corpora|features|samples|observations|sequences)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|run|python|available|download|paper|publication|cite|citation)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### PRO_CODE_RESEARCH_V3

Research-specific implementation operation with a contextual identifier.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive operation and contextual identifier in the same Python function; comments and strings masked. No repository identity or human label is a feature.

**All required positive patterns:**

```regex
^\s*def\s+(?:preprocess|clean|normalize|tokenize|extract_features)(?:_\w+)?\s*\(
\b(?:dropna|fillna|fit_transform|transform|tokenize|standardize|normalize)\s*\(
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

### PRO_CODE_MULTILANG_V3

Conjunctive research operation and contextual identifier in R, Julia, MATLAB or shell.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 6 lines (subject to detector unit policy).

**Why this rule exists:** Lexically masked comments and strings cannot provide either condition; matched executable statements are evidence, without asserting scientific validity. Function/call context for method; research repetitions for experimentation.

**All required positive patterns:**

```regex
\b(?:na\.omit|complete\.cases|zscore|standardize|tokenize)\s*\(
\b(?:data|dataset|features|samples|x_train)\b
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

**scope:** `statement`.

**extensions:** `['.r', '.jl', '.m', '.sh']`.

### PRO_DOC_EXTENDED_V4

Candidate extended wording for processing.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object wording from the conceptual stage definition; no benchmark identity, labels or unique repository phrase used. Synthetic tests only; empirical benefit unverified.

**All required positive patterns:**

```regex
\b(?:prepar(?:e|es|ed|ing|ation)|standardiz(?:e|es|ed|ing)|augment(?:s|ed|ing|ation)?|resampl(?:e|es|ed|ing)|split(?:s|ting)?)\b
\b(?:data(?:sets?)?|corpus|corpora|features|observations|training data)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this\s+(?:tool|package|software|repository|code|library|implementation)|the\s+(?:tool|package|software|repository|code|library))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### PRO_DOC_WORKFLOW_V5_1

Development candidate: documentation-described processing activities and artifacts.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General heading/paragraph/workflow evidence motivated by development-only error review; no repository identity or label enters matching. Stage proxies need codebook review; not an independent evaluation.

**All required positive patterns:**

```regex
(?<![\w./-])(?:preprocess\w*|clean\w*|normaliz\w*|tokeniz\w*|transform\w*|convert\w*|merg\w*|split\w*|augment\w*|extract\w*\s+features?|prepar(?:e|es|ed|ing)\s+(?:the\s+)?data|data preparation)\b
\b(?:data(?:sets?)?|corpus|corpora|features?|samples|observations|sequences|files?|text|images|input)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|package|library|run|python|Rscript|MATLAB|notebook|paper|publication|cite|citation|download)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not supported|not implemented|does not|do not|cannot|doesn.t|don.t|never|future work|planned|todo|hypothetical|example only)\b
\b(?:reduced model|model reduction|reduced[- ]order model)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:unit|integration|software) tests?\b
```

**unit_policy:** `documented-workflow-v5`.

### PRO_CODE_BRACE_TRANSFORM_V51

Call a data-preparation operation on identified research-input variables.

**Source:** code. **Detector/layer:** brace-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Call a data-preparation operation on identified research-input variables. Comments/literals are masked and all matching conditions must occur inside one executable brace block, excluding declarations and software-test paths. Lexical candidate evidence, not semantic proof.

**All required positive patterns:**

```regex
\b(?:normalize|normalise|standardize|tokenize|preprocess|extractFeatures|extract_features|resample|splitDataset|cleanData)\s*\(
\b(?:data|dataset|corpus|samples|features|measurements|tokens|sentences|featureVector)\b
```

**scope:** `lexical-block`.

**extensions:** `['.c', '.cpp', '.cc', '.h', '.hpp', '.java', '.js', '.ts', '.go', '.rs', '.scala']`.

### PRO_CODE_PORTABLE_TRANSFORM_V51

Transform identified research inputs.

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Transform identified research inputs. All conditions must occur within one lexical statement. Comments and literals are masked. This is a language-neutral candidate heuristic, not a semantic proof.

**All required positive patterns:**

```regex
\b(?:normalize|normalise|standardize|tokenize|preprocess|extract[_-]?features|resample|split[_-]?dataset|clean[_-]?data)\b\s*(?:\(|[A-Za-z_$])
\b(?:data|dataset|corpus|samples|features|measurements|tokens|sentences|featureVector)\b
```

**scope:** `portable-statement`.

### PRO_CODE_SHELL_PREP_V52

shell prep

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** shell prep Development evidence candidate; no repository identity or reference labels used.

**All required positive patterns:**

```regex
(?m)^\s*(?:[\w./-]*/)?(?:prepare[-_][\w.-]*|preprocess[\w.-]*|tokenize[\w.-]*|cv-prepdata\.sh)\s+
(?:\$[\w{]|\s-\w|\b(?:data|corpus|input|train)\b)
```

**scope:** `portable-statement`.

### PRO_DOC_DATA_SUBSET_V53

Construct a subset of identified research inputs; not filtering a software log or a path name.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Explicit research-input subsetting is preprocessing evidence.

**All required positive patterns:**

```regex
\b(?:subset|subsample|subsetting|subsampling|tail)\b
\b(?:dataset|data|triples|corpus|observations|samples)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|package|library|run|python|Rscript|MATLAB|notebook|paper|publication|cite|citation|download)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not supported|not implemented|does not|do not|cannot|doesn.t|don.t|never|future work|planned|todo|hypothetical|example only)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:unit|integration|software) tests?\b
```

**unit_policy:** `documented-workflow-v5`.

### PRO_DOC_DOCUMENTED_INPUT_PREPARATION_FINAL

documented input preparation

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive documentation evidence reviewed across the development log; no repository identity or labels enter matching.

**All required positive patterns:**

```regex
\b(?:preprocess\w*|prepar\w*|transform\w*|convert\w*|filter\w*|outlier rejection|outlier analysis)\b
\b(?:input data|datasets?|raw data|training data|triples|sequences|images|observations|observer\w*)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|code|repository|package|software|toolbox|model|method|algorithm|experiment\w*|results?|parser)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not implemented|future work|planned|todo|hypothetical)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|external|third[- ]party)\s+(?:repository|software|package|tool)\b
```

**unit_policy:** `documented-workflow-v5`.

## Method

### MET_CODE_ACTIVITY_V1

Implement a scientific model, algorithm, or analytical technique.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** Scientific method implementation, excluding packaging, entry points and software tests. Definition awaits human codebook.

**All required positive patterns:**

```regex
^\s*def\s+(?:fit_statistical_model|implement_proposed_algorithm|estimate_scientific_model)\s*\(
\b(?:minimize|optimizer\.step|np\.linalg\.solve)\s*\(
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

### MET_DOC_EXPLICIT_V2

Implement a scientific model, algorithm, or analytical technique.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Scientific method implementation, excluding packaging, entry points and software tests. Definition awaits human codebook. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(implement(?:s|ed|ing)?|estimat(?:e|es|ed|ing)|fit(?:s|ted|ting)?)\b
\b(scientific model|proposed algorithm|statistical model|research method)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### MET_DOC_CONTEXTUAL_V2

Implement a scientific model, algorithm, or analytical technique.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Scientific method implementation, excluding packaging, entry points and software tests. Definition awaits human codebook. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:implement(?:s|ed|ing)?|provid(?:e|es|ed|ing)|estimat(?:e|es|ed|ing)|fit(?:s|ted|ting)|offer(?:s|ed|ing)?)\b
\b(?:scientific models?|statistical models?|proposed algorithms?|research methods?|analytical methods?|statistical analysis|principal component analysis|linear regression|bayesian inference|finite element methods?)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### MET_DOC_WORKFLOW_V2

Implement a scientific model, algorithm, or analytical technique.

**Source:** documentation. **Detector/layer:** workflow. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Scientific method implementation, excluding packaging, entry points and software tests. Definition awaits human codebook. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:implement(?:s|ed|ing)?|provid(?:e|es|ed|ing)|estimat(?:e|es|ed|ing)|fit(?:s|ted|ting)|offer(?:s|ed|ing)?)\b
\b(?:scientific models?|statistical models?|proposed algorithms?|research methods?|analytical methods?|statistical analysis|principal component analysis|linear regression|bayesian inference|finite element methods?)\b
```

**Local scope/header pattern:**

```regex
\b(?:run|use|execute)\s+(?:this|the|our)\s+(?:command|workflow|tutorial)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### MET_DOC_RESEARCH_V3

Repository-scoped research activity and object using common disciplinary wording.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object conjunction; supports instructional and passive repository descriptions without requiring the literal word research.

**All required positive patterns:**

```regex
(?<![-_./])\b(?:implement(?:s|ed|ing|ation)?|propos(?:e|es|ed|ing)|provid(?:e|es|ed|ing)|features|(?:is|includes|contains)\s+(?:an?\s+)?(?:statistical\s+)?(?:algorithm|model|estimator))\b
(?<![-_./])\b(?:algorithm|model|method|estimator|inference|optimization|sampling|neural|regression|classifier)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|run|python|available|download|paper|publication|cite|citation)\b|\bis\s+an?\s+(?:statistical\s+)?(?:algorithm|model|estimator)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### MET_CODE_RESEARCH_V3

Research-specific implementation operation with a contextual identifier.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive operation and contextual identifier in the same Python function; comments and strings masked. No repository identity or human label is a feature.

**All required positive patterns:**

```regex
^\s*def\s+(?:fit|predict|infer|optimize|sample|estimate)(?:_\w+)?\s*\(
\b(?:dot|matmul|solve|gradient|backward|minimize|linalg|logpdf)\b
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

### MET_CODE_MULTILANG_V3

Conjunctive research operation and contextual identifier in R, Julia, MATLAB or shell.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 6 lines (subject to detector unit policy).

**Why this rule exists:** Lexically masked comments and strings cannot provide either condition; matched executable statements are evidence, without asserting scientific validity. Function/call context for method; research repetitions for experimentation.

**All required positive patterns:**

```regex
\bfunction\b
\b(?:optim|optimize|solve|lm|glm|eigen|svd)\s*\(
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

**scope:** `statement`.

**extensions:** `['.r', '.jl', '.m', '.sh']`.

### MET_DOC_EXTENDED_V4

Candidate extended wording for method.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object wording from the conceptual stage definition; no benchmark identity, labels or unique repository phrase used. Synthetic tests only; empirical benefit unverified.

**All required positive patterns:**

```regex
\b(?:train(?:s|ed|ing)?|fit(?:s|ted|ting)?|estimat(?:e|es|ed|ing)|infer(?:s|red|ring)?)\b
\b(?:neural networks?|statistical models?|regression models?|classifiers?|probabilistic models?|model parameters|posterior distributions?)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this\s+(?:tool|package|software|repository|code|library|implementation)|the\s+(?:tool|package|software|repository|code|library))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### MET_CODE_BRACE_MODEL_CALL_V51

Invoke scientific model computation with research-input variables.

**Source:** code. **Detector/layer:** brace-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Invoke scientific model computation with research-input variables. Comments/literals are masked and all matching conditions must occur inside one executable brace block, excluding declarations and software-test paths. Lexical candidate evidence, not semantic proof.

**All required positive patterns:**

```regex
\b(?:fit|train|predict|infer|optimize|solve)\s*\(
\b(?:model|estimator|classifier|solver)\b
\b(?:data|dataset|features|samples|observations|targets|labels)\b
```

**scope:** `lexical-block`.

**extensions:** `['.c', '.cpp', '.cc', '.h', '.hpp', '.java', '.js', '.ts', '.go', '.rs', '.scala']`.

### MET_CODE_BRACE_NAMED_COMPUTATION_V51

Numerical operations within an explicitly named scientific computation routine.

**Source:** code. **Detector/layer:** brace-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Numerical operations within an explicitly named scientific computation routine. Comments/literals are masked and all matching conditions must occur inside one executable brace block, excluding declarations and software-test paths. Lexical candidate evidence, not semantic proof.

**All required positive patterns:**

```regex
(?:\b[A-Za-z_]\w*(?:\[[^\]\n]+\])?\s*(?:\+=|-=|\*=|/=|=)|\b(?:sqrt|pow|exp|log|dot|matmul|solve|min|max)\s*\()
(?:\b[A-Za-z_]\w*(?:\[[^\]\n]+\])?\s*[*/+-]\s*[A-Za-z_0-9]|\b(?:sqrt|pow|exp|log|dot|matmul|solve)\s*\()
```

**Local scope/header pattern:**

```regex
\b\w*(?:cosine|jaccard|similarity|likelihood|posterior|entropy|gradient|eigen|svd|estimate|infer|optim|regress|classifier|computeSimScore)\w*\s*\(
```

**scope:** `lexical-block`.

**extensions:** `['.c', '.cpp', '.cc', '.h', '.hpp', '.java', '.js', '.ts', '.go', '.rs', '.scala']`.

### MET_CODE_PORTABLE_MODEL_V51

Invoke scientific model computation on research inputs.

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Invoke scientific model computation on research inputs. All conditions must occur within one lexical statement. Comments and literals are masked. This is a language-neutral candidate heuristic, not a semantic proof.

**All required positive patterns:**

```regex
\b(?:fit|train|predict|infer|optimize|optim|solve|lm|glm)\b\s*(?:\(|[A-Za-z_$])
\b(?:model|estimator|classifier|solver|regression)\b
\b(?:data|dataset|features|samples|observations|targets|labels)\b
```

**scope:** `portable-statement`.

### MET_DOC_IMPLEMENTED_METHOD_V52

Explicit implementation or derivation of a named research method, not merely code accompanying a paper or training an existing model.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 6 lines (subject to detector unit policy).

**Why this rule exists:** Explicit implementation or derivation of a named research method, not merely code accompanying a paper or training an existing model. Development evidence candidate; no repository identity or reference labels used.

**All required positive patterns:**

```regex
\b(?:implement(?:s|ed|ation|ing)?|introduc(?:e|es|ed|ing)|propos(?:e|es|ed|ing)|deriv(?:e|es|ed|ation))\b
\b(?:algorithm|method|estimator|architecture|optimization procedure|inference procedure)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|code|implementation|algorithm|method|pipeline|reranker)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not implemented|future work|planned|todo|related work)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### MET_DOC_COMPUTATIONAL_STEPS_V52

Documented implementation with an explicit multistep computational mechanism, beyond merely training or citing a model.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** Documented implementation with an explicit multistep computational mechanism, beyond merely training or citing a model. Development evidence candidate; no repository identity or reference labels used.

**All required positive patterns:**

```regex
\b(?:code|implementation|algorithm|method|pipeline|reranker|classifier)\b
\b(?:consists? of|comprises?|composed of)\b[^.!?]{0,100}\b(?:steps|stages|components)\b
\b(?:feature extraction|supervised learning|inference|optimization|sampling|ranking)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|code|implementation|algorithm|method|pipeline|reranker)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not implemented|future work|planned|todo|related work)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### MET_CODE_NUMERIC_UPDATE_V52

numeric update

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** numeric update Development evidence candidate; no repository identity or reference labels used.

**All required positive patterns:**

```regex
\b\w+\s*=\s*\w+\s*-\s*\w+\s*\*\s*\w*(?:grad|gradient)\w*\b
(?:=|\()
```

**scope:** `portable-statement`.

### MET_CODE_OPTIMIZER_CALL_V52

optimizer call

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** optimizer call Development evidence candidate; no repository identity or reference labels used.

**All required positive patterns:**

```regex
\b(?:grad_descent|gradient_descent|fminunc|fmincon|fminsearch|least_squares|curve_fit)\s*\(
\b(?:W|X|Y|data|features|params|parameters|weights|theta)\b
```

**scope:** `portable-statement`.

### MET_DOC_EXPERIMENTAL_DESIGN_V53

Repository implementation of an explicitly named experimental-design method.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** Named statistical design plus local implementation evidence; merely mentioning an experiment is insufficient.

**All required positive patterns:**

```regex
\b(?:statistical design of experiments|factorial design|fractional factorial|response surface methodology)\b
\b(?:code|package|implementation|implement\w*|developed)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|code|implementation|algorithm|method|pipeline|reranker)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:study|research|experiment\w*)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not implemented|future work|planned|todo|related work)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

**unit_policy:** `documented-workflow-v5`.

### MET_DOC_AGENT_MECHANISM_V53

Documented agent interaction/decision mechanism in a simulation implementation.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** Agent mechanism with its simulated environment, not merely a generic model or paper title.

**All required positive patterns:**

```regex
\b(?:agents?|multiagent|multi-agent)\b
\b(?:trade|interact|decid\w*|behaviou?r|actions?)\b
\b(?:market|environment|simulation|simulat\w*)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|code|implementation|algorithm|method|pipeline|reranker)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:API|code|package|simulation|model)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not implemented|future work|planned|todo|related work)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

**unit_policy:** `documented-workflow-v5`.

### MET_CODE_PHYSICAL_EQUATION_V53

Assign an identified physical/statistical quantity using multiplicative arithmetic, in source containing a nonlinear numerical operation. This is a lexical equation candidate; the file-context condition is not data-flow proof.

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Assign an identified physical/statistical quantity using multiplicative arithmetic, in source containing a nonlinear numerical operation. This is a lexical equation candidate; the file-context condition is not data-flow proof. Comments and string contents are masked. No repository identity or reference label is used.

**All required positive patterns:**

```regex
\b(?:energy|density|pressure|temperature|radiation|concentration|resistance|conductance|flux|velocity|acceleration|potential|entropy|likelihood)\w*\s*(?:<-|=(?!=))
(?:<-|=(?!=))\s*[^;\n]*\b[A-Za-z_]\w*\s*[*/^]\s*[A-Za-z_(]
```

**All required file-context patterns:**

```regex
\b(?:exp|sqrt|log|log10|sin|cos|pow)\s*\(
```

**scope:** `portable-statement`.

### MET_CODE_AGENT_DECISION_V53

Compute an agent decision and dispatch its action to a simulated environment in one executable brace block.

**Source:** code. **Detector/layer:** brace-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Compute an agent decision and dispatch its action to a simulated environment in one executable brace block. Comments and string contents are masked. No repository identity or reference label is used.

**All required positive patterns:**

```regex
\b\w+\s*=\s*agent\w*\s*\.\s*(?:decide|act|chooseAction)\s*\(
\b(?:market|environment|world)\w*\s*\.\s*(?:send|applyAction|step)\s*\([^;\n]*\bagent\w*\b
```

**scope:** `lexical-block`.

**extensions:** `['.java', '.js', '.ts', '.cpp', '.cc']`.

### MET_DOC_IMPLEMENTATION_OBJECT_FINAL

implementation object

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive documentation evidence reviewed across the development log; no repository identity or labels enter matching.

**All required positive patterns:**

```regex
\b(?:implementation\s+of|implements?|implemented|contains?\s+(?:two\s+versions?\s+of\s+)?(?:the\s+)?(?:models?|algorithms?)|models?\s+simulating)\b
\b(?:parser|neural|tensor|bayesian|statistical|mathematical|mechanistic|differential|regression|optimization|inference|sampling|classification|discovery|reconstruction)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|code|repository|package|software|toolbox|model|method|algorithm|experiment\w*|results?|parser)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:study|research|experiment\w*)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not implemented|future work|planned|todo|hypothetical)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|external|third[- ]party)\s+(?:repository|software|package|tool)\b
```

**unit_policy:** `documented-workflow-v5`.

### MET_DOC_NUMERICAL_TECHNIQUE_FINAL

numerical technique

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive documentation evidence reviewed across the development log; no repository identity or labels enter matching.

**All required positive patterns:**

```regex
\b(?:compute\w*|calculat\w*|estimat\w*|implement\w*|learn\w*|discover\w*)\b
\b(?:compatibility probability|matrix functions?|gaussian process|grammar[- ]guided|symbolic regression|differential equations?|posterior|likelihood|dependency pars(?:er|ing)|neural networks?|statistical models?)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|code|repository|package|software|toolbox|model|method|algorithm|experiment\w*|results?|parser)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:study|research|experiment\w*)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not implemented|future work|planned|todo|hypothetical)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|external|third[- ]party)\s+(?:repository|software|package|tool)\b
```

**unit_policy:** `documented-workflow-v5`.

### MET_CODE_SCIENTIFIC_NUMERICAL_CALL_FINAL

scientific numerical call

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Executable scientific API evidence with argument/context requirements; comments/literals masked. No general semantic guarantee.

**All required positive patterns:**

```regex
\b(?:np\.linalg\.(?:solve|inv|eigh|eig|svd)|scipy\.optimize\.(?:minimize|least_squares)|trainNetwork|fitnet|patternnet|feedforwardnet|fminsearch)\s*\(
\(\s*[A-Za-z_]\w*
```

**scope:** `portable-statement`.

### MET_CODE_ODE_SOLVER_FINAL

ode solver

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Executable scientific API evidence with argument/context requirements; comments/literals masked. No general semantic guarantee.

**All required positive patterns:**

```regex
\b(?:ode15s|ode45|ode23s?|ode113|odeint|solve_ivp|NDSolve|NDSolveValue|DSolve)\s*[\[(]
(?:@\w+|\b(?:model|rhs|fun|func|system|deriv\w*|t|tspan|y0|initial\w*)\b)
```

**scope:** `portable-statement`.

### MET_CODE_SCIENTIFIC_FIT_CALL_FINAL

scientific fit call

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Executable scientific API evidence with argument/context requirements; comments/literals masked. No general semantic guarantee.

**All required positive patterns:**

```regex
\b\w+\s*\.\s*(?:fit|predict|forward|backward)\s*\(
\(\s*[A-Za-z_]\w*
```

**All required file-context patterns:**

```regex
\b(?:torch|tensorflow|keras|sklearn|scipy|numpy|Flux|GaussianProcesses)\b
```

**scope:** `portable-statement`.

### MET_CODE_STATISTICAL_ESTIMATOR_FINAL

statistical estimator

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Executable scientific API evidence with argument/context requirements; comments/literals masked. No general semantic guarantee.

**All required positive patterns:**

```regex
\b(?:lm|glm|optim|optimize|svd|eigen|nnls|lsqnonneg|fminunc|fmincon|fitglm|fitlm|FindMinimum|FindMaximum)\s*[\[(]
[\[(]\s*[A-Za-z_@]\w*
```

**scope:** `portable-statement`.

## Experimentation

### EXP_CODE_ACTIVITY_V1

Execute controlled research trials or parameter studies.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** An explicit research trial activity together with iteration over controlled conditions; run.py alone is insufficient.

**All required positive patterns:**

```regex
^\s*def\s+(?:run_controlled_experiments|run_parameter_sweep|conduct_research_trials)\s*\(
^\s*for\s+\w+\s+in\s+(?:parameter_grid|trial_seeds|experimental_conditions)\s*:
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

### EXP_DOC_EXPLICIT_V2

Execute controlled research trials or parameter studies.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** An explicit research trial activity together with iteration over controlled conditions; run.py alone is insufficient. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(run(?:s|ning)?|execut(?:e|es|ed|ing)|conduct(?:s|ed|ing)?)\b
\b(controlled experiments|parameter sweep|research trials|experimental trials)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### EXP_DOC_CONTEXTUAL_V2

Execute controlled research trials or parameter studies.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** An explicit research trial activity together with iteration over controlled conditions; run.py alone is insufficient. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:run(?:s|ning)?|execut(?:e|es|ed|ing)|conduct(?:s|ed|ing)?|perform(?:s|ed|ing)?)\b
\b(?:controlled experiments?|research trials?|experimental trials?|parameter sweeps?|scientific simulations?|experimental workflows?)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### EXP_DOC_WORKFLOW_V2

Execute controlled research trials or parameter studies.

**Source:** documentation. **Detector/layer:** workflow. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** An explicit research trial activity together with iteration over controlled conditions; run.py alone is insufficient. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:run(?:s|ning)?|execut(?:e|es|ed|ing)|conduct(?:s|ed|ing)?|perform(?:s|ed|ing)?)\b
\b(?:controlled experiments?|research trials?|experimental trials?|parameter sweeps?|scientific simulations?|experimental workflows?)\b
```

**Local scope/header pattern:**

```regex
\b(?:run|use|execute)\s+(?:this|the|our)\s+(?:command|workflow|tutorial)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### EXP_DOC_RESEARCH_V3

Repository-scoped research activity and object using common disciplinary wording.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object conjunction; supports instructional and passive repository descriptions without requiring the literal word research.

**All required positive patterns:**

```regex
(?<![-_./])\b(?:run(?:s|ning)?|reproduc(?:e|es|ed|ing)|perform(?:s|ed|ing)?|conduct(?:s|ed|ing)?|launch(?:es|ed|ing)?)\b
(?<![-_./])\b(?:experiments?|simulations?|parameter sweeps?|hyperparameter|training)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|run|python|available|download|paper|publication|cite|citation)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### EXP_CODE_RESEARCH_V3

Research-specific implementation operation with a contextual identifier.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 3 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive operation and contextual identifier in the same Python function; comments and strings masked. No repository identity or human label is a feature.

**All required positive patterns:**

```regex
\b(?:GridSearchCV|RandomizedSearchCV|ParameterGrid)\s*\(
\b(?:fit|for|estimator|param_grid|param_distributions)\b
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

**scope:** `statement`.

### EXP_CODE_MULTILANG_V3

Conjunctive research operation and contextual identifier in R, Julia, MATLAB or shell.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 6 lines (subject to detector unit policy).

**Why this rule exists:** Lexically masked comments and strings cannot provide either condition; matched executable statements are evidence, without asserting scientific validity. Function/call context for method; research repetitions for experimentation.

**All required positive patterns:**

```regex
\b(?:for|parfor|expand\.grid|Iterators\.product)\b
\b(?:n_trials|num_trials|n_repeats|seeds|hyperparameters|param_grid|experiments)\b
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

**scope:** `statement`.

**extensions:** `['.r', '.jl', '.m', '.sh']`.

### EXP_DOC_EXTENDED_V4

Candidate extended wording for experimentation.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object wording from the conceptual stage definition; no benchmark identity, labels or unique repository phrase used. Synthetic tests only; empirical benefit unverified.

**All required positive patterns:**

```regex
\b(?:run(?:s|ning)?|perform(?:s|ed|ing)?|conduct(?:s|ed|ing)?|reproduc(?:e|es|ed|ing))\b
\b(?:ablation stud(?:y|ies)|sensitivity analys(?:is|es)|cross[- ]validation experiments|experimental trials|randomized trials)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this\s+(?:tool|package|software|repository|code|library|implementation)|the\s+(?:tool|package|software|repository|code|library))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### EXP_DOC_WORKFLOW_V5_1

Development candidate: documentation-described experimentation activities and artifacts.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General heading/paragraph/workflow evidence motivated by development-only error review; no repository identity or label enters matching. Stage proxies need codebook review; not an independent evaluation.

**All required positive patterns:**

```regex
\b(?:experiments?|simulations?|trials?|parameter sweeps?|ablation|reproduc\w*|replicat\w*)\b
\b(?:code|scripts?|implementation|run|runs|running|ran|perform(?:s|ed|ing)?|conduct(?:s|ed|ing)?|reproduc\w*|replicat\w*|python|bash|Rscript|MATLAB|notebooks?|simulat(?:e|es|ed|ing)|configurations?)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|package|library|run|python|Rscript|MATLAB|notebook|paper|publication|cite|citation|download)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not supported|not implemented|does not|do not|cannot|doesn.t|don.t|never|future work|planned|todo|hypothetical|example only)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:unit|integration|software) tests?\b
```

**unit_policy:** `documented-workflow-v5`.

### EXP_DOC_WORKFLOW_V5_2

Development candidate: documentation-described experimentation activities and artifacts.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General heading/paragraph/workflow evidence motivated by development-only error review; no repository identity or label enters matching. Stage proxies need codebook review; not an independent evaluation.

**All required positive patterns:**

```regex
\b(?:reproduc\w*|replicat\w*|generat\w*)\b
\b(?:results|figures?)\b[^.!?]{0,160}\b(?:paper|report|study|experiment\w*)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|package|library|run|python|Rscript|MATLAB|notebook|paper|publication|cite|citation|download)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not supported|not implemented|does not|do not|cannot|doesn.t|don.t|never|future work|planned|todo|hypothetical|example only)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:unit|integration|software) tests?\b
```

**unit_policy:** `documented-workflow-v5`.

### EXP_CODE_BRACE_TRIALS_V51

Controlled/repeated research runs with a scientific call and recorded outcomes.

**Source:** code. **Detector/layer:** brace-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Controlled/repeated research runs with a scientific call and recorded outcomes. Comments/literals are masked and all matching conditions must occur inside one executable brace block, excluding declarations and software-test paths. Lexical candidate evidence, not semantic proof.

**All required positive patterns:**

```regex
\b(?:for|while)\s*\(
\b(?:n_trials|num_trials|trialSeeds|seeds|experimentalConditions|parameterGrid|param_grid|nRepeats|trial|experiment)\b
\b(?:runTrial|run_trial|runExperiment|run_experiment|fit|train|evaluate)\s*\(
\b(?:results|scores|observations|outcomes)\b
```

**scope:** `lexical-block`.

**extensions:** `['.c', '.cpp', '.cc', '.h', '.hpp', '.java', '.js', '.ts', '.go', '.rs', '.scala']`.

### EXP_CODE_PORTABLE_TRIALS_V51

Apply a research runner across explicit conditions and retain results.

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Apply a research runner across explicit conditions and retain results. All conditions must occur within one lexical statement. Comments and literals are masked. This is a language-neutral candidate heuristic, not a semantic proof.

**All required positive patterns:**

```regex
\b(?:run[_-]?trial|run[_-]?experiment|lapply|parallelMap|map|sweep)\b\s*(?:\(|[A-Za-z_$])
\b(?:trialSeeds|trial_seeds|seeds|experimentalConditions|parameterGrid|param_grid|trial_conditions)\b
\b(?:results|scores|outcomes)\b
```

**scope:** `portable-statement`.

### EXP_CODE_REPEATED_SCIENTIFIC_CALL_V52

Scientific runner call in a file with an executable repeat/parameter loop; file-level context, not proven data flow.

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** Scientific runner call in a file with an executable repeat/parameter loop; file-level context, not proven data flow. Development evidence candidate; no repository identity or reference labels used.

**All required positive patterns:**

```regex
\b(?:grad_descent|gradient_descent|run_experiment|run_trial|cross_val_score|cross_validate)\s*\(
(?:=|\()
```

**All required file-context patterns:**

```regex
\bfor\b[^\n]*(?:reps|trials|seeds|folds|length\s*\(|range\s*\()
```

**scope:** `portable-statement`.

### EXP_CODE_FACTORIAL_RUNS_V53

Execute an experimental function across an explicit design table.

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Scientific runner over design rows, not a generic collection map.

**All required positive patterns:**

```regex
\b(?:apply|lapply|sapply|map)\s*\(
\bdesign\b
\b(?:experiment|run_experiment|run_trial)\b
```

**scope:** `portable-statement`.

### EXP_CODE_AGENT_TIME_STEPS_V53

Execute agent updates inside a bounded simulated-time loop and explicitly advance simulated time; not a generic software loop.

**Source:** code. **Detector/layer:** brace-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Execute agent updates inside a bounded simulated-time loop and explicitly advance simulated time; not a generic software loop. Comments and string contents are masked. No repository identity or reference label is used.

**All required positive patterns:**

```regex
\b(?:while|for)\s*\([^\n]*(?:currentTick|timeStep|timestep|simulationTime)\s*\(
\b(?:queryAllAgents|updateAgents|stepAgents|advanceAgents)\s*\(
\.\s*(?:nextTick|advanceTime|nextTimeStep)\s*\(
```

**scope:** `lexical-block`.

**extensions:** `['.java', '.js', '.ts', '.cpp', '.cc']`.

### EXP_DOC_SCIENTIFIC_TRAIN_TEST_COMMAND_FINAL

scientific train test command

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive documentation evidence reviewed across the development log; no repository identity or labels enter matching.

**All required positive patterns:**

```regex
(?m)^\s*(?:(?:python[23]?|bash|sh|Rscript|julia|matlab)\s+|\./)[^\n]*(?:train|experiment|simulation|pipeline|run)[\w./-]*
\b(?:train|training|validation|experiments?|simulations?|parser|model|results?)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|code|repository|package|software|toolbox|model|method|algorithm|experiment\w*|results?|parser)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not implemented|future work|planned|todo|hypothetical)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|external|third[- ]party)\s+(?:repository|software|package|tool)\b
```

**unit_policy:** `documented-workflow-v5`.

### EXP_CODE_ODE_SIMULATION_RUN_FINAL

ode simulation run

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Executable scientific API evidence with argument/context requirements; comments/literals masked. No general semantic guarantee.

**All required positive patterns:**

```regex
\b(?:ode15s|ode45|ode23s?|ode113|odeint|solve_ivp)\s*\(
\b(?:t|tspan|time|times|t_eval)\b
\b(?:y0|initial\w*|state0)\b
```

**scope:** `portable-statement`.

## Evaluation

### EVA_CODE_ACTIVITY_V1

Assess scientific performance against reference outcomes or baselines.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** Explicit scientific assessment with reference-labelled metric computation; unit tests and isolated metrics are excluded.

**All required positive patterns:**

```regex
^\s*def\s+(?:evaluate_research_predictions|compare_scientific_baselines|evaluate_ablation_study)\s*\(
\b(?:f1_score|mean_squared_error|accuracy_score)\s*\(\s*(?:ground_truth|reference_labels)\s*,
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

### EVA_DOC_EXPLICIT_V2

Assess scientific performance against reference outcomes or baselines.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Explicit scientific assessment with reference-labelled metric computation; unit tests and isolated metrics are excluded. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(evaluat(?:e|es|ed|ing)|compar(?:e|es|ed|ing)|assess(?:es|ed|ing)?)\b
\b(?:predictive performance against (?:a )?baseline|scientific accuracy against ground truth|ablation study|research benchmark against reference)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### EVA_DOC_CONTEXTUAL_V2

Assess scientific performance against reference outcomes or baselines.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Explicit scientific assessment with reference-labelled metric computation; unit tests and isolated metrics are excluded. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:evaluat(?:e|es|ed|ing)|assess(?:es|ed|ing)?|compar(?:e|es|ed|ing)|measur(?:e|es|ed|ing))\b
\b(?:predictive performance|research outputs?|scientific accuracy|research benchmarks?|ablation stud(?:y|ies)|scientific models?)\b[\s\S]{0,160}\b(?:baselines?|ground truth|reference data|reference labels|scientific metrics|statistical tests|f1|accuracy|precision|recall)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### EVA_DOC_WORKFLOW_V2

Assess scientific performance against reference outcomes or baselines.

**Source:** documentation. **Detector/layer:** workflow. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Explicit scientific assessment with reference-labelled metric computation; unit tests and isolated metrics are excluded. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:evaluat(?:e|es|ed|ing)|assess(?:es|ed|ing)?|compar(?:e|es|ed|ing)|measur(?:e|es|ed|ing))\b
\b(?:predictive performance|research outputs?|scientific accuracy|research benchmarks?|ablation stud(?:y|ies)|scientific models?)\b[\s\S]{0,160}\b(?:baselines?|ground truth|reference data|reference labels|scientific metrics|statistical tests|f1|accuracy|precision|recall)\b
```

**Local scope/header pattern:**

```regex
\b(?:run|use|execute)\s+(?:this|the|our)\s+(?:command|workflow|tutorial)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### EVA_DOC_RESEARCH_V3

Repository-scoped research activity and object using common disciplinary wording.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object conjunction; supports instructional and passive repository descriptions without requiring the literal word research.

**All required positive patterns:**

```regex
(?<![-_./])\b(?:evaluat(?:e|es|ed|ing|ion)|benchmark(?:s|ed|ing)?|compar(?:e|es|ed|ing)|measur(?:e|es|ed|ing))\b
(?<![-_./])\b(?:accuracy|precision|recall|f1|performance|baselines?|predictions?|test set|held.out|metrics|error rates?)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|run|python|available|download|paper|publication|cite|citation)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### EVA_CODE_RESEARCH_V3

Research-specific implementation operation with a contextual identifier.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 3 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive operation and contextual identifier in the same Python function; comments and strings masked. No repository identity or human label is a feature.

**All required positive patterns:**

```regex
\b(?:accuracy_score|precision_score|recall_score|f1_score|mean_squared_error|roc_auc_score)\s*\(
\b(?:y_true|y_test|y_pred|predictions|labels|targets|ground_truth)\b
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

**scope:** `statement`.

### EVA_CODE_MULTILANG_V3

Conjunctive research operation and contextual identifier in R, Julia, MATLAB or shell.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 6 lines (subject to detector unit policy).

**Why this rule exists:** Lexically masked comments and strings cannot provide either condition; matched executable statements are evidence, without asserting scientific validity. Function/call context for method; research repetitions for experimentation.

**All required positive patterns:**

```regex
\b(?:accuracy|precision|recall|f1|rmse|auc)\s*(?:=|<-|\()
\b(?:predictions?|predicted|y_true|y_test|labels|ground_truth)\b
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

**scope:** `statement`.

**extensions:** `['.r', '.jl', '.m', '.sh']`.

### EVA_DOC_EXTENDED_V4

Candidate extended wording for evaluation.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object wording from the conceptual stage definition; no benchmark identity, labels or unique repository phrase used. Synthetic tests only; empirical benefit unverified.

**All required positive patterns:**

```regex
\b(?:comput(?:e|es|ed|ing)|calculat(?:e|es|ed|ing)|assess(?:es|ed|ing)?)\b
\b(?:prediction error|classification accuracy|f1 scores?|precision and recall|root mean square(?:d)? error|area under the (?:roc )?curve)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this\s+(?:tool|package|software|repository|code|library|implementation)|the\s+(?:tool|package|software|repository|code|library))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### EVA_DOC_WORKFLOW_V5_1

Development candidate: documentation-described evaluation activities and artifacts.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General heading/paragraph/workflow evidence motivated by development-only error review; no repository identity or label enters matching. Stage proxies need codebook review; not an independent evaluation.

**All required positive patterns:**

```regex
\b(?:evaluat\w*|benchmark\w*|compar\w*|assess\w*|measur\w*|analys\w*|calculat\w*|comput\w*)\b
\b(?:accuracy|precision|recall|f1|scores?|performance|baselines?|prediction error|errors?|ratios?|confidence intervals?|significance|effect sizes?|test data|test sets?|held[- ]out|metrics|memory|timing|bootstrap\w*)\b
\b(?:accuracy|precision|recall|f1|metrics?|baselines?|confidence intervals?|significance|effect sizes?|held[- ]out|test sets?|test data|timing|runtime|elapsed|memory usage|prediction error)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|package|library|run|python|Rscript|MATLAB|notebook|paper|publication|cite|citation|download)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not supported|not implemented|does not|do not|cannot|doesn.t|don.t|never|future work|planned|todo|hypothetical|example only)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:unit|integration|software) tests?\b
```

**unit_policy:** `documented-workflow-v5`.

### EVA_DOC_WORKFLOW_V5_2

Development candidate: documentation-described evaluation activities and artifacts.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General heading/paragraph/workflow evidence motivated by development-only error review; no repository identity or label enters matching. Stage proxies need codebook review; not an independent evaluation.

**All required positive patterns:**

```regex
\b(?:evaluation|benchmark|validation|cross[- ]validation)\b
\b(?:code|scripts?|results|python|Rscript|MATLAB|notebooks?|model|data|experiments?|run\w*|strateg\w*)\b
\b(?:accuracy|precision|recall|f1|metrics?|baselines?|confidence intervals?|significance|held[- ]out|cross[- ]validation|timing|runtime|prediction error)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|package|library|run|python|Rscript|MATLAB|notebook|paper|publication|cite|citation|download)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not supported|not implemented|does not|do not|cannot|doesn.t|don.t|never|future work|planned|todo|hypothetical|example only)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:unit|integration|software) tests?\b
```

**unit_policy:** `documented-workflow-v5`.

### EVA_CODE_BRACE_METRIC_CALL_V51

Scientific metric calls connected to reference/predicted research outcomes.

**Source:** code. **Detector/layer:** brace-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Scientific metric calls connected to reference/predicted research outcomes. Comments/literals are masked and all matching conditions must occur inside one executable brace block, excluding declarations and software-test paths. Lexical candidate evidence, not semantic proof.

**All required positive patterns:**

```regex
\b(?:f1Score|f1_score|precisionScore|recallScore|accuracyScore|meanSquaredError|rmse|rocAuc|computeAccuracy)\s*\(
\b(?:y_true|referenceLabels|reference_labels|ground_truth|gold|labels|predictions|predicted)\b
```

**scope:** `lexical-block`.

**extensions:** `['.c', '.cpp', '.cc', '.h', '.hpp', '.java', '.js', '.ts', '.go', '.rs', '.scala']`.

### EVA_CODE_BRACE_METRIC_ARITHMETIC_V51

Explicit metric arithmetic connected to reference/prediction counts.

**Source:** code. **Detector/layer:** brace-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Explicit metric arithmetic connected to reference/prediction counts. Comments/literals are masked and all matching conditions must occur inside one executable brace block, excluding declarations and software-test paths. Lexical candidate evidence, not semantic proof.

**All required positive patterns:**

```regex
\b(?:precision|recall|f1|fscore|accuracy|rmse|mse)\s*=
(?:/|\b(?:sqrt|pow)\s*\()
\b(?:truePositives|falsePositives|tp|fp|fn|correct|predictions|labels|gold|predicted|n_correct)\b
```

**scope:** `lexical-block`.

**extensions:** `['.c', '.cpp', '.cc', '.h', '.hpp', '.java', '.js', '.ts', '.go', '.rs', '.scala']`.

### EVA_CODE_PORTABLE_METRIC_V51

Compute a research metric against identified outcomes/reference labels.

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Compute a research metric against identified outcomes/reference labels. All conditions must occur within one lexical statement. Comments and literals are masked. This is a language-neutral candidate heuristic, not a semantic proof.

**All required positive patterns:**

```regex
\b(?:f1[_-]?score|precision[_-]?score|recall[_-]?score|accuracy[_-]?score|mean[_-]?squared[_-]?error|rmse|roc[_-]?auc|compute[_-]?accuracy)\b\s*(?:\(|[A-Za-z_$])
\b(?:y_true|y_test|referenceLabels|reference_labels|ground_truth|gold|labels|predictions|predicted)\b
```

**scope:** `portable-statement`.

### EVA_CODE_PORTABLE_ARITHMETIC_V51

Compute explicit metric arithmetic using prediction/reference counts.

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Compute explicit metric arithmetic using prediction/reference counts. All conditions must occur within one lexical statement. Comments and literals are masked. This is a language-neutral candidate heuristic, not a semantic proof.

**All required positive patterns:**

```regex
\b(?:precision|recall|f1|fscore|accuracy|rmse|mse)\s*(?:=|<-)
(?:/|\b(?:sqrt|pow)\s*\()
\b(?:truePositives|falsePositives|tp|fp|fn|correct|predictions|labels|gold|predicted|n_correct)\b
```

**scope:** `portable-statement`.

### EVA_CODE_SHELL_EVALUATE_V52

shell evaluate

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** shell evaluate Development evidence candidate; no repository identity or reference labels used.

**All required positive patterns:**

```regex
(?m)^\s*(?:(?:python[23]?|perl|Rscript)\s+)?(?:[\w./-]*/)?(?:evaluate|eval|score)(?:[_.-][\w.-]+|\.py|\.pl)?\s+
(?:\$|>|\b(?:gold|reference|predict\w*|test)\b)
```

**scope:** `portable-statement`.

### EVA_CODE_HELDOUT_ERROR_V52

heldout error

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** heldout error Development evidence candidate; no repository identity or reference labels used.

**All required positive patterns:**

```regex
\b\w+\s*=\s*[^;\n]*\b\w*(?:test|heldout|gold|reference)\w*\b[^;\n]*-\s*\w+
(?:=|\()
```

**scope:** `portable-statement`.

### EVA_CODE_METRIC_NAMES_V52

metric names

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** metric names Development evidence candidate; no repository identity or reference labels used.

**All required positive patterns:**

```regex
\b(?:accuracy_score|precision_score|recall_score|f1_score|mean_squared_error|roc_auc_score|classification_report)\s*\(
\b\w*(?:true|gold|test|reference|labels|target)\w*\b
```

**scope:** `portable-statement`.

### EVA_DOC_REPORTED_METRIC_FINAL

reported metric

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive documentation evidence reviewed across the development log; no repository identity or labels enter matching.

**All required positive patterns:**

```regex
\b(?:accuracy|precision|recall|f1|error rate|misclassification rate|runtime|run time|memory usage)\b
\b(?:results?|achiev\w*|obtain\w*|performance|measur\w*|evaluat\w*|report\w*|baseline)\b
\d+(?:\.\d+)?\s*(?:\\?%|seconds?\b|milliseconds?\b|MB\b|GB\b)
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|code|repository|package|software|toolbox|model|method|algorithm|experiment\w*|results?|parser)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not implemented|future work|planned|todo|hypothetical)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|external|third[- ]party)\s+(?:repository|software|package|tool)\b
```

**unit_policy:** `documented-workflow-v5`.

### EVA_DOC_RESEARCH_EVALUATION_COMMAND_FINAL

research evaluation command

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive documentation evidence reviewed across the development log; no repository identity or labels enter matching.

**All required positive patterns:**

```regex
(?m)^\s*(?:(?:python[23]?|bash|sh|Rscript|julia|matlab)\s+|\./)[^\n]*(?:eval(?:uate|uation)?|acc(?:uracy|s)?|benchmark|metrics?|score|test[_-]and[_-]train|train[_-]and[_-]test)[\w./-]*
\b(?:model|experiment\w*|dataset|data|train|validation|test|results?|accurac\w*|metric\w*|parser)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|code|repository|package|software|toolbox|model|method|algorithm|experiment\w*|results?|parser)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not implemented|future work|planned|todo|hypothetical)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:references|bibliography)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|external|third[- ]party)\s+(?:repository|software|package|tool)\b
```

**unit_policy:** `documented-workflow-v5`.

### EVA_CODE_STATISTICAL_COMPARISON_FINAL

statistical comparison

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Executable scientific API evidence with argument/context requirements; comments/literals masked. No general semantic guarantee.

**All required positive patterns:**

```regex
\b(?:t\.test|wilcox\.test|anova|ttest|ttest_ind|ttest_rel|mannwhitneyu|kstest|ks_2samp|chisquare|cor_test|cor\.test)\s*\(
\(\s*[A-Za-z_]\w*
```

**scope:** `portable-statement`.

### EVA_CODE_CROSS_VALIDATION_CALL_FINAL

cross validation call

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Executable scientific API evidence with argument/context requirements; comments/literals masked. No general semantic guarantee.

**All required positive patterns:**

```regex
\b(?:cross_val_score|cross_validate|crossval|cv\.glmnet)\s*\(
\(\s*[A-Za-z_]\w*
```

**scope:** `portable-statement`.

## Dissemination

### DIS_CODE_ACTIVITY_V1

Communicate or deposit research outputs for external reuse.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 8 lines (subject to detector unit policy).

**Why this rule exists:** External publication/deposition of research outputs; README presence and generic software releases do not suffice.

**All required positive patterns:**

```regex
^\s*def\s+(?:deposit_research_dataset|publish_research_results|archive_research_software)\s*\(
\b(?:zenodo\.deposit|repository\.publish)\s*\(
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

### DIS_DOC_EXPLICIT_V2

Communicate or deposit research outputs for external reuse.

**Source:** documentation. **Detector/layer:** explicit. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** External publication/deposition of research outputs; README presence and generic software releases do not suffice. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(publish(?:es|ed|ing)?|deposit(?:s|ed|ing)?|archiv(?:e|es|ed|ing)|releas(?:e|es|ed|ing))\b
\b(research (?:results|dataset|software)|scientific findings)\b[^\n]{0,100}\b(?:doi|zenodo|public repository|journal)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### DIS_DOC_CONTEXTUAL_V2

Communicate or deposit research outputs for external reuse.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** External publication/deposition of research outputs; README presence and generic software releases do not suffice. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:publish(?:es|ed|ing)?|deposit(?:s|ed|ing)?|archiv(?:e|es|ed|ing)|export(?:s|ed|ing)?|present(?:s|ed|ing)?|distribut(?:e|es|ed|ing)|prepar(?:e|es|ed|ing))\b
\b(?:research (?:results|datasets?|software|artifacts)|scientific (?:findings|figures|results)|publication[- ]ready figures)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our (?:tool|package|repository|software|library|workflow)|this (?:tool|package|repository|software|library|workflow)|the (?:package|software|repository))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### DIS_DOC_WORKFLOW_V2

Communicate or deposit research outputs for external reuse.

**Source:** documentation. **Detector/layer:** workflow. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** External publication/deposition of research outputs; README presence and generic software releases do not suffice. Activity/object must have affirmative local-repository scope; contextual and workflow families are unapproved candidates.

**All required positive patterns:**

```regex
\b(?:publish(?:es|ed|ing)?|deposit(?:s|ed|ing)?|archiv(?:e|es|ed|ing)|export(?:s|ed|ing)?|present(?:s|ed|ing)?|distribut(?:e|es|ed|ing)|prepar(?:e|es|ed|ing))\b
\b(?:research (?:results|datasets?|software|artifacts)|scientific (?:findings|figures|results)|publication[- ]ready figures)\b
```

**Local scope/header pattern:**

```regex
\b(?:run|use|execute)\s+(?:this|the|our)\s+(?:command|workflow|tutorial)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|references|bibliography|installation|dependencies|acknowledgments)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### DIS_DOC_RESEARCH_V3

Repository-scoped research activity and object using common disciplinary wording.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object conjunction; supports instructional and passive repository descriptions without requiring the literal word research.

**All required positive patterns:**

```regex
(?<![-_./])\b(?:paper|publication|published|cite|citation|article|results|figures?)\b
(?<![-_./])(?:arxiv\.org/|doi\.org/|@(?:article|inproceedings)\s*\{|\b(?:code|scripts?|repository|accompanying|associated|presented|described|report(?:ed|ing)?|reproduc(?:e|ing)|visualiz(?:e|ing)|plot(?:s|ting)?)\b)
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|run|python|available|download|paper|publication|cite|citation)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|installation|dependencies)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### DIS_CODE_RESEARCH_V3

Research-specific implementation operation with a contextual identifier.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 3 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive operation and contextual identifier in the same Python function; comments and strings masked. No repository identity or human label is a feature.

**All required positive patterns:**

```regex
\b(?:savefig|ggsave)\s*\(
\b(?:plt|fig|figure|plot|results)\b
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

**scope:** `statement`.

### DIS_CODE_MULTILANG_V3

Conjunctive research operation and contextual identifier in R, Julia, MATLAB or shell.

**Source:** code. **Detector/layer:** native-code. **Window bound:** 6 lines (subject to detector unit policy).

**Why this rule exists:** Lexically masked comments and strings cannot provide either condition; matched executable statements are evidence, without asserting scientific validity. Function/call context for method; research repetitions for experimentation.

**All required positive patterns:**

```regex
\b(?:ggsave|savefig|saveas|exportgraphics)\s*\(
\b(?:plot|figure|fig|results)\b
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|does not|do not|not supported|not implemented|planned|todo|future work|hypothetical|example only)\b
```

**scope:** `statement`.

**extensions:** `['.r', '.jl', '.m', '.sh']`.

### DIS_DOC_EXTENDED_V4

Candidate extended wording for dissemination.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General activity/object wording from the conceptual stage definition; no benchmark identity, labels or unique repository phrase used. Synthetic tests only; empirical benefit unverified.

**All required positive patterns:**

```regex
\b(?:generat(?:e|es|ed|ing)|creat(?:e|es|ed|ing)|produc(?:e|es|ed|ing)|export(?:s|ed|ing)?)\b
\b(?:(?:plots?|figures?|tables?)\s+(?:of|for|from)\s+(?:the\s+)?(?:experimental|research|scientific)\s+(?:results|outputs)|publication[- ]ready\s+(?:plots?|figures?|tables?))\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this\s+(?:tool|package|software|repository|code|library|implementation)|the\s+(?:tool|package|software|repository|code|library))\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not|never|doesn't|don't|cannot|can't|will|plan(?:s|ned)?|todo|future work|hypothetical|example only|might|could|would|may|should)\b
\b(?:pip|dependencies|install(?:ation)?|health.check|software tests?)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|related work|installation|dependencies)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:we|this (?:tool|package|repository))\s+(?:use|uses|cite|cites|recommend|recommends|invoke|invokes)\s+[^.!?]{1,100}\b(?:to|which|that)\b
```

### DIS_DOC_WORKFLOW_V5_1

Development candidate: documentation-described dissemination activities and artifacts.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General heading/paragraph/workflow evidence motivated by development-only error review; no repository identity or label enters matching. Stage proxies need codebook review; not an independent evaluation.

**All required positive patterns:**

```regex
\b(?:paper|article|publication|thesis|preprint|technical report|citation|citing|cite|bibtex|@article|@inproceedings)\b
\b(?:code|repository|accompan\w*|reproduc\w*|results|availab\w*|cite|citing|citation|figures?|tables?|arxiv|doi|title|author)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|package|library|run|python|Rscript|MATLAB|notebook|paper|publication|cite|citation|download)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not supported|not implemented|does not|do not|cannot|doesn.t|don.t|never|future work|planned|todo|hypothetical|example only)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:unit|integration|software) tests?\b
```

**unit_policy:** `documented-workflow-v5`.

### DIS_DOC_WORKFLOW_V5_2

Development candidate: documentation-described dissemination activities and artifacts.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** General heading/paragraph/workflow evidence motivated by development-only error review; no repository identity or label enters matching. Stage proxies need codebook review; not an independent evaluation.

**All required positive patterns:**

```regex
(?<![\w./-])(?:plots?|plotting|figures?|tables?|visualiz\w*|latex|knit\w*|reports?)\b
\b(?:paper|publication|manuscript|research results|publish\w*|export\w*|savefig|ggsave)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|package|library|run|python|Rscript|MATLAB|notebook|paper|publication|cite|citation|download)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not supported|not implemented|does not|do not|cannot|doesn.t|don.t|never|future work|planned|todo|hypothetical|example only)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:unit|integration|software) tests?\b
```

**unit_policy:** `documented-workflow-v5`.

### DIS_CODE_BRACE_EXPORT_V51

Export a scientific communication artifact with result/figure/report context.

**Source:** code. **Detector/layer:** brace-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Export a scientific communication artifact with result/figure/report context. Comments/literals are masked and all matching conditions must occur inside one executable brace block, excluding declarations and software-test paths. Lexical candidate evidence, not semantic proof.

**All required positive patterns:**

```regex
\b(?:savefig|saveFigure|exportFigure|writeFigure|exportPlot|writeReport|publishResults)\s*\(
\b(?:results|plot|figure|report|researchOutputs|trialResults)\b
```

**scope:** `lexical-block`.

**extensions:** `['.c', '.cpp', '.cc', '.h', '.hpp', '.java', '.js', '.ts', '.go', '.rs', '.scala']`.

### DIS_CODE_BRACE_DEPOSIT_V51

Deposit identified research outputs through an explicit publication call.

**Source:** code. **Detector/layer:** brace-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Deposit identified research outputs through an explicit publication call. Comments/literals are masked and all matching conditions must occur inside one executable brace block, excluding declarations and software-test paths. Lexical candidate evidence, not semantic proof.

**All required positive patterns:**

```regex
\b(?:zenodo\s*\.\s*deposit|repository\s*\.\s*publish)\s*\(
\b(?:researchOutputs|research_outputs|trialResults|researchDataset)\b
```

**scope:** `lexical-block`.

**extensions:** `['.c', '.cpp', '.cc', '.h', '.hpp', '.java', '.js', '.ts', '.go', '.rs', '.scala']`.

### DIS_CODE_PORTABLE_EXPORT_V51

Export a scientific communication artifact from research outputs.

**Source:** code. **Detector/layer:** portable-lexical-v1. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Export a scientific communication artifact from research outputs. All conditions must occur within one lexical statement. Comments and literals are masked. This is a language-neutral candidate heuristic, not a semantic proof.

**All required positive patterns:**

```regex
\b(?:savefig|ggsave|saveFigure|exportFigure|writeFigure|exportPlot|writeReport|publishResults)\b\s*(?:\(|[A-Za-z_$])
\b(?:results|plot|figure|report|researchOutputs|trialResults)\b
```

**scope:** `portable-statement`.

### DIS_DOC_RESEARCH_RESULTS_ARCHIVE_V53

Repository explicitly presents archived research data and results; does not by itself establish runnable experiments or evaluation code.

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Sharing archived research outputs is Dissemination evidence.

**All required positive patterns:**

```regex
\b(?:experiment|research|study)\s+data\s+and\s+results\b
\b(?:on|for|from|of|accompany\w*)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|repository|code|scripts?|implementation|package|library|run|python|Rscript|MATLAB|notebook|paper|publication|cite|citation|download)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not supported|not implemented|does not|do not|cannot|doesn.t|don.t|never|future work|planned|todo|hypothetical|example only)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|another|external|third[- ]party)\s+(?:tool|package|repository|library|software)\b
\b(?:unit|integration|software) tests?\b
```

**unit_policy:** `documented-workflow-v5`.

### DIS_DOC_LINKED_RESEARCH_ARTIFACT_FINAL

linked research artifact

**Source:** documentation. **Detector/layer:** contextual. **Window bound:** 12 lines (subject to detector unit policy).

**Why this rule exists:** Conjunctive documentation evidence reviewed across the development log; no repository identity or labels enter matching.

**All required positive patterns:**

```regex
(?:arxiv\.org/(?:abs|pdf)/|doi\.org/|aclanthology\.org/|aclweb\.org/anthology/|https?://[^\s)>]+\.pdf\b)
\b(?:code|repository|software|toolbox|package|experiments?|accompanies|replicat\w*|reproduc\w*)\b
```

**Local scope/header pattern:**

```regex
\b(?:we|our|this|code|repository|package|software|toolbox|model|method|algorithm|experiment\w*|results?|parser)\b
```

**Document scope fallback under its unit policy:**

```regex
\b(?:research|experiments?|paper|scientific|study|simulation|models?|algorithms?|learning|datasets?|corpus|analysis|measurements)\b
```

**Command requirement for workflow-layer matching:**

```regex
^\s*(?:\$\s*)?[a-z][\w.-]*\s+(?:[a-z][\w./-]*|--[a-z][\w-]*)
```

**Candidate exclusion patterns:**

```regex
\b(?:not implemented|future work|planned|todo|hypothetical)\b
```

**Excluded heading contexts:**

```regex
\b(?:future|roadmap|installation|dependencies|acknowledgments|credits|license|related work)\b
\b(?:licen[cs]e|copyright|acknowledg\w*|bibliography)\b
```

**Excluded third-party scope:**

```regex
\b(?:other|external|third[- ]party)\s+(?:repository|software|package|tool)\b
```

**unit_policy:** `documented-workflow-v5`.

## Interpretation and limitations

A generic download, load, run, model, accuracy or print keyword is not a universal rule. Only the concrete combinations above qualify. A documentation mention can be positive when implementation is missing or not detected; a code-only positive can be absent from documentation. These differences are evidence-scope differences and rule limitations, not automatically annotation errors. All 100 benchmark repositories informed rule development; reference agreement is not held-out accuracy.
