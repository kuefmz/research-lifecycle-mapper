# Multilanguage development v5.1

Development profile with 75 rules: all 59 v5 rules retained unchanged, plus nine brace-language rules and seven portable source rules. Documentation rules are unchanged. This is not a new measured benchmark result or an accuracy guarantee.

Programming files are selected using the bundled pinned GitHub Linguist programming-language catalogue (562 languages), with explicit data-format exclusions. C, C++, Java, JavaScript, TypeScript, Go, Rust and Scala receive brace-block matching; all selected source languages receive portable statement matching using pinned Pygments tokenization. If a lexer is unavailable, conservative quote/comment masking is recorded explicitly. Native syntax gaps remain source warnings when lexical scanning succeeds. Scan complete means all selected scans ran, not complete semantic comprehension.

Notebook Markdown cells are documentation; code cells use their kernel language and portable fallback. Outputs, raw cells and metadata are excluded. Data contents (including TTL and CSV) never supply stage evidence. No repository code is executed.

Each rule in rule_catalog.csv records its exact runtime specification. Added brace rules cover acquisition, preparation, model calls, named numerical computation, controlled trials, metric calls, metric arithmetic, result export and deposition. Added portable rules cover acquisition, preparation, model operations, repeated trials, metric calls, metric arithmetic and result export. All required conditions must co-occur in the configured block or statement; comments and string contents are masked. These are candidate evidence rules requiring empirical validation.

Source scans retain lexer/fallback policy, language names, native detector policy and warnings. Evidence retains file/cell, physical line range, matched rule attribution and excerpt. Documentation-only, code-only and combined results remain separate; combined is their union.

Rebuild with `python scripts/build_multilanguage_profile.py`. Catalogue provenance and third-party licence are bundled with the package; regenerate that catalogue using scripts/build_language_catalog.py and its pinned upstream source. Run instructions: docs/run-benchmark-100.md. Use a fresh output directory after changing the profile or acquisition policy.
