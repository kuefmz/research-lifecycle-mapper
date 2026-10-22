"""Build a history-free anonymous review ZIP from tracked files.

Shared-conversation URLs and this artifact's recorded source commit IDs are withheld
by default; exact prompts, predictions and scientific configuration hashes are retained.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = (".github/",)


def review_files(root: Path, names: list[str], include_shared_links: bool = False) -> dict:
    files = {
        name: (root / name).read_bytes()
        for name in names
        if name
        and not name.startswith(EXCLUDED)
        and name != "AGENTS.md"
        and (root / name).is_file()
    }
    replacements = {}
    if not include_shared_links:
        for raw in files.values():
            for url in re.findall(rb"https://chatgpt\.com/share/[A-Za-z0-9-]+", raw):
                replacements[url] = (
                    b"withheld-conversation-" + hashlib.sha256(url).hexdigest()[:16].encode()
                )
    # These are this artifact's development commits, not analyzed repository commits.
    for name, raw in files.items():
        if name.endswith("manifest.json"):
            try:
                source = json.loads(raw).get("source", {})
                commit = source.get("commit") if isinstance(source, dict) else None
                if commit and re.fullmatch(r"[a-f0-9]{40}", commit):
                    replacements[commit.encode()] = b"withheld-artifact-development-commit"
            except (ValueError, AttributeError):
                continue
    changed = []
    for name, raw in files.items():
        if name.endswith((".md", ".json", ".ipynb", ".csv", ".txt", ".cff")):
            new = raw
            for before, after in replacements.items():
                new = new.replace(before, after)
            if new != raw:
                changed.append({"path": name, "original_sha256": hashlib.sha256(raw).hexdigest()})
                files[name] = new
    # Update derivative checksum maps so documented integrity checks still work.
    for name, raw in list(files.items()):
        if not name.endswith(".json"):
            continue
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        updated = False
        for field in ("files", "publication_files"):
            mapping = data.get(field)
            if isinstance(mapping, dict):
                for relative, value in mapping.items():
                    target = (Path(name).parent / relative).as_posix()
                    if isinstance(value, str) and target in files:
                        digest = hashlib.sha256(files[target]).hexdigest()
                        if value != digest:
                            mapping[relative] = digest
                            updated = True
        if updated:
            files[name] = (json.dumps(data, indent=2) + "\n").encode()
    files["ANONYMOUS_PACKAGE.json"] = (
        json.dumps(
            {
                "scope": "History-free review derivative; original working files remain unchanged.",
                "shared_conversation_links": "included by explicit option"
                if include_shared_links
                else "withheld; original prompts and saved labels retained",
                "source_commit_policy": "Artifact development commit identifiers withheld; analyzed repository commit identifiers retained.",
                "original_files_transformed": changed,
                "checksum_policy": "Derivative file checksum maps updated where necessary; original source-file hashes retained as provenance.",
                "limitations": "Content scanning cannot guarantee anonymity against contextual inference. See docs/submission.md.",
            },
            indent=2,
        )
        + "\n"
    ).encode()
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("dist/submission.zip"))
    parser.add_argument(
        "--include-shared-links",
        action="store_true",
        help="Include externally traceable conversation links; omit for anonymous review",
    )
    args = parser.parse_args()
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    files = review_files(ROOT, names, args.include_shared_links)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            archive.writestr(name, content)
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(".sha256").write_text(digest + "\n")
    print(f"{args.output}: {digest}")
    print("Tracked files only; Git history and workflow/agent metadata excluded.")
    print("Review derivative created. Audit extracted contents before anonymous publication.")


if __name__ == "__main__":
    main()
