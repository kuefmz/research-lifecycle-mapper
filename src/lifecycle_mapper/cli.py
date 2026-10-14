"""Research CLI; replay is the default and benchmark never acquires live inputs."""

import argparse
from pathlib import Path

from .acquisition import acquire
from .analysis import analyze
from .annotations import import_annotations
from .benchmark import run, verify
from .bundles import pack, unpack
from .canonical import json_bytes, write_json


def main() -> None:
    parser = argparse.ArgumentParser(prog="lifecycle-mapper")
    commands = parser.add_subparsers(dest="command", required=True)
    acquisition = commands.add_parser("acquire")
    acquisition.add_argument("url")
    acquisition.add_argument("--ref")
    acquisition.add_argument("--snapshot", type=Path, required=True)
    acquisition.add_argument("--max-bytes", type=int, default=250_000)
    analysis = commands.add_parser("analyze")
    analysis.add_argument("--snapshot", type=Path, required=True)
    analysis.add_argument(
        "--mode", choices=["documentation-only", "code-only", "combined"], default="combined"
    )
    analysis.add_argument("--rules", type=Path)
    analysis.add_argument("--output", type=Path)
    snapshots = commands.add_parser("snapshot")
    snapshot_actions = snapshots.add_subparsers(dest="action", required=True)
    bundle = snapshot_actions.add_parser("pack")
    bundle.add_argument("--snapshot", type=Path, required=True)
    bundle.add_argument("--output", type=Path, required=True)
    restore = snapshot_actions.add_parser("unpack")
    restore.add_argument("--bundle", type=Path, required=True)
    restore.add_argument("--output", type=Path, required=True)
    benchmark = commands.add_parser("benchmark")
    actions = benchmark.add_subparsers(dest="action", required=True)
    execution = actions.add_parser("run")
    execution.add_argument("--config", type=Path, default=Path("configs/benchmark.yaml"))
    execution.add_argument("--output", type=Path)
    verification = actions.add_parser("verify")
    verification.add_argument("--config", type=Path, required=True)
    verification.add_argument("--workspace", type=Path, required=True)
    verification.add_argument("--reference", type=Path)
    annotations = commands.add_parser("annotations")
    imports = annotations.add_subparsers(dest="action", required=True)
    importer = imports.add_parser("import")
    importer.add_argument("source", type=Path)
    importer.add_argument("--output", type=Path, required=True)
    importer.add_argument("--version", required=True)
    importer.add_argument("--expected-repositories", type=int, default=100)
    importer.add_argument("--expected-disagreements", type=int, default=247)
    args = parser.parse_args()
    try:
        if args.command == "acquire":
            result = acquire(args.url, args.snapshot, args.ref, args.max_bytes)
        elif args.command == "analyze":
            result = analyze(args.snapshot, args.mode, args.rules)
            if args.output:
                if args.output.exists():
                    raise ValueError("Analysis output already exists")
                write_json(args.output, result)
        elif args.command == "annotations":
            result = import_annotations(
                args.source,
                args.output,
                args.version,
                args.expected_repositories,
                args.expected_disagreements,
            )
        elif args.command == "snapshot":
            if args.action == "pack":
                pack(args.snapshot, args.output)
            else:
                unpack(args.bundle, args.output)
            result = {"output": str(args.output)}
        elif args.action == "run":
            result = {"run_directory": str(run(args.config, args.output))}
        else:
            result = verify(args.config, args.workspace, args.reference)
        print(json_bytes(result).decode(), end="")
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"error: {exc}\n")
