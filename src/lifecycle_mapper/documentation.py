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
    text: str,
    rule: dict[str, Any],
    units: list[dict[str, Any]] | None = None,
    *,
    first_only: bool = False,
) -> list[dict[str, Any]]:
    records = []
    workflow_policy = rule.get("unit_policy") == "documented-workflow-v5"
    if workflow_policy and units is None:
        units = workflow_units(text)
    original_lines = physical_lines(text, keepends=True)
    fallback_scope = (
        re.search(rule["document_context_pattern"], normalize(text), re.I)
        if workflow_policy
        else None
    )
    for unit in document_units(text) if units is None else units:
        if not workflow_policy and rule["layer"] == "workflow" and unit["kind"] != "workflow":
            continue
        if not workflow_policy and rule["layer"] != "workflow" and unit["kind"] != "prose":
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
        if scope_match is None and workflow_policy:
            scope_match = fallback_scope
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
            "unit_version": "documented-workflow-v5" if workflow_policy else VERSION,
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
        if first_only and not reasons:
            return records
    return records


def workflow_units(text: str) -> list[dict[str, Any]]:
    """Opt-in paragraph/heading+command units for documented scientific workflows.

    All evidence is a contiguous original-document range of at most 12 lines.
    Scope headings are tracked even when they are outside that range.
    """
    masked = re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n\r]", " ", m.group()), text, flags=re.S)
    lines = physical_lines(masked)
    headings: list[tuple[int, str]] = []
    units = []
    fence = False
    consumed_until = 0
    for index, line in enumerate(lines):
        if re.match(r"^\s*(?:```|~~~)", line):
            fence = not fence
        md = None if fence else re.match(r"^\s*(#{1,6})\s+(.+)$", line)
        rst = (
            not fence
            and index + 1 < len(lines)
            and bool(re.fullmatch(r"\s*[-=~^]{3,}\s*", lines[index + 1]))
        )
        special = not fence and re.fullmatch(
            r"\s*(?:\d+[.)]\s*)?(?:references|bibliography|credits|license|installation|dependencies|future work)\s*[:.]?\s*",
            line,
            re.I,
        )
        if md or rst or special:
            level = len(md[1]) if md else (1 if rst and "=" in lines[index + 1] else 2)
            title = md[2] if md else line.strip()
            headings = [(depth, value) for depth, value in headings if depth < level]
            headings.append((level, title))
        if index < consumed_until:
            continue
        if not line.strip() or re.fullmatch(r"\s*[-=~^]{3,}\s*", line):
            continue
        end = index + 1
        # Keep a paragraph and an immediately following command; never borrow
        # positive features across the next section heading.
        while end < min(len(lines), index + 12):
            if re.match(r"^\s*#{1,6}\s", lines[end]):
                break
            if end + 1 < len(lines) and re.fullmatch(r"\s*[-=~^]{3,}\s*", lines[end + 1]):
                break
            if not lines[end].strip():
                if md or rst:
                    end += 1
                    continue
                if end + 1 < len(lines) and re.match(
                    r"^\s*(?:```|~~~|`|(?:python|Rscript|bash|sh|make)\b)", lines[end + 1]
                ):
                    end += 1
                    continue
                break
            end += 1
        consumed_until = end
        block = "\n".join(lines[index:end])
        # Strip presentation markup only for matching; evidence remains original.
        visible = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 \2", block)
        visible = re.sub(r"<[^>]+>", " ", visible)
        visible = re.sub(r"[*_`]+", " ", visible)
        units.append(
            {
                "text": normalize(visible),
                "start_line": index + 1,
                "end_line": end,
                "heading": normalize(" / ".join(title for _, title in headings)),
                "kind": "workflow-context",
            }
        )
    return units
