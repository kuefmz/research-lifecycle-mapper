"""Candidate conjunctive rules; evidence modes are isolated before aggregation."""

import ast
import io
import json
import re
import tokenize
from pathlib import Path
from typing import Any
from urllib.parse import quote

from . import MODES, STAGES
from .acquisition import replay
from .canonical import json_bytes, sha256


def default_rules() -> Path:
    return Path(__file__).with_name("rules")


def load_rules(directory: Path | None = None) -> tuple[list[dict[str, Any]], str]:
    directory = directory or default_rules()
    rules = []
    for stage in STAGES:
        catalog = json.loads((directory / f"{stage.lower()}.yaml").read_bytes())
        if catalog["version"] != "0.1.0-candidate" or catalog["stage"] != stage:
            raise ValueError("Invalid catalog version/stage")
        rules.extend(catalog["rules"])
    ids = [rule["id"] for rule in rules]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate rule IDs")
    required = {
        "id",
        "stage",
        "source",
        "description",
        "positive",
        "supporting",
        "exclusions",
        "required_evidence_fields",
        "version",
        "justification",
        "status",
        "window_lines",
    }
    for rule in rules:
        if not required <= rule.keys() or rule["stage"] not in STAGES:
            raise ValueError("Incomplete rule definition")
        if rule["source"] not in {"documentation", "code"} or len(rule["positive"]) < 2:
            raise ValueError("Rules require isolated sources and conjunctive positive conditions")
        if not 1 <= rule["window_lines"] <= 12:
            raise ValueError("Invalid evidence window")
        for pattern in rule["positive"] + rule["supporting"] + rule["exclusions"]:
            re.compile(pattern)
    rules.sort(key=lambda rule: (STAGES.index(rule["stage"]), rule["source"], rule["id"]))
    return rules, sha256(json_bytes(rules))


def unit_test_path(path: str) -> bool:
    parts = Path(path.lower()).parts
    return any(part in {"test", "tests", "testing"} for part in parts) or Path(
        path
    ).name.lower().startswith("test_")


def implementation_view(text: str, path: str) -> str:
    """Mask Python comments and docstrings while retaining exact source line positions.

    The initial implementation rules only support Python. Other source languages
    remain inventoried but have no candidate code rules; this is a coverage limit.
    Never execute inspected repository code.
    """
    if Path(path).suffix.lower() != ".py":
        return ""
    ast.parse(text)
    lines = text.splitlines(keepends=True)
    masks = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type in {tokenize.COMMENT, tokenize.STRING}:
            masks.append((token.start, token.end))
    for (start_line, start_col), (end_line, end_col) in masks:
        for index in range(start_line - 1, end_line):
            line = lines[index]
            left = start_col if index == start_line - 1 else 0
            right = end_col if index == end_line - 1 else len(line.rstrip("\r\n"))
            lines[index] = line[:left] + " " * (right - left) + line[right:]
    return "".join(lines)


def analyze(
    snapshot: Path, mode: str, rules_dir: Path | None = None, expected_hash: str | None = None
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}")
    manifest, contents = replay(snapshot, expected_hash)
    rules, rules_hash = load_rules(rules_dir)
    permitted = (
        {"documentation"}
        if mode == MODES[0]
        else {"code"}
        if mode == MODES[1]
        else {"documentation", "code"}
    )
    evidence = []
    excluded_evidence = []
    analysis_errors = []
    for item in manifest["files"]:
        source = item["source"]
        if item["status"] != "captured" or source not in permitted:
            continue
        original_lines = contents[item["path"]].splitlines(keepends=True)
        try:
            view = (
                implementation_view(contents[item["path"]], item["path"])
                if source == "code"
                else contents[item["path"]]
            )
        except (SyntaxError, tokenize.TokenError, IndentationError):
            analysis_errors.append({"path": item["path"], "reason": "python-parse-error"})
            continue
        lines = view.splitlines(keepends=True)
        function_spans = []
        if source == "code" and Path(item["path"]).suffix.lower() == ".py":
            function_spans = [
                (node.lineno, node.end_lineno or node.lineno)
                for node in ast.walk(ast.parse(contents[item["path"]]))
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
        for rule in rules:
            if rule["source"] != source:
                continue
            seen = set()
            for offset in range(len(lines)):
                window = "".join(lines[offset : offset + rule["window_lines"]])
                matches = [re.search(pattern, window, re.I | re.M) for pattern in rule["positive"]]
                if not all(matches):
                    continue
                actual = [match for match in matches if match is not None]
                start = min(match.start() for match in actual)
                end = max(match.end() for match in actual)
                start_line = offset + window.count("\n", 0, start) + 1
                end_line = offset + window.count("\n", 0, max(start, end - 1)) + 1
                if source == "code" and not any(
                    left == start_line and end_line <= right for left, right in function_spans
                ):
                    continue
                identity = (start_line, end_line)
                if identity in seen:
                    continue
                seen.add(identity)
                reasons = [
                    pattern for pattern in rule["exclusions"] if re.search(pattern, window, re.I)
                ]
                if source == "code" and unit_test_path(item["path"]):
                    reasons.append("software-test-path")
                record = {
                    "repository": manifest["repository"],
                    "commit": manifest["commit"],
                    "stage": rule["stage"],
                    "source": source,
                    "rule_id": rule["id"],
                    "path": item["path"],
                    "start_line": start_line,
                    "end_line": end_line,
                    "content_sha256": item["sha256"],
                    "matched_conditions": [match.group(0) for match in actual],
                    "supporting_conditions": [
                        pattern
                        for pattern in rule["supporting"]
                        if re.search(pattern, window, re.I)
                    ],
                    "excerpt": "".join(original_lines[start_line - 1 : end_line]).rstrip("\r\n"),
                    "url": f"{manifest['source_url']}/blob/{manifest['commit']}/{quote(item['path'], safe='/')}#L{start_line}-L{end_line}",
                }
                if reasons:
                    excluded_evidence.append({**record, "exclusion_reasons": reasons})
                else:
                    evidence.append(record)

    def order(record: dict[str, Any]) -> tuple[Any, ...]:
        return (
            STAGES.index(record["stage"]),
            record["path"],
            record["rule_id"],
            record["start_line"],
            record["end_line"],
        )

    evidence.sort(key=order)
    excluded_evidence.sort(key=order)
    labels = [stage for stage in STAGES if any(record["stage"] == stage for record in evidence)]
    eligible = [item for item in manifest["files"] if item["source"] in permitted]
    unavailable = [item for item in eligible if item["status"] == "unavailable"]
    complete = manifest["inventory_complete"] is True and not unavailable and not analysis_errors
    return {
        "repository": manifest["repository"],
        "commit": manifest["commit"],
        "mode": mode,
        "labels": labels,
        "evidence": evidence,
        "excluded_evidence": excluded_evidence,
        "rule_catalog_hash": rules_hash,
        "snapshot_hash": sha256((snapshot / "manifest.json").read_bytes()),
        "scan_complete": complete,
        "analysis_errors": analysis_errors,
        "eligible_files": len(eligible),
        "captured_files": sum(item["status"] == "captured" for item in eligible),
        "unavailable_files": len(unavailable),
        "inventory_complete": manifest["inventory_complete"],
        "interpretation": "candidate; absence of a match is not proof of absence of an activity",
    }
