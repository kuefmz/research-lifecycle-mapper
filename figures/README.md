# OpenAIRE selection funnel

Source: [OpenAIRE Graph Dataset](https://zenodo.org/records/20428976), release 11.1.1,
published 2026-06-08. Its `software.tar` contains research-software metadata; the
source deposition reports 730,346 software records.

`openaire_funnel_counts.json` is the single figure count/provenance source. The figure
was adapted from the supplied editable generator. `openaire_funnel.svg` remains
editable text/vector artwork; PDF is the complete figure linked from the root README. PNG is intentionally not retained because its preview omits content.

```bash
uv run --frozen --with matplotlib==3.10.8 python scripts/create_openaire_funnel.py
```

Optional `--full-summary PATH --filtered-summary PATH` checks actual extraction summaries
against all corresponding count fields and the archive SHA-256 before rendering. See
[the extraction commands](../docs/data-generation.md). Rendering stored counts alone
is figure reproduction, not an independent rerun of the OpenAIRE extraction.

The branches distinguish records, record-repository links and deduplicated repositories.
The 386 are supplied publication-associated repositories with verified containment in
the reconstructed 3,211 list. The original publication-selection query is unavailable.
The figure therefore does not depict that query as a reproduced extraction step.
The 100 are the annotated development sample; 286 complete the 386 and 2,825 complete
3,211. The figure distinguishes verified repository membership from the unreconstructed publication-selection query.
