"""Rule-based baselines for the RFOTO-ABC MEC scenario."""

from __future__ import annotations

from .registry import RULE_BASELINES
from .rfoto_core import RunResult, run_rule

__all__ = ["RULE_BASELINES", "RunResult", "run_rule"]
