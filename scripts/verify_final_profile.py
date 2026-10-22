"""Verify frozen scientific catalog and both default mirrors without network access."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
profile = ROOT / "configs/consolidated-development-v5.4"
record = json.loads((profile / "profile_checksums.json").read_text())
count = 0
for name, digest in record["yaml_sha256"].items():
    data = (profile / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, f"Changed frozen rule file: {name}"
    for mirror in (ROOT / "rules", ROOT / "src/lifecycle_mapper/rules"):
        assert (mirror / name).read_bytes() == data, f"Inconsistent mirror: {mirror}/{name}"
    count += len(json.loads(data)["rules"])
assert count == record["rule_count"] == 105
print("Verified 105 frozen rules and both default mirrors")
