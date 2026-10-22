"""Syntax-only Python 2 compatibility; original source is never executed or changed."""

import warnings


def modernize_syntax(text: str) -> str | None:
    """Return a parse view only when conversion preserves every physical line.

    Python 3.12 (the project's pinned runtime) includes lib2to3. Only syntax
    fixers are enabled: no import, API or scientific-operation rewriting.
    Unsupported conversions remain explicit parse failures.
    """
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message="lib2to3 package is deprecated.*", category=DeprecationWarning
            )
            from lib2to3.refactor import RefactoringTool
        tool = RefactoringTool(
            [
                "lib2to3.fixes.fix_" + name
                for name in ("print", "except", "raise", "numliterals", "ne", "exec", "repr")
            ]
        )
        source = text if text.endswith("\n") else text + "\n"
        converted = str(tool.refactor_string(source, "inspected_source"))
        if converted == source or converted.count("\n") != source.count("\n"):
            return None
        return converted
    except (ImportError, ValueError, SyntaxError):
        return None
    except Exception:
        # lib2to3 ParseError/TokenError are parser-specific; preserve unknowns.
        return None
