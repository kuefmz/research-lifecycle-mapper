# Human annotation provenance — current status

Jenifer and Esteban independently classified the same 100 repositories against six lifecycle stages, then reviewed the annotations together and agreed on final_agreement (researcher confirmation, 2026-10-20). The final 600 labels are complete and are the documentation-only evaluation reference.

See ../../docs/annotation_status_20261020.md for the exact connected-source verification and the discrepancy between the reported independent-cell correction and the still-empty original Method cell. Do not confuse this historical reliability issue with incomplete final consensus. Recompute initial agreement from the corrected original version; never fill independent labels from consensus or classifier output.

The final labels match the bundled dataset JSON exactly. Final-label consensus does not establish sampling randomness, annotation-time repository commits, a versioned human codebook, or code-only accuracy. The relationship among the 105k frame, 386 candidates and 100 benchmark repositories must be documented.

Original independent labels and final adjudication remain separate immutable inputs. Exports record exact checksums; do not alter reference labels to improve classifier agreement. Additional code evidence is manually reviewed using a separate rubric. The original source workbook is not modified by the application.
