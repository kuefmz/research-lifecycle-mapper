"""Package original scientific outputs for review, without repository snapshots or secrets.

Creates a private transfer ZIP, not a publication-ready anonymous artifact.
"""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

RUN_FILES = (
    "manifest.json",
    "summary.json",
    "progress.json",
    "stopped_repositories.json",
    "predictions.csv",
    "repository_status.csv",
    "documentation_comparison.csv",
    "additional_evidence_candidates.csv",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        type=Path,
        action="append",
        required=True,
        help="Original run directory; repeat for the 100, 286 and 2825 batches",
    )
    parser.add_argument(
        "--openaire-list",
        type=Path,
        required=True,
        help="Original full 3211-repository list, not the remaining subset",
    )
    parser.add_argument("--output", type=Path, default=Path("local/results-upload.zip"))
    args = parser.parse_args()
    sources = []
    for index, run in enumerate(args.run, 1):
        if not (run / "manifest.json").is_file():
            parser.error(f"Missing run manifest: {run}")
        results = sorted((run / "repositories").glob("*/result.json"))
        if not results:
            parser.error(f"No repository results found: {run}")
        prefix = f"runs/batch-{index:03d}"
        for name in RUN_FILES:
            path = run / name
            if path.is_file():
                sources.append((path, f"{prefix}/{name}"))
        for number, path in enumerate(results, 1):
            digest = path.with_name("result.sha256")
            if not digest.is_file():
                parser.error(f"Missing result checksum: {digest}")
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest.read_text().strip():
                parser.error(f"Result checksum mismatch: {path}")
            for item in (path, digest):
                sources.append((item, f"{prefix}/repositories/repository-{number:04d}/{item.name}"))
    if not args.openaire_list.is_file():
        parser.error(f"Missing full OpenAIRE repository list: {args.openaire_list}")
    root = Path(__file__).resolve().parents[1]
    for source, destination in (
        (root / "data/corpus/benchmark_100.txt", "lists/benchmark-100.txt"),
        (root / "data/corpus/benchmark_386.txt", "lists/corpus-386.txt"),
        (args.openaire_list, "lists/corpus-3211.txt"),
    ):
        sources.append((source, destination))
    inventory = [
        {
            "path": destination,
            "bytes": source.stat().st_size,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
        for source, destination in sources
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        parser.error(f"Output already exists; choose a new filename: {args.output}")
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, destination in sources:
            archive.write(source, destination)
        archive.writestr(
            "transfer_manifest.json",
            json.dumps(
                {
                    "purpose": "Private transfer of original outputs for verification and anonymous publication preparation",
                    "files": inventory,
                    "excluded": [
                        "snapshots",
                        "downloaded repository files",
                        "tokens",
                        "environment files",
                        "Git directories",
                        "software archives",
                    ],
                },
                indent=2,
            )
            + "\n",
        )
    print(
        f"Created {args.output}: {len(sources)} files, {args.output.stat().st_size / 1048576:.2f} MiB"
    )
    print("Upload this ZIP in the conversation. Do not commit the private transfer ZIP.")
    print(
        "Original JSON may contain local paths or original metadata; publication requires review."
    )


if __name__ == "__main__":
    main()
