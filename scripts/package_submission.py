"""Build a history-free submission ZIP from tracked files; audit identities separately."""

import argparse
import hashlib
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = (".github/",)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("dist/submission.zip"))
    args = parser.parse_args()
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", ZIP_DEFLATED) as archive:
        for name in sorted(files):
            if not name or name.startswith(EXCLUDED) or name == "AGENTS.md":
                continue
            path = ROOT / name
            if path.is_file():
                archive.write(path, name)
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(".sha256").write_text(digest + "\n")
    print(f"{args.output}: {digest}")
    print("Tracked files only. Untracked local results are NOT included. Audit the extracted ZIP.")


if __name__ == "__main__":
    main()
