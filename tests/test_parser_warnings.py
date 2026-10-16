import ast
import warnings

import pytest

from lifecycle_mapper.analysis import analyze, parse_python
from lifecycle_mapper.cli import show_progress
from test_rules import make_snapshot


def test_repository_invalid_escape_warnings_do_not_spam_stderr(tmp_path):
    text = 'pattern = "\\ "\ndef preprocess_data(data):\n    return data.dropna()\n'
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = analyze(make_snapshot(tmp_path, text), "code-only")
    assert result["labels"] == ["Processing"]
    assert not caught


def test_syntax_errors_and_other_warnings_remain_visible(monkeypatch):
    with pytest.raises(SyntaxError):
        parse_python("def broken(:", "broken.py")
    original_parse = ast.parse

    def warn_then_parse(*args, **kwargs):
        warnings.warn("unrelated source warning", SyntaxWarning)
        return original_parse(*args, **kwargs)

    monkeypatch.setattr(ast, "parse", warn_then_parse)
    before = list(warnings.filters)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        tree = parse_python("x = 2\n", "literal.py")
    assert isinstance(tree, ast.Module)
    assert any("unrelated source warning" in str(w.message) for w in caught)
    assert warnings.filters == before


def test_progress_is_flushed_to_stderr_not_json_stdout(capsys):
    show_progress({"completed": 8, "total": 100, "current_repository": "https://github.com/a/b"})
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "[8/100]" in captured.err and "https://github.com/a/b" in captured.err


def test_execute_command_connects_progress_and_preserves_json_output(monkeypatch, capsys):
    import json
    import sys
    from lifecycle_mapper import cli

    def fake_execute(*args, progress):
        progress({"completed": 8, "total": 100, "current_repository": "https://github.com/a/b"})
        return {"completed": 8}

    monkeypatch.setattr(cli, "execute_dataset", fake_execute)
    monkeypatch.setattr(
        sys, "argv", ["lifecycle-mapper", "benchmark", "execute", "--transport", "git"]
    )
    cli.main()
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"completed": 8}
    assert "[8/100]" in captured.err
