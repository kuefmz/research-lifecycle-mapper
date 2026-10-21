"""Read notebook cell sources only; never execute cells or inspect outputs."""

import json
import re
from copy import deepcopy
from typing import Any
from .source_languages import extension_for_language

LANGUAGES = {"python": ".py", "r": ".r", "julia": ".jl", "matlab": ".m", "bash": ".sh", "sh": ".sh"}


def expand_notebooks(
    manifest: dict[str, Any], contents: dict[str, str]
) -> tuple[dict[str, Any], dict[str, str]]:
    """Create deterministic cell views after integrity checking original blobs.

    Lines are cell-relative. Unreadable containers affect both channels; unknown
    languages and magics affect code only. Raw cells and outputs are not sources.
    Original manifests and original content hashes are never rewritten.
    """
    result = deepcopy(manifest)
    expanded = dict(contents)
    files = []
    for item in manifest["files"]:
        if item["source"] != "notebook":
            files.append(item)
            continue
        if item["status"] == "excluded":
            continue

        def unavailable(source: str, reason: str) -> None:
            files.append(
                {
                    **item,
                    "path": item["path"] + "/unavailable-" + source,
                    "source": source,
                    "status": "unavailable",
                    "reason": reason,
                    "notebook_path": item["path"],
                }
            )

        if item["status"] != "captured":
            for source in ("documentation", "code"):
                unavailable(source, item["reason"])
            continue
        try:
            notebook = json.loads(contents[item["path"]])
            if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
                raise ValueError("unsupported notebook format")
            metadata = notebook.get("metadata", {})
            language = metadata.get("language_info", {}).get("name") or metadata.get(
                "kernelspec", {}
            ).get("language", "")
            suffix = LANGUAGES.get(str(language).lower())
            broad_policy = manifest.get("policy_version") in {
                "eligibility-3-programming-catalog",
                "eligibility-4-txt-folder-density",
            }
            if suffix is None and broad_policy:
                suffix = extension_for_language(str(language)) or ".unknown-code"
            cells = []
            for index, cell in enumerate(notebook["cells"], 1):
                kind = cell["cell_type"]
                if kind == "raw":
                    continue
                if kind not in {"markdown", "code"}:
                    raise ValueError("unknown cell type")
                text = cell["source"]
                if isinstance(text, list) and all(isinstance(x, str) for x in text):
                    text = "".join(text)
                if not isinstance(text, str):
                    raise ValueError("invalid cell source")
                source = "documentation" if kind == "markdown" else "code"
                extension = ".md" if kind == "markdown" else suffix or ".unsupported"
                path = item["path"] + f"/cell-{index:05d}" + extension
                reason = None
                ignored_lines = []
                if kind == "code" and suffix == ".py":
                    lines = text.splitlines(keepends=True)
                    for number, line in enumerate(lines, 1):
                        if re.fullmatch(r"\s*%matplotlib\s+(?:inline|notebook|widget)\s*", line):
                            ignored_lines.append(number)
                            lines[number - 1] = re.sub(r"[^\r\n]", " ", line)
                    text = "".join(lines)
                if kind == "code" and text.strip():
                    if suffix is None:
                        reason = "notebook-language-unsupported"
                    elif (
                        not broad_policy
                        and suffix == ".py"
                        and any(
                            line.lstrip().startswith(("%", "!", "?")) for line in text.splitlines()
                        )
                    ):
                        reason = "notebook-magic-unsupported"
                cells.append(
                    {
                        **item,
                        "path": path,
                        "source": source,
                        "status": "unavailable" if reason else "captured",
                        "reason": reason,
                        "notebook_path": item["path"],
                        "notebook_cell": index,
                        "notebook_cell_type": kind,
                        "notebook_language": str(language),
                        "ignored_plotting_magic_lines": ignored_lines,
                    }
                )
                expanded[path] = text
            files.extend(cells)
        except (ValueError, TypeError, KeyError, AttributeError):
            for source in ("documentation", "code"):
                unavailable(source, "notebook-parse-error")
    result["files"] = files
    return result, expanded
