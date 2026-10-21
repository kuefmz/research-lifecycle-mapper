"""Candidate conjunctive rules; evidence modes are isolated before aggregation."""

import ast
import io
import json
import re
import tokenize
import warnings
from itertools import accumulate
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import quote

from . import MODES, STAGES
from .acquisition import replay
from .canonical import json_bytes, sha256, physical_lines
from .documentation import documentation_matches, document_units, workflow_units
from .notebooks import expand_notebooks
from .telemetry import emit
from .legacy_python import modernize_syntax
from .brace_code import BRACE_SUFFIXES, lexical_view, executable_blocks
from .portable_code import matches as portable_matches


def default_rules() -> Path:
    return Path(__file__).with_name("rules")


def load_rules(directory: Path | None = None) -> tuple[list[dict[str, Any]], str]:
    directory = directory or default_rules()
    rules = []
    for stage in STAGES:
        catalog = json.loads((directory / f"{stage.lower()}.yaml").read_bytes())
        if (
            catalog["version"]
            not in {
                "0.1.0-candidate",
                "0.2.0-candidate",
                "0.3.0-candidate",
                "0.4.0-candidate",
                "0.5.0-development",
                "0.5.1-development",
                "0.5.2-development",
                "0.5.3-development",
                "0.5.4-development",
            }
            or catalog["stage"] != stage
        ):
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
        if rule["source"] == "documentation" and rule.get("layer") not in {
            "explicit",
            "contextual",
            "workflow",
        }:
            raise ValueError("Documentation rules require an explicit detector layer")
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


_PARSE_LOCK = Lock()


def parse_python(text: str, path: str) -> ast.Module:
    """Ignore only invalid-escape warnings from inspected string literals.

    Those strings are masked by the detector. Syntax errors still propagate and
    other warning categories/messages retain their normal behavior.
    """
    with _PARSE_LOCK, warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", message=r"invalid escape sequence", category=SyntaxWarning
        )
        try:
            syntax = ast.parse(text, filename=path)
            setattr(syntax, "_lifecycle_syntax", "python3-native")
            return syntax
        except SyntaxError:
            converted = modernize_syntax(text)
            if converted is None:
                raise
            syntax = ast.parse(converted, filename=path)
            setattr(syntax, "_lifecycle_syntax", "python2-syntax-compatibility; line-preserving")
            return syntax


def implementation_view(text: str, path: str) -> str:
    """Mask Python comments and docstrings while retaining exact source line positions.

    Python uses AST/tokenization; R, Julia, MATLAB and shell use lexical masking.
    Other source languages remain inventoried without rule coverage.
    Never execute inspected repository code.
    """
    suffix = Path(path).suffix.lower()
    if suffix in BRACE_SUFFIXES:
        return lexical_view(text, suffix)
    if suffix in {".r", ".jl", ".m", ".sh"}:
        # Lexical, not semantic parsing. Preserve every physical newline exactly.
        comment = r"%[^\n]*" if suffix == ".m" else r"\#[^\n]*"
        lexical_pattern = r"\"\"\"[\s\S]*?\"\"\"|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|" + comment
        return re.sub(lexical_pattern, lambda m: re.sub(r"[^\r\n]", " ", m.group()), text)
    if suffix != ".py":
        return ""
    parse_python(text, path)
    lines = physical_lines(text, keepends=True)
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
    snapshot: Path,
    mode: str,
    rules_dir: Path | None = None,
    expected_hash: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}")
    manifest, contents = replay(snapshot, expected_hash)
    emit(phase="notebook-parsing")
    manifest, contents = expand_notebooks(manifest, contents)
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
    source_scans = []
    source_warnings: list[dict[str, Any]] = []
    portable_rules = [r for r in rules if r.get("detector") == "portable-lexical-v1"]
    for item in manifest["files"]:
        source = item["source"]
        if item["status"] != "captured" or source not in permitted:
            continue
        if portable_rules and source == "code":
            emit(
                phase="analysis-tokenization",
                current_file=item.get("notebook_path", item["path"]),
                current_cell=item.get("notebook_cell"),
                current_file_bytes=item.get("size"),
            )
            portable, scan = portable_matches(contents[item["path"]], item["path"], portable_rules)
            source_scans.append(
                {
                    "path": item.get("notebook_path", item["path"]),
                    "notebook_cell": item.get("notebook_cell"),
                    "notebook_language": item.get("notebook_language"),
                    "native_policy": "not-applied",
                    **scan,
                }
            )
            if scan.get("coverage_gap"):
                analysis_errors.append({"path": item["path"], "reason": scan["coverage_gap"]})
            if scan.get("error_tokens") or scan.get("lexer_failure"):
                source_warnings.append(
                    {
                        "path": item["path"],
                        "reason": "lexical-token-warning",
                        "error_tokens": scan.get("error_tokens", 0),
                        "lexer_failure": scan.get("lexer_failure"),
                    }
                )
            for finding in portable:
                reasons = finding.pop("exclusion_reasons")
                if unit_test_path(item["path"]):
                    reasons.append("software-test-path")
                record = {
                    "repository": manifest["repository"],
                    "commit": manifest["commit"],
                    "path": item["path"],
                    "content_sha256": item["sha256"],
                    **finding,
                    "url": f"{manifest['source_url']}/blob/{manifest['commit']}/{quote(item['path'], safe='/')}#L{finding['start_line']}-L{finding['end_line']}",
                }
                if reasons:
                    excluded_evidence.append({**record, "exclusion_reasons": reasons})
                else:
                    evidence.append(record)
        emit(
            phase="analysis",
            current_file=item.get("notebook_path", item["path"]),
            current_cell=item.get("notebook_cell"),
            current_source=source,
            current_file_bytes=item.get("size"),
        )
        original_lines = physical_lines(contents[item["path"]], keepends=True)
        if source == "documentation":
            units = document_units(contents[item["path"]])
            extended_units = (
                workflow_units(contents[item["path"]])
                if any(r.get("unit_policy") == "documented-workflow-v5" for r in rules)
                else None
            )
            for rule in rules:
                if rule["source"] != source:
                    continue
                for match in documentation_matches(
                    contents[item["path"]],
                    rule,
                    extended_units
                    if rule.get("unit_policy") == "documented-workflow-v5"
                    else units,
                ):
                    reasons = match.pop("exclusion_reasons")
                    record = {
                        "repository": manifest["repository"],
                        "commit": manifest["commit"],
                        "stage": rule["stage"],
                        "source": source,
                        "rule_id": rule["id"],
                        "rule_version": rule["version"],
                        "path": item["path"],
                        "content_sha256": item["sha256"],
                        **match,
                        "url": f"{manifest['source_url']}/blob/{manifest['commit']}/{quote(item['path'], safe='/')}#L{match['start_line']}-L{match['end_line']}",
                    }
                    if reasons:
                        excluded_evidence.append({**record, "exclusion_reasons": reasons})
                    else:
                        evidence.append(record)
            continue
        brace_supported = Path(item["path"]).suffix.lower() in BRACE_SUFFIXES and any(
            r.get("detector") == "brace-lexical-v1"
            and Path(item["path"]).suffix.lower() in r.get("extensions", [])
            for r in rules
        )
        if (
            source == "code"
            and Path(item["path"]).suffix.lower() not in {".py", ".r", ".jl", ".m", ".sh"}
            and not brace_supported
            and contents[item["path"]].strip()
        ):
            if not portable_rules:
                analysis_errors.append(
                    {"path": item["path"], "reason": "unsupported-source-language"}
                )
            continue
        try:
            view = (
                implementation_view(contents[item["path"]], item["path"])
                if source == "code"
                else contents[item["path"]]
            )
            blocks = executable_blocks(view) if brace_supported else []
        except (SyntaxError, tokenize.TokenError, IndentationError) as exc:
            (source_warnings if portable_rules else analysis_errors).append(
                {
                    "path": item["path"],
                    "reason": "python-parse-error",
                    "line": getattr(exc, "lineno", None),
                }
            )
            continue
        except ValueError as exc:
            (source_warnings if portable_rules else analysis_errors).append(
                {"path": item["path"], "reason": "brace-lexical-error", "detail": str(exc)}
            )
            continue
        lines = physical_lines(view, keepends=True)
        line_offsets = [0, *accumulate(len(line) for line in lines)]
        function_spans = []
        statement_spans = []
        syntax_policy = "brace-lexical-v1" if brace_supported else "lexical"
        if source == "code" and Path(item["path"]).suffix.lower() == ".py":
            syntax = parse_python(contents[item["path"]], item["path"])
            syntax_policy = getattr(syntax, "_lifecycle_syntax", "python3-native")
            statement_spans = [
                (node.lineno, node.end_lineno or node.lineno)
                for node in ast.walk(syntax)
                if isinstance(node, ast.stmt)
                and not isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                        ast.If,
                        ast.For,
                        ast.While,
                        ast.Try,
                        ast.With,
                    ),
                )
            ]
            function_spans = [
                (node.lineno, node.end_lineno or node.lineno)
                for node in ast.walk(syntax)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
        if portable_rules:
            source_scans[-1]["native_policy"] = syntax_policy
        for rule in rules:
            if rule["source"] != source:
                continue
            if rule.get("detector") == "portable-lexical-v1":
                continue
            if (
                rule.get("extensions")
                and Path(item["path"]).suffix.lower() not in rule["extensions"]
            ):
                continue
            if not rule.get("extensions") and Path(item["path"]).suffix.lower() != ".py":
                continue
            if not all(re.search(pattern, view, re.I | re.M) for pattern in rule["positive"]):
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
                if (
                    source == "code"
                    and Path(item["path"]).suffix.lower() == ".py"
                    and rule.get("scope") != "statement"
                    and not any(
                        left == start_line and end_line <= right for left, right in function_spans
                    )
                ):
                    continue
                context = None
                if rule.get("detector") == "brace-lexical-v1":
                    contexts = [
                        block
                        for block in blocks
                        if int(block["start_line"])
                        <= start_line
                        <= end_line
                        <= int(block["end_line"])
                        and int(block["body_start"]) <= line_offsets[offset] + start
                        and line_offsets[offset] + end <= int(block["body_end"])
                        and (
                            not rule.get("context_pattern")
                            or re.search(rule["context_pattern"], str(block["header"]), re.I)
                        )
                    ]
                    if not contexts:
                        continue
                    context = min(contexts, key=lambda b: int(b["end_line"]) - int(b["start_line"]))
                if (
                    Path(item["path"]).suffix.lower() == ".py"
                    and rule.get("scope") == "statement"
                    and not any(
                        left <= start_line <= end_line <= right for left, right in statement_spans
                    )
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
                    "code_syntax_policy": syntax_policy,
                    **({"code_context": context} if context is not None else {}),
                    "rule_id": rule["id"],
                    "rule_version": rule["version"],
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

    cell_items = {item["path"]: item for item in manifest["files"] if "notebook_path" in item}
    for record in evidence + excluded_evidence:
        item = cell_items.get(record["path"])
        if item is not None:
            record.update(
                path=item["notebook_path"],
                notebook_cell=item["notebook_cell"],
                notebook_cell_type=item["notebook_cell_type"],
                notebook_language=item["notebook_language"],
                line_scope="notebook-cell",
                url=f"{manifest['source_url']}/blob/{manifest['commit']}/{quote(item['notebook_path'], safe='/')}",
            )

    def order(record: dict[str, Any]) -> tuple[Any, ...]:
        return (
            STAGES.index(record["stage"]),
            record["path"],
            record["rule_id"],
            record["start_line"],
            record["end_line"],
        )

    snapshot_hash = sha256((snapshot / "manifest.json").read_bytes())
    run_id = run_id or sha256(json_bytes([snapshot_hash, rules_hash, mode]))
    # One occurrence per stage/source/file/physical span/excerpt. All matching
    # rule attributions survive; overlaps with different spans are not collapsed.
    unique: dict[str, dict[str, Any]] = {}
    for record in evidence:
        occurrence_id = sha256(
            json_bytes(
                [
                    record["repository"].casefold(),
                    record["commit"],
                    record["stage"],
                    record["source"],
                    record["path"],
                    record.get("notebook_cell"),
                    record["start_line"],
                    record["end_line"],
                    record["excerpt"],
                ]
            )
        )
        attribution = {"id": record["rule_id"], "version": record["rule_version"]}
        if record["source"] == "code":
            attribution["code_syntax_policy"] = record["code_syntax_policy"]
            if record.get("code_context"):
                attribution["code_context"] = record["code_context"]
        if occurrence_id in unique:
            if attribution not in unique[occurrence_id]["matched_rules"]:
                unique[occurrence_id]["matched_rules"].append(attribution)
        else:
            unique[occurrence_id] = {
                **record,
                "evidence_id": occurrence_id,
                "run_id": run_id,
                "repository_url": manifest["source_url"],
                "rule_catalog_hash": rules_hash,
                "matched_rules": [attribution],
                "strength": "conjunctive-rule-match; not a probability",
            }
    evidence = list(unique.values())
    for record in excluded_evidence:
        record.update(
            run_id=run_id, repository_url=manifest["source_url"], rule_catalog_hash=rules_hash
        )
    evidence.sort(key=order)
    excluded_evidence.sort(key=order)
    labels = [stage for stage in STAGES if any(record["stage"] == stage for record in evidence)]
    eligible = [item for item in manifest["files"] if item["source"] in permitted]
    unavailable = [item for item in eligible if item["status"] == "unavailable"]
    complete = manifest["inventory_complete"] is True and not unavailable and not analysis_errors
    return {
        "repository": manifest["repository"],
        "repository_url": manifest["source_url"],
        "run_id": run_id,
        "commit": manifest["commit"],
        "mode": mode,
        "predictions": {
            stage: True if stage in labels else False if complete else None for stage in STAGES
        },
        "evidence_counts": {
            stage: {
                "documentation": sum(
                    e["stage"] == stage and e["source"] == "documentation" for e in evidence
                ),
                "code": sum(e["stage"] == stage and e["source"] == "code" for e in evidence),
                "overall": sum(e["stage"] == stage for e in evidence),
            }
            for stage in STAGES
        },
        "labels": labels,
        "evidence": evidence,
        "excluded_evidence": excluded_evidence,
        "rule_catalog_hash": rules_hash,
        "snapshot_hash": sha256((snapshot / "manifest.json").read_bytes()),
        "scan_complete": complete,
        "analysis_errors": analysis_errors,
        "source_scans": source_scans,
        "source_warnings": source_warnings,
        "text_decodings": [
            {"path": item["path"], "encoding": item["text_encoding"]}
            for item in eligible
            if item.get("text_encoding") == "windows-1252"
        ],
        "eligible_files": len(eligible),
        "captured_files": sum(item["status"] == "captured" for item in eligible),
        "coverage_issues": [
            {"path": item["path"], "reason": item.get("reason") or "unavailable-artifact"}
            for item in unavailable
        ],
        "unavailable_files": len(unavailable),
        "inventory_complete": manifest["inventory_complete"],
        "interpretation": "candidate; absence of a match is not proof of absence of an activity",
    }


def analyze_modes(
    snapshot: Path,
    modes: tuple[str, ...],
    expected_hash: str | None = None,
    rules_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Match each source once, projecting identical per-mode evidence and IDs."""
    from copy import deepcopy

    if not modes or any(mode not in MODES for mode in modes):
        raise ValueError("Supply valid prediction modes")
    if len(modes) == 1:
        return [analyze(snapshot, modes[0], rules_dir=rules_dir, expected_hash=expected_hash)]
    combined = analyze(snapshot, "combined", rules_dir=rules_dir, expected_hash=expected_hash)
    manifest, contents = replay(snapshot, expected_hash)
    manifest, contents = expand_notebooks(manifest, contents)
    results = []
    for mode in modes:
        if mode == "combined":
            results.append(combined)
            continue
        source = "documentation" if mode == "documentation-only" else "code"
        run_id = sha256(
            json_bytes([combined["snapshot_hash"], combined["rule_catalog_hash"], mode])
        )
        evidence = deepcopy([e for e in combined["evidence"] if e["source"] == source])
        excluded = deepcopy([e for e in combined["excluded_evidence"] if e["source"] == source])
        for record in evidence + excluded:
            record["run_id"] = run_id
        eligible = [f for f in manifest["files"] if f["source"] == source]
        unavailable = [f for f in eligible if f["status"] == "unavailable"]
        errors = combined["analysis_errors"] if source == "code" else []
        complete = manifest["inventory_complete"] is True and not unavailable and not errors
        labels = [s for s in STAGES if any(e["stage"] == s for e in evidence)]
        results.append(
            {
                **combined,
                "run_id": run_id,
                "mode": mode,
                "predictions": {
                    stage: True if stage in labels else False if complete else None
                    for stage in STAGES
                },
                "evidence_counts": {
                    stage: {
                        "documentation": sum(
                            e["stage"] == stage and e["source"] == "documentation" for e in evidence
                        ),
                        "code": sum(
                            e["stage"] == stage and e["source"] == "code" for e in evidence
                        ),
                        "overall": sum(e["stage"] == stage for e in evidence),
                    }
                    for stage in STAGES
                },
                "labels": labels,
                "evidence": evidence,
                "excluded_evidence": excluded,
                "scan_complete": complete,
                "analysis_errors": errors,
                "source_scans": combined["source_scans"] if source == "code" else [],
                "source_warnings": combined["source_warnings"] if source == "code" else [],
                "text_decodings": [
                    {"path": item["path"], "encoding": item["text_encoding"]}
                    for item in eligible
                    if item.get("text_encoding") == "windows-1252"
                ],
                "eligible_files": len(eligible),
                "captured_files": sum(f["status"] == "captured" for f in eligible),
                "coverage_issues": [
                    {"path": item["path"], "reason": item.get("reason") or "unavailable-artifact"}
                    for item in unavailable
                ],
                "unavailable_files": len(unavailable),
            }
        )
    return results
