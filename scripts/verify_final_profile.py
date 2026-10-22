"""Verify frozen scientific catalog and packaged default without network access."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
profile = ROOT / "configs/heuristics"
record = json.loads((profile / "profile_checksums.json").read_text())
count = 0
for name, digest in record["yaml_sha256"].items():
    data = (profile / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, f"Changed frozen rule file: {name}"
    mirror = ROOT / "src/lifecycle_mapper/rules" / name
    assert mirror.read_bytes() == data, f"Inconsistent packaged rule: {name}"
    count += len(json.loads(data)["rules"])
assert count == record["rule_count"] == 105
print("Verified 105 frozen rules and packaged default")
