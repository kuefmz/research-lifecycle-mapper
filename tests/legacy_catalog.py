"""Explicit historical catalog for regression tests written before the final default.

These helpers do not patch production defaults. Final-profile tests call production APIs.
"""

from pathlib import Path
from typing import Any
from lifecycle_mapper import analysis

BASELINE = Path(__file__).resolve().parents[1] / "tests/fixtures/legacy-profiles/packaged-default"


def default_rules() -> Path:
    return BASELINE


def load_rules(directory: Path | None = None) -> Any:
    return analysis.load_rules(directory or BASELINE)


def analyze(*args: Any, **kwargs: Any) -> Any:
    kwargs.setdefault("rules_dir", BASELINE)
    return analysis.analyze(*args, **kwargs)


def analyze_modes(*args: Any, **kwargs: Any) -> Any:
    kwargs.setdefault("rules_dir", BASELINE)
    return analysis.analyze_modes(*args, **kwargs)
