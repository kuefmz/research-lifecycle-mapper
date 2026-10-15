"""Canonical UTF-8 JSON and CSV; decimal metrics rounded to eight places."""

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(
        {key: f"{value:.8f}" if isinstance(value, float) else value for key, value in row.items()}
        for row in rows
    )
    path.write_text(stream.getvalue(), encoding="utf-8")


def ratio(numerator: int | float, denominator: int | float) -> float:
    return round(numerator / denominator, 8) if denominator else 0.0


def contained(root: Path, relative: str) -> Path:
    """Reject path traversal and symlink escapes, including preexisting symlinks."""
    candidate = root / relative
    if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"Unsafe relative path: {relative!r}")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes root: {relative!r}")
    return candidate


def physical_lines(text: str, keepends: bool = False) -> list[str]:
    """GitHub line anchors count LF/CRLF, not Unicode paragraph separators."""
    parts = text.split("\n")
    result = [line + "\n" if keepends else line.removesuffix("\r") for line in parts[:-1]]
    if parts[-1]:
        result.append(parts[-1] if keepends else parts[-1].removesuffix("\r"))
    return result
