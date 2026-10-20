# Annotation status and evidence scope — 2026-10-20

This note supersedes earlier statements that the final reference has not been adjudicated.

## Confirmed by the researchers

Jenifer states that, after the initial independent annotation/agreement phase, Jenifer and Esteban reviewed the annotations together and agreed on the final_agreement worksheet. Treat those final labels as the jointly adjudicated documentation reference. Human annotation considers documentation only. This confirmation does not establish that an operational classifier codebook is identical to the original human instructions, that sampling is random, or that historical repository commits are known.

## Verified against the exact connected source

Read final_agreement!A1:G101 and both named independent annotator tabs on 2026-10-20. The final table has 100 unique repository identities and 600 literal binary labels, with stage positives 36, 44, 71, 88, 66, 79. Every final label matches the bundled JSON. No reference labels or source cells were changed.

Jenifer reports that the missing record has been fixed. In the connected source read during this update, research_lifecycle_benchmark_100_jenifer!D61 still returns an empty value for Method at michael135/count-vector-paper-experiments. This is an unresolved source/version discrepancy, not an unresolved final consensus label. The current observed independent table yields 599 valid pairs, 353 agreements, 246 disagreements and one missing pair. Do not infer whether its eventual correction is 0 or 1. Re-audit the corrected original before updating initial agreement/kappa. A later correction informed by adjudication must not be described as an original independent judgment unless that history is established.

The current final labels are complete and agreed regardless of that historical independent-cell issue. They are the primary documentation reference. Historical 2026-10-15 measurements retain their original denominators and source checksum.

## What the evaluation means

1. Compare documentation-only predictions with final_agreement. A disagreement is a documentation classifier error (or unknown when acquisition is incomplete), subject to manual evidence review.
2. Review source-code detections separately. No documentation classifier match is not sufficient proof that documentation contains no relevant information.
3. A human documentation label of 0 plus manually validated relevant source evidence is a candidate documentation omission. Review the full documentation scope before confirming it.
4. A human label of 1 with documentation prediction 0 remains a documentation false negative even if code detects the activity.
5. Code-only or combined agreement against documentation labels is not independently validated code accuracy. Use those modes for evidence expansion; do not optimize them to erase documentation errors.
6. Other files are supplementary only to the extent actually supported. The current classifier does not cover notebooks, PDFs, configuration files or all programming languages. A research activity match is not evidence of execution or reproducibility.

Keep initial inter-rater agreement separate from final adjudication. Joint consensus does not make the initial independent agreement 100%.

## Evidence review table

For each repository-stage, retain the documentation label/prediction, documentation completeness, code prediction, commit-pinned path/lines/excerpt, reviewer decisions, and final category: documentation detector error; confirmed additional source evidence; irrelevant/static-code false positive; ambiguous; unsupported/unavailable. Count repository-stage discoveries separately from multiple matching occurrences.
