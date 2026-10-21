"""Small, atomic worker heartbeats; no content, headers or credentials."""

import json
import time
from pathlib import Path
from typing import Any

_path: Path | None = None
_state: dict[str, Any] = {}


def configure(path: Path) -> None:
    global _path, _state
    _path = path
    _state = {
        "phase": "starting",
        "files_attempted": 0,
        "files_captured": 0,
        "captured_bytes": 0,
        "api_calls": 0,
        "rate_limit_wait_seconds": 0.0,
    }
    emit()


def emit(**fields: Any) -> None:
    if _path is None:
        return
    _state.update(fields)
    _state["updated_at_unix"] = time.time()
    temporary = _path.with_suffix(".tmp")
    temporary.write_text(json.dumps(_state, sort_keys=True) + "\n")
    temporary.replace(_path)


def current_state() -> dict[str, Any]:
    return dict(_state)
