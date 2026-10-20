# Annotation provenance

Two independent reviewers annotated 100 repositories across six research-lifecycle stages using documentation only. They then reviewed the annotations jointly and agreed on final_agreement. The final 600 binary labels are the primary documentation reference.

The corrected reviewer2 Method value for michael135/count-vector-paper-experiments is 0. The current independent table has 600 valid pairs, 354 agreements (59%), 246 disagreements (41%) and no missing pairs. The corrected Method Cohen kappa is 0.07334385. Initial independent agreement remains separate from final consensus; do not report joint adjudication as independent 100% agreement.

The workbook has all ten sheets. Human reviewer tabs are reviewer1 and reviewer2. The other eight tabs, their cells, formulas, styles, notes/legends, and final labels are retained. Spreadsheet export shortened several original tab names; their purposes are documented in data/README.md. No mapping from pseudonyms to personal identities is distributed. The original connected workbook was not modified.

The anonymous workbook hash, corrected independent counts and per-stage kappas are in data/annotation_audit_20261020.json. The bundled JSON is regenerated from the anonymous workbook and checksum-bound to it; every final label is unchanged.

Primary evaluation compares documentation-only predictions against final_agreement. Code evidence is separately reviewed. A documentation detector false negative remains a detector error even if code supports the stage. A code-positive/documentation-negative pair is a candidate omission, confirmed only after human review of both the source evidence and the full documentation scope. Unknown acquisition status is not absence.

Historical measurements remain dated and retain their original input versions; they must not be relabeled as results under the current branch policy.
