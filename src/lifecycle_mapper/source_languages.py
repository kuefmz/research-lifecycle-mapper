"""Pinned programming-language inventory; data formats always take precedence."""

import json
from pathlib import Path, PurePosixPath

CATALOG = json.loads(Path(__file__).with_name("language_catalog.json").read_text())
DATA_SUFFIXES = {
    ".ttl",
    ".rdf",
    ".owl",
    ".nt",
    ".nq",
    ".trig",
    ".csv",
    ".tsv",
    ".json",
    ".jsonl",
    ".ndjson",
    ".jsonld",
    ".xml",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".parquet",
    ".feather",
    ".arrow",
    ".h5",
    ".hdf5",
    ".npy",
    ".npz",
    ".arff",
    ".pkl",
    ".pickle",
    ".rds",
    ".rdata",
    ".dat",
    ".bin",
    ".log",
    ".svg",
}
_extensions: dict[str, list[str]] = {}
_filenames: dict[str, list[str]] = {}
for _language in CATALOG["languages"]:
    for _suffix in _language["extensions"]:
        _extensions.setdefault(_suffix.lower(), []).append(_language["name"])
    for _filename in _language["filenames"]:
        _filenames.setdefault(_filename.lower(), []).append(_language["name"])
_compound = tuple(sorted((s for s in _extensions if s.count(".") > 1), key=len, reverse=True))


def language_names(path: str) -> list[str]:
    name = PurePosixPath(path).name.lower()
    suffix = PurePosixPath(name).suffix
    if suffix in DATA_SUFFIXES:
        return []
    if name in _filenames:
        return _filenames[name]
    for extension in _compound:
        if name.endswith(extension):
            return _extensions[extension]
    return _extensions.get(suffix, [])


def extension_for_language(language: str) -> str | None:
    for row in CATALOG["languages"]:
        if row["name"].casefold() == language.casefold() and row["extensions"]:
            return row["extensions"][0].lower()
    return None
