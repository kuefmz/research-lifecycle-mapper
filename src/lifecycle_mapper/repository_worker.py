"""Private CLI worker; credentials are inherited from environment, never job files."""

import sys
from pathlib import Path

from .canonical import read_json
from .corpus import PacedAPI, run_repository
from .telemetry import configure


def main() -> None:
    job = read_json(Path(sys.argv[1]))
    configure(Path(job["heartbeat"]))
    run_repository(
        job["record"],
        Path(job["output"]),
        tuple(job["modes"]),
        job["transport"],
        job["max_bytes"],
        PacedAPI(job["api_interval"]),
        job["retry_failed"],
        Path(job["rules_dir"]) if job["rules_dir"] else None,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Worker failed: " + type(exc).__name__, file=sys.stderr)
        raise SystemExit(2) from None
