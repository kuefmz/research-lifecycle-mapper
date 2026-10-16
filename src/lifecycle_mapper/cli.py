"""Research CLI; replay is the default and benchmark never acquires live inputs."""

import argparse
from pathlib import Path
from . import MODES

from .acquisition import acquire
from .analysis import analyze
from .annotations import import_annotations
from .benchmark import run, verify
from .bundles import pack, unpack
from .canonical import json_bytes, write_json, read_json
from .consensus import import_final, publication_export
from .protocol import create_split, freeze
from .batch import predict_batch, read_inputs
from .comparison import compare
from .dataset import DEFAULT_DATASET, convert_workbook, execute_dataset, dataset_reference
from .reference import final_reference, audit_workbook
from .web import serve


def main() -> None:
    parser = argparse.ArgumentParser(prog="lifecycle-mapper")
    commands = parser.add_subparsers(dest="command", required=True)
    ui = commands.add_parser("ui", help="Start the local repository and benchmark UI")
    ui.add_argument("--port", type=int, default=8000)
    ui.add_argument("--state-dir", type=Path, default=Path("local/ui"))
    acquisition = commands.add_parser("acquire")
    acquisition.add_argument("url")
    acquisition.add_argument("--ref")
    acquisition.add_argument("--snapshot", type=Path, required=True)
    acquisition.add_argument("--max-bytes", type=int, default=250_000)
    analysis = commands.add_parser("analyze")
    analysis.add_argument("--snapshot", type=Path, required=True)
    analysis.add_argument(
        "--mode",
        choices=["documentation-only", "code-only", "combined"],
        default="documentation-only",
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
    predicting = actions.add_parser("predict", help="Run benchmark heuristics without human labels")
    predicting.add_argument("--input", type=Path, required=True)
    predicting.add_argument("--output", type=Path, required=True)
    predicting.add_argument("--repository-column", default="A")
    predicting.add_argument("--worksheet", default="final_agreement")
    predicting.add_argument("--header-row", type=int, default=1)
    predicting.add_argument("--mode", choices=[*MODES, "all"], default="all")
    predicting.add_argument("--transport", choices=["api", "git"], default="api")
    dataset_import = actions.add_parser(
        "dataset", help="Convert the final workbook to a reusable JSON dataset"
    )
    dataset_import.add_argument("source", type=Path)
    dataset_import.add_argument("--output", type=Path, default=DEFAULT_DATASET)
    executing = actions.add_parser(
        "execute", help="Run the bundled benchmark and checkpoint results in its JSON"
    )
    executing.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    executing.add_argument("--output", type=Path)
    executing.add_argument("--transport", choices=["api", "git"], default="api")
    executing.add_argument("--mode", choices=[*MODES, "all"], default="all")
    comparing = actions.add_parser(
        "compare", help="Compare pinned captures to imported reference labels"
    )
    comparing.add_argument("--reference", type=Path, required=True)
    comparing.add_argument("--run", type=Path, required=True)
    comparing.add_argument("--split", type=Path, required=True)
    comparing.add_argument("--rules", type=Path)
    comparing.add_argument(
        "--partition", choices=["development", "held_out", "full_exploratory"], action="append"
    )
    comparing.add_argument("--output", type=Path, required=True)
    auditing = actions.add_parser(
        "audit", help="Audit final labels and independent annotator cells"
    )
    auditing.add_argument("source", type=Path)
    auditing.add_argument("--annotator-sheets", nargs=2, required=True)
    auditing.add_argument("--output", type=Path, required=True)
    execution = actions.add_parser("run")
    execution.add_argument("--config", type=Path, default=Path("configs/benchmark.yaml"))
    execution.add_argument("--output", type=Path)
    verification = actions.add_parser("verify")
    verification.add_argument("--config", type=Path, required=True)
    verification.add_argument("--workspace", type=Path, required=True)
    verification.add_argument("--reference", type=Path)
    final_import = actions.add_parser("import")
    final_import.add_argument("source", type=Path)
    final_import.add_argument("--config", type=Path, required=True)
    final_import.add_argument("--approval", type=Path)
    final_import.add_argument("--output", type=Path, required=True)
    splitting = actions.add_parser("split")
    splitting.add_argument("--manifest", type=Path, required=True)
    splitting.add_argument("--output", type=Path, required=True)
    splitting.add_argument("--test-fraction", type=float, default=0.2)
    splitting.add_argument("--seed", default="rlm-split-v1")
    freezing = actions.add_parser("freeze")
    freezing.add_argument("--config", type=Path, required=True)
    freezing.add_argument("--output", type=Path, required=True)
    freezing.add_argument("--approval-reference", required=True)
    exporting = actions.add_parser("export")
    exporting.add_argument("--imported", type=Path, required=True)
    exporting.add_argument("--release-approval", type=Path, required=True)
    exporting.add_argument("--output", type=Path, required=True)
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
        if args.command == "ui":
            serve(Path.cwd(), args.state_dir, args.port)
            return
        elif args.command == "acquire":
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
        elif args.action == "dataset":
            result = convert_workbook(args.source, args.output)
        elif args.action == "execute":
            result = execute_dataset(
                args.dataset,
                args.output,
                args.transport,
                MODES if args.mode == "all" else (args.mode,),
            )
        elif args.action == "predict":
            records = read_inputs(
                args.input, args.repository_column, args.worksheet, args.header_row
            )
            result = predict_batch(
                records,
                args.output,
                MODES if args.mode == "all" else (args.mode,),
                reference=(
                    final_reference(args.input)
                    if args.input.suffix.lower() == ".xlsx" and args.worksheet == "final_agreement"
                    else dataset_reference(read_json(args.input))
                    if args.input.suffix.lower() == ".json"
                    and isinstance(read_json(args.input), dict)
                    and read_json(args.input).get("kind") == "lifecycle-benchmark-dataset"
                    else None
                ),
                transport=args.transport,
            )
        elif args.action == "audit":
            result = audit_workbook(args.source, tuple(args.annotator_sheets))
            if args.output.exists():
                raise ValueError("Audit output already exists")
            write_json(args.output, result)
        elif args.action == "compare":
            result = compare(
                args.reference,
                args.run,
                args.split,
                args.output,
                args.rules,
                tuple(args.partition or ["development"]),
            )
        elif args.action == "run":
            result = {"run_directory": str(run(args.config, args.output))}
        elif args.action == "import":
            result = import_final(args.source, args.output, args.config, args.approval)
        elif args.action == "split":
            result = create_split(args.manifest, args.output, args.test_fraction, args.seed)
        elif args.action == "freeze":
            result = freeze(args.config, args.output, args.approval_reference)
        elif args.action == "export":
            result = publication_export(args.imported, args.output, args.release_approval)
        else:
            result = verify(args.config, args.workspace, args.reference)
        print(json_bytes(result).decode(), end="")
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"error: {exc}\n")
