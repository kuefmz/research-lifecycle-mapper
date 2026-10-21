"""Conservative lexical views for brace-delimited source; never compile or run."""

import re

BRACE_SUFFIXES = {".c", ".cpp", ".cc", ".h", ".hpp", ".java", ".js", ".ts", ".go", ".rs", ".scala"}


def lexical_view(text: str, suffix: str) -> str:
    """Mask comments/literals without moving any original character or line.

    Reject unhandled literals rather than treating their text as executable.
    This is a lexical detector, not a compiler, type checker or data-flow proof.
    """
    chars = list(text)
    i = 0
    while i < len(text):
        start = i
        if text.startswith("//", i):
            end = text.find("\n", i)
            i = len(text) if end == -1 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end == -1:
                raise ValueError("unterminated-comment")
            if suffix == ".rs":
                depth = 1
                at = i + 2
                while depth:
                    match = re.search(r"/\*|\*/", text[at:])
                    if match is None:
                        raise ValueError("unterminated-comment")
                    depth += 1 if match.group() == "/*" else -1
                    at += match.end()
                i = at
            else:
                i = end + 2
        elif suffix in {".c", ".cpp", ".cc", ".h", ".hpp"} and text.startswith('R"', i):
            match = re.match(r'R"([^\s()\\]{0,16})\(', text[i:])
            if match is None:
                raise ValueError("unsupported-raw-string")
            close = ")" + match[1] + '"'
            end = text.find(close, i + match.end())
            if end == -1:
                raise ValueError("unterminated-raw-string")
            i = end + len(close)
        elif suffix == ".rs" and re.match(r'b?r#*"', text[i:]):
            match = re.match(r'b?r(#{0,})"', text[i:])
            assert match is not None
            close = '"' + match[1]
            end = text.find(close, i + match.end())
            if end == -1:
                raise ValueError("unterminated-raw-string")
            i = end + len(close)
        elif text.startswith('"""', i):
            end = text.find('"""', i + 3)
            if end == -1:
                raise ValueError("unterminated-text-block")
            i = end + 3
        elif text[i] in {'"', "'", "`"}:
            quote = text[i]
            if (
                quote == "'"
                and suffix in {".c", ".cpp", ".cc", ".h", ".hpp"}
                and i > 0
                and text[i - 1].isdigit()
                and i + 1 < len(text)
                and text[i + 1].isalnum()
            ):
                i += 1  # C++ digit separator, not a character literal.
                continue
            if quote == "'" and suffix in {".rs", ".scala"}:
                literal = re.match(r"'(?:\\(?:u\{[0-9a-fA-F]+\}|.)|[^'\\\n])'", text[i:])
                if literal is None:  # Lifetime/symbol, not a quoted string.
                    i += 1
                    continue
            at = i + 1
            while at < len(text):
                if quote != "`" and text[at] == "\\":
                    at += 2
                elif text[at] == quote:
                    break
                else:
                    at += 1
            if at >= len(text):
                raise ValueError("unterminated-literal")
            if quote == "`" and suffix in {".js", ".ts"} and "${" in text[i:at]:
                raise ValueError("unsupported-template-interpolation")
            i = at + 1
        else:
            i += 1
            continue
        for index in range(start, i):
            if chars[index] not in "\r\n":
                chars[index] = " "
    view = "".join(chars)
    if suffix in {".js", ".ts"} and re.search(r"(?:[=(:,;!&|?]|\breturn)\s*/(?![/*])", view):
        raise ValueError("unsupported-regex-literal")
    return view


def executable_blocks(view: str) -> list[dict[str, int | str]]:
    """Balanced brace blocks with source ranges; declarations remain outside rules."""
    stack = []
    result: list[dict[str, int | str]] = []
    for match in re.finditer(r"[{}]", view):
        position = match.start()
        if match.group() == "{":
            boundary = max(view.rfind(c, 0, position) for c in ";{}") + 1
            header = view[boundary:position].strip()
            stack.append((position, boundary, header))
        else:
            if not stack:
                raise ValueError("unbalanced-braces")
            opening, boundary, header = stack.pop()
            # Function/loop/conditional blocks contain executable statements.
            # Class, namespace, object and initializer bodies alone are not enough.
            if ")" in header or re.search(r"\b(?:else|try|finally|do)\s*$", header):
                result.append(
                    {
                        "start_line": view.count("\n", 0, boundary) + 1,
                        "end_line": view.count("\n", 0, position) + 1,
                        "body_start": opening + 1,
                        "body_end": position,
                        "header": header,
                    }
                )
    if stack:
        raise ValueError("unbalanced-braces")
    return result
