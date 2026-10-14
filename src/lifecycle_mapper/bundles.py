"""Portable snapshot archives with explicit redistribution checks."""

import io
import tarfile
from pathlib import Path

from .acquisition import replay
from .canonical import contained


def pack(snapshot: Path, output: Path) -> None:
    manifest, _ = replay(snapshot)
    if manifest.get("redistribution") not in {
        "approved-for-redistribution",
        "synthetic-original-test-content",
    }:
        raise ValueError("Redistribution has not been reviewed and approved for this snapshot")
    if output.exists():
        raise ValueError("Bundle output already exists")
    paths = ["manifest.json"] + [
        "content/" + item["path"] for item in manifest["files"] if item["status"] == "captured"
    ]
    with tarfile.open(output, "w", format=tarfile.USTAR_FORMAT) as archive:
        for relative in sorted(paths):
            data = contained(snapshot, relative).read_bytes()
            entry = tarfile.TarInfo(relative)
            entry.size = len(data)
            entry.mode = 0o644
            entry.mtime = entry.uid = entry.gid = 0
            entry.uname = entry.gname = ""
            archive.addfile(entry, io.BytesIO(data))


def unpack(bundle: Path, output: Path) -> None:
    if output.exists():
        raise ValueError("Replay snapshot directory already exists")
    with tarfile.open(bundle, "r:") as archive:
        entries = archive.getmembers()
        names = [entry.name for entry in entries]
        if len(names) != len(set(names)) or "manifest.json" not in names:
            raise ValueError("Invalid bundle inventory")
        for entry in entries:
            if not entry.isfile() or entry.size > 10_000_000:
                raise ValueError("Bundle permits only bounded regular files")
            contained(output, entry.name)
            if entry.name != "manifest.json" and not entry.name.startswith("content/"):
                raise ValueError("Unexpected bundle member")
        output.mkdir(parents=True)
        for entry in entries:
            stream = archive.extractfile(entry)
            if stream is None:
                raise ValueError("Unreadable bundle member")
            path = contained(output, entry.name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(stream.read())
    replay(output)
