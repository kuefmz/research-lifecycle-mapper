"""Inventory supplied research results; does not certify their scientific compatibility."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = []
for relative in ("results", "data/runs", "data/reports"):
    directory = ROOT / relative
    if not directory.exists():
        continue
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.name in {"inventory.json", ".corpus.lock"}:
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        records.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": digest.hexdigest(),
            }
        )
output = ROOT / "results/inventory.json"
output.write_text(
    json.dumps({"files": records, "validation": "content inventory only"}, indent=2) + "\n"
)
print(f"Indexed {len(records)} files in {output.relative_to(ROOT)}")
