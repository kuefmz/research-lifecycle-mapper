"""Small, atomic worker heartbeats; no content, headers or credentials."""

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

_path: Path | None = None
_state: dict[str, Any] = {}
_lock = threading.RLock()


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
    with _lock:
        _state.update(fields)
        _state["updated_at_unix"] = time.time()
        temporary = None
        try:
            _path.parent.mkdir(parents=True, exist_ok=True)
            # Unique temp files avoid collisions with concurrent telemetry writers.
            with tempfile.NamedTemporaryFile(
                mode="w", dir=_path.parent, prefix=".heartbeat-", delete=False
            ) as handle:
                temporary = Path(handle.name)
                handle.write(json.dumps(_state, sort_keys=True) + "\n")
            os.replace(temporary, _path)
        except OSError as exc:
            # Monitoring must never turn a successful acquisition into a failure.
            _state["telemetry_write_error"] = type(exc).__name__
            _state["telemetry_write_errno"] = exc.errno
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass


def current_state() -> dict[str, Any]:
    with _lock:
        return dict(_state)
