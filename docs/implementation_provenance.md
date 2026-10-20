# Upstream audit and implementation provenance

Audited repository: (upstream source withheld during anonymous review)

Exact audited commit: `dfb22f9545860a99a57199975dd78a4d9cb80fea` (root commit).

Inspected: README, recursive inventory, `heuristics.py`, `analyzer.py`, `storage.py`, `api.py`, heuristic tests, OpenAIRE compiler, corpus README, and annotations README. The original repository was not modified. Upstream tests were inspected, not executed in this project.

The inspected tree contains no LICENSE or declared licensing grant. Attribution does not substitute for a license. **No upstream source code, test bodies, cached results, or corpus rows are distributed here.** There is consequently no source commit from which code was copied; the commit above identifies the implementation whose concepts were audited. The new code and synthetic fixtures are independently authored and MIT licensed. Any later literal adaptation requires an explicit compatible licensing grant, attribution, and a recorded adaptation commit.

| Upstream component | Useful concept carried forward | Gap/change in this implementation |
| --- | --- | --- |
| heuristics.py | Stable IDs, multi-label rules, deterministic artifact typing | External versioned catalogs with positive conjunctions, exclusions and conceptual justifications; source paths alone never qualify |
| analyzer.py | File inventory, evidence terms and line numbers | Immutable commit resolution, blob acquisition, content hashes, safe offline replay and exact start/end ranges |
| storage.py | Persistent JSON records, content-derived identifiers, atomic-write intent | URL-only write-once caching removed; snapshot/rule/config/benchmark hashes identify inputs and runs cannot overwrite output directories |
| api.py | Evidence URL inspection and explicit repository requests | HTTP server, random batches and demo cache omitted; research CLI is the supported interface |
| OpenAIRE compiler | Separate raw corpus records, normalized repository identities and provenance | Source frame described with its limits; no claim that its default random batch produced the human sample |
| heuristic tests | Positive/negative, multi-label and test-versus-evaluation distinctions | Independently authored offline tests add mode isolation, pinning, incomplete scans, leakage and canonical reproduction |

Specific audit findings:

* The analyzer uses a mutable branch/ref for tree lookup and raw downloads. `commit_tree_sha` is a tree object SHA, not a resolved commit. A branch can advance during acquisition and evidence URLs can change meaning.
* Content download exceptions collapse into an empty unscanned file without an error record. Decoding uses replacement characters. This implementation records unavailable artifacts and rejects non-UTF-8 content.
* URL-only persistence returns earlier cached results despite changed ref, content limits or rules; the API disables custom refs. The research design requires explicit immutable inputs instead.
* Sorting by lowercased paths does not fully define case-sensitive tie order. This implementation uses exact path ordering.
* The score threshold is two, while most content rules contribute one per stage. Isolated path rules can nevertheless qualify Collection, Processing, Experimentation, Evaluation or Dissemination. README presence qualifies Dissemination. These behaviors conflict with the brief's conservative evidence requirement.
* Generic source directories, packaging and software tests qualify upstream Implementation. They cannot be converted mechanically to Method.
* The entry-point regular expression appears over-escaped in the inspected source. It was not inherited.
* The corpus README's positional compiler example does not match the inspected script's CLI: the actual script accepts `--software-tar` and `--output-dir`. Do not reuse that example unchanged.
* The annotation directory contains a placeholder README, not the independent workbook or adjudicated gold labels. Cached heuristic results are not annotation data.

The compiler identifies Zenodo record `12819872`, field `codeRepositoryUrl`, GitHub-host filtering, normalization, and case-insensitive repository deduplication. This supports documenting a **candidate sampling frame**, not inventing how the 100 human-annotated repositories were actually selected.

These substantive differences are deliberate methodological changes. They are not claims that the original authors approved the new rule catalog.

## v0.2.0 reuse/redesign

The v0.1 acquisition, replay, source isolation, evidence linking, metric computation, bundles and canonical serialization were reused directly within this new repository. Documentation matching, benchmark import and evaluation protocol were redesigned for the revised specification. The source audit also inspected the upstream summary.json; candidate_sampling_frame.md records its documented hashes/counts with explicit unverified-sample limits. No new upstream code was copied.
