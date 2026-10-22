# Final heuristic method, release 1.0

This is the single maintained scientific profile: 105 conjunctive documentation/code
rules across six stages. Its original v5.4 directory and internal JSON version strings
are retained to preserve catalog identity with completed runs; they are provenance,
not additional maintained methods. Do not edit these frozen rules in place.

The `.yaml` files contain JSON (a YAML-compatible subset). `rule_catalog.csv` gives
one row per exact rule. `profile_checksums.json` records original hashes and development
status; that history is not rewritten by the release label. Packaged defaults and root
rules are identical copies checked by scripts/verify_final_profile.py.

Read ../../docs/method.md and ../../docs/rules.md for execution and limitations.
Earlier profiles exist only as historical regression fixtures under tests/fixtures.
No independent held-out evaluation is implied by the release designation.
