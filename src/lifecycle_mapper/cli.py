"""Small local entrypoint; corpus extraction and assessment use their dedicated modules."""

import argparse
from pathlib import Path

from . import MODES
from .acquisition import acquire
from .analysis import analyze
from .bundles import pack, unpack
from .canonical import json_bytes, write_json
from .demo import serve


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lifecycle-mapper",
        description="Detect research lifecycle evidence; replication artifact for the submitted MSR 2027 paper.",
        epilog="Batch runs: python -m lifecycle_mapper.corpus --help. Evaluation: python -m lifecycle_mapper.assess --help.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    ui = commands.add_parser("ui", help="Start the minimal local UI")
    ui.add_argument("--port", type=int, default=8000)
    ui.add_argument("--state-dir", type=Path, default=Path("local/ui"))
    acquisition = commands.add_parser(
        "acquire", help="Capture a public repository without executing it"
    )
    acquisition.add_argument("url")
    acquisition.add_argument("--ref")
    acquisition.add_argument("--snapshot", type=Path, required=True)
    acquisition.add_argument("--max-bytes", type=int, default=10485760)
    analysis = commands.add_parser("analyze", help="Analyze a captured snapshot offline")
    analysis.add_argument("--snapshot", type=Path, required=True)
    analysis.add_argument("--mode", choices=MODES, default="documentation-only")
    analysis.add_argument("--rules", type=Path)
    analysis.add_argument("--output", type=Path)
    snapshot = commands.add_parser("snapshot", help="Pack or restore captured inputs")
    actions = snapshot.add_subparsers(dest="action", required=True)
    bundle = actions.add_parser("pack")
    bundle.add_argument("--snapshot", type=Path, required=True)
    bundle.add_argument("--output", type=Path, required=True)
    restore = actions.add_parser("unpack")
    restore.add_argument("--bundle", type=Path, required=True)
    restore.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "ui":
            serve(Path.cwd(), args.state_dir, args.port)
            return
        if args.command == "acquire":
            result = acquire(args.url, args.snapshot, args.ref, args.max_bytes)
        elif args.command == "analyze":
            result = analyze(args.snapshot, args.mode, args.rules)
            if args.output:
                if args.output.exists():
                    raise ValueError("Analysis output already exists")
                write_json(args.output, result)
        elif args.action == "pack":
            pack(args.snapshot, args.output)
            result = {"output": str(args.output)}
        else:
            unpack(args.bundle, args.output)
            result = {"output": str(args.output)}
        print(json_bytes(result).decode(), end="")
    except (ValueError, OSError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
