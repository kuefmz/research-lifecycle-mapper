import ast
import warnings

import pytest

from lifecycle_mapper.analysis import analyze, parse_python
from helpers import make_snapshot


def test_repository_invalid_escape_warnings_do_not_spam_stderr(tmp_path):
    text = 'pattern = "\\ "\ndef preprocess_data(data):\n    return data.dropna()\n'
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = analyze(make_snapshot(tmp_path, text), "code-only")
    assert result["labels"] == ["Processing"]
    assert not caught


def test_python2_print_syntax_keeps_original_evidence_lines(tmp_path):
    text = (
        "def evaluate_research_predictions():\n"
        '    print "legacy report"\n'
        "    return f1_score(reference_labels, predictions)\n"
    )
    result = analyze(make_snapshot(tmp_path, text), "code-only")
    assert result["scan_complete"]
    assert result["labels"] == ["Evaluation"]
    assert result["evidence"][0]["code_syntax_policy"].startswith("python2-syntax")
    assert result["evidence"][0]["start_line"] == 1
    assert result["evidence"][0]["end_line"] == 3
    assert 'print "legacy report"' in result["evidence"][0]["excerpt"]


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
