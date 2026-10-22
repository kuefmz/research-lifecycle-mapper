# Heuristics

The single maintained profile contains 105 conjunctive documentation/code rules across
six stages. Catalog metadata uses release 1.0.0. Do not retune frozen rules in place.

The `.yaml` files contain JSON (a YAML-compatible subset). `rule_catalog.csv` and
`docs/rules.md` document the exact runtime objects. `profile_checksums.json` records
current checksums. Packaged defaults and root rules are identical copies checked by
scripts/verify_final_profile.py.

Read ../../docs/method.md and ../../docs/rules.md for execution and limitations.
Existing saved runs retain original metadata and hashes; see ../../docs/cleanup-provenance.json.
All 100 annotated repositories informed development; release naming does not create
an independent held-out evaluation.
