"""Broad lexical evidence scanning, with explicit provenance and no code execution."""

import re
from bisect import bisect_right
from typing import Any

from pygments.lexers import get_lexer_for_filename, get_lexer_by_name  # type: ignore[import-untyped]
from pygments.token import Comment, Literal, Error  # type: ignore[import-untyped]
from pygments.util import ClassNotFound  # type: ignore[import-untyped]

from .source_languages import language_names
from .canonical import physical_lines


def wolfram_view(text: str) -> str:
    """Linear masking of nested Wolfram comments and escaped string literals."""
    chars = list(text)
    i = 0
    while i < len(text):
        start = i
        if text.startswith("(*", i):
            depth = 1
            i += 2
            while i < len(text) and depth:
                if text.startswith("(*", i):
                    depth += 1
                    i += 2
                elif text.startswith("*)", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError("unterminated-wolfram-comment")
        elif text[i] == '"':
            i += 1
            while i < len(text):
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError("unterminated-wolfram-string")
        else:
            i += 1
            continue
        for offset in range(start, min(i, len(chars))):
            if chars[offset] not in "\r\n":
                chars[offset] = " "
    return "".join(chars)


def token_view(text: str, path: str) -> tuple[str, dict[str, Any]]:
    """Mask comments/literals at original offsets; no language is excluded for lack of a lexer."""
    if path.lower().endswith((".nb", ".wl", ".wls")):
        gap = None
        try:
            view = wolfram_view(text)
        except ValueError:
            view = re.sub(r"[^\r\n]", " ", text)
            gap = "malformed-wolfram-source"
        return view, {
            "languages": ["Wolfram Language"],
            "policy": "wolfram-linear-v1",
            "lexer": None,
            "error_tokens": 0,
            "coverage_gap": gap
            or (
                "serialized-notebook-box-code-unparsed"
                if path.lower().endswith(".nb")
                and re.search(r"\b(?:RowBox|FractionBox|SuperscriptBox)\s*\[", view)
                else None
            ),
        }
    names = language_names(path)
    info: dict[str, Any] = {
        "languages": names or ["unidentified-notebook-language"],
        "policy": "pygments-lexical-v1",
        "lexer": None,
        "error_tokens": 0,
    }
    try:
        lexer = get_lexer_for_filename(path, text)
        tokens = list(lexer.get_tokens_unprocessed(text))
        errors = sum(token in Error for _, token, _ in tokens)
        if errors and len(names) > 1:
            # Ambiguous extensions (notably .pl) need content-aware alternatives.
            for language in names:
                try:
                    candidate = get_lexer_by_name(language.lower().replace(" ", "-"))
                    candidate_tokens = list(candidate.get_tokens_unprocessed(text))
                    candidate_errors = sum(token in Error for _, token, _ in candidate_tokens)
                    if candidate_errors < errors:
                        lexer, tokens, errors = candidate, candidate_tokens, candidate_errors
                except ClassNotFound:
                    continue
        info["lexer"] = lexer.name
        chars = list(text)
        for offset, token, value in tokens:
            if token in Error:
                info["error_tokens"] += 1
            bare_symbol = token in (Literal.String.Atom, Literal.String.Symbol) and re.fullmatch(
                r"[A-Za-z_]\w*", value
            )
            if token in Comment or (token in Literal.String and not bare_symbol) or token in Error:
                for index in range(offset, min(len(chars), offset + len(value))):
                    if chars[index] not in "\r\n":
                        chars[index] = " "
        return "".join(chars), info
    except Exception as exc:
        if not isinstance(exc, ClassNotFound):
            info["lexer_failure"] = type(exc).__name__
        info["policy"] = "conservative-token-fallback-v1"
        # Unknown grammar: suppress common literal/comment forms conservatively.
        # Masking may remove real operations; this is explicitly weaker than a parser.
        pattern = (
            r'"""[\s\S]*?(?:"""|$)|\x27\x27\x27[\s\S]*?(?:\x27\x27\x27|$)|'
            r'"(?:\\[\s\S]|[^"\\])*(?:"|$)|\x27(?:\\[\s\S]|[^\x27\\])*(?:\x27|$)|'
            r"`[^`]*(?:`|$)|/\*[\s\S]*?(?:\*/|$)|//[^\n]*|\#[^\n]*|--[^\n]*"
        )
        return re.sub(pattern, lambda m: re.sub(r"[^\r\n]", " ", m.group()), text), info


def statements(view: str) -> list[dict[str, int]]:
    """Separate lexical statements; do not conjoin unrelated commands or declarations."""
    units = []
    start = depth = 0
    for offset, char in enumerate(view):
        if char in "([":
            depth += 1
        elif char in ")]":
            depth = max(0, depth - 1)
        if char in "{}" or (depth == 0 and char in ";\n") or offset == len(view) - 1:
            end = offset if char in "{}" else offset + 1
            chunk = view[start:end]
            # Imports, function signatures and declarations are not activity evidence.
            declaration = re.match(
                r"\s*(?:def|function|fn|func|class|interface|struct|module|namespace|import|from|using|package|include)\b",
                chunk,
            )
            if chunk.strip() and not declaration:
                units.append({"start": start, "end": end})
            start = offset + 1
    return units


def matches(
    text: str, path: str, rules: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    view, info = token_view(text, path)
    records = []
    rules = [
        rule
        for rule in rules
        if all(
            re.search(pattern, view, re.I | re.M)
            for pattern in rule.get("file_context_patterns", [])
        )
    ]
    newline_positions = [match.start() for match in re.finditer("\n", view)]
    # Use LF positions, matching the rest of the evidence pipeline.
    original_lines = text.split("\n")
    for unit in statements(view):
        chunk = view[unit["start"] : unit["end"]]
        lines = physical_lines(chunk, keepends=True)
        for rule in rules:
            seen = set()
            start = unit["start"]
            for index, line in enumerate(lines):
                window = "".join(lines[index : index + rule["window_lines"]])
                found = [re.search(pattern, window, re.I | re.M) for pattern in rule["positive"]]
                if all(found):
                    actual = [match for match in found if match is not None]
                    left = start + min(match.start() for match in actual)
                    right = start + max(match.end() for match in actual)
                    first = bisect_right(newline_positions, left - 1) + 1
                    last = bisect_right(newline_positions, max(left, right - 1) - 1) + 1
                    identity = (first, last)
                    if identity not in seen:
                        seen.add(identity)
                        records.append(
                            {
                                "stage": rule["stage"],
                                "source": "code",
                                "rule_id": rule["id"],
                                "rule_version": rule["version"],
                                "start_line": first,
                                "end_line": last,
                                "matched_conditions": [match.group() for match in actual],
                                "supporting_conditions": [],
                                "exclusion_reasons": [
                                    p for p in rule["exclusions"] if re.search(p, window, re.I)
                                ],
                                "excerpt": "\n".join(original_lines[first - 1 : last]).rstrip(
                                    "\r\n"
                                ),
                                "code_syntax_policy": info["policy"],
                                "lexer": info["lexer"],
                                "languages": info["languages"],
                            }
                        )
                start += len(line)
    return records, info
