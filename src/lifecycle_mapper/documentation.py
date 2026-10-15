"""Deterministic documentation units, polarity/scope and inspectable dimensions.

No repository identity, gold labels or source code enter this detector.
"""

import re
import unicodedata
from typing import Any

from .canonical import sha256, physical_lines

VERSION = "documentation-units-1"


def normalize(text: str) -> str:
    # Physical lines are preserved. Compatibility/case expansion needs no column mapping.
    return (
        unicodedata.normalize("NFKC", text)
        .casefold()
        .translate({ord("’"): "'", ord("‘"): "'", ord("–"): "-", ord("—"): "-", ord("\u00a0"): " "})
    )


def document_units(text: str) -> list[dict[str, Any]]:
    """Sentence-scoped prose and purpose+fenced-command workflow units, max 12 lines.

    Headings propagate as exclusion context, not positive stage features. Prose
    wraps are joined inside paragraphs; distinct sentences cannot lend scope to
    each other. Fences remain documentation, never leak into implementation mode.
    """
    masked = re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n\r]", " ", m.group()), text, flags=re.S)
    lines = physical_lines(masked)
    units: list[dict[str, Any]] = []
    heading = ""
    heading_stack: list[tuple[int, str]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        heading_match = re.match(r"^\s*([#=]{1,6})\s+(.+)$", line)
        rst_heading = index + 1 < len(lines) and bool(
            re.fullmatch(r"\s*[-=~^]{3,}\s*", lines[index + 1])
        )
        if heading_match or rst_heading:
            level = (
                len(heading_match[1]) if heading_match else (1 if "=" in lines[index + 1] else 2)
            )
            title = heading_match[2] if heading_match else line.strip()
            heading_stack = [(depth, value) for depth, value in heading_stack if depth < level]
            heading_stack.append((level, title))
            heading = " / ".join(value for _, value in heading_stack)
            if rst_heading:
                index += 1
            index += 1
            continue
        if not line.strip():
            index += 1
            continue
        start = index
        fenced = False
        while index < len(lines) and index - start < 12:
            current = lines[index]
            if re.match(r"^\s*(?:```|~~~)", current):
                fenced = not fenced
            if index > start and not fenced and re.match(r"^\s*#{1,6}\s", current):
                break
            if index > start and not fenced and re.match(r"^\s*(?:[-*+]\s|\d+[.)]\s)", current):
                break
            if not current.strip() and not fenced:
                # A blank before a command fence can connect an immediately preceding purpose.
                if index + 1 < len(lines) and re.match(r"^\s*(?:```|~~~)", lines[index + 1]):
                    index += 1
                    continue
                break
            index += 1
        if index == start:
            index += 1
        block = "\n".join(lines[start:index])
        if re.search(r"^\s*(?:```|~~~)", block, re.M):
            units.append(
                {
                    "text": normalize(block),
                    "start_line": start + 1,
                    "end_line": index,
                    "heading": normalize(heading),
                    "kind": "workflow",
                }
            )
        else:
            # Sentence boundaries only at punctuation followed by whitespace.
            for match in re.finditer(r"[\s\S]+?(?:[.!?](?=\s|$)|\Z)", block):
                sentence = match.group()
                if not sentence.strip():
                    continue
                left = match.start() + len(sentence) - len(sentence.lstrip())
                right = match.end() - len(sentence) + len(sentence.rstrip())
                units.append(
                    {
                        "text": normalize(block[left:right]),
                        "start_line": start + block.count("\n", 0, left) + 1,
                        "end_line": start + block.count("\n", 0, max(left, right - 1)) + 1,
                        "heading": normalize(heading),
                        "kind": "prose",
                    }
                )
    return units


def documentation_matches(
    text: str, rule: dict[str, Any], units: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    records = []
    original_lines = physical_lines(text, keepends=True)
    for unit in document_units(text) if units is None else units:
        if rule["layer"] == "workflow" and unit["kind"] != "workflow":
            continue
        if rule["layer"] != "workflow" and unit["kind"] != "prose":
            continue
        window = unit["text"]
        matches = [re.search(pattern, window, re.I | re.M) for pattern in rule["positive"]]
        if not all(matches):
            continue
        reasons = [
            "polarity:" + pattern
            for pattern in rule["exclusions"]
            if re.search(pattern, window, re.I)
        ]
        reasons += [
            "heading-scope:" + pattern
            for pattern in rule["heading_exclusions"]
            if re.search(pattern, unit["heading"], re.I)
        ]
        reasons += [
            "third-party-scope:" + pattern
            for pattern in rule["scope_exclusions"]
            if re.search(pattern, window, re.I)
        ]
        scope_match = re.search(rule["context_pattern"], window, re.I)
        if scope_match is None:
            reasons.append("ambiguous-repository-scope")
        if rule["layer"] == "workflow" and not re.search(rule["command_pattern"], window, re.M):
            reasons.append("missing-demonstrated-command")
        start_line, end_line = unit["start_line"], unit["end_line"]
        excerpt = "".join(original_lines[start_line - 1 : end_line]).rstrip("\r\n")
        dimensions = {
            "activity": matches[0].group() if matches[0] else "",
            "object": matches[1].group() if matches[1] else "",
            "context": scope_match.group() if scope_match else "unresolved",
            "polarity": "excluded-or-ambiguous" if reasons else "affirmative",
            "scope": "unresolved-or-excluded" if reasons else "repository",
            "layer": rule["layer"],
            "heading": unit["heading"],
            "unit_version": VERSION,
        }
        records.append(
            {
                "start_line": start_line,
                "end_line": end_line,
                "excerpt": excerpt,
                "matched_conditions": [m.group() for m in matches if m is not None],
                "supporting_conditions": [],
                "documentation_dimensions": dimensions,
                "exclusion_reasons": reasons,
                "excerpt_sha256": sha256(excerpt.encode()),
            }
        )
    return records
