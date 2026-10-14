import io
import tarfile
from pathlib import Path

import pytest

from lifecycle_mapper.analysis import analyze
from lifecycle_mapper.bundles import pack, unpack

ROOT = Path(__file__).resolve().parents[1]


def test_portable_bundle_replay_and_stable_bytes(tmp_path):
    source = ROOT / "benchmark/synthetic/snapshots/docs-positive"
    pack(source, tmp_path / "first.tar")
    pack(source, tmp_path / "second.tar")
    assert (tmp_path / "first.tar").read_bytes() == (tmp_path / "second.tar").read_bytes()
    unpack(tmp_path / "first.tar", tmp_path / "snapshot")
    assert analyze(source, "combined") == analyze(tmp_path / "snapshot", "combined")


def test_bundle_rejects_unsafe_paths(tmp_path):
    with tarfile.open(tmp_path / "unsafe.tar", "w") as archive:
        for name in ["manifest.json", "../escape"]:
            entry = tarfile.TarInfo(name)
            entry.size = 2
            archive.addfile(entry, io.BytesIO(b"{}"))
    with pytest.raises(ValueError, match="Unsafe"):
        unpack(tmp_path / "unsafe.tar", tmp_path / "snapshot")
    assert not (tmp_path / "snapshot").exists()
