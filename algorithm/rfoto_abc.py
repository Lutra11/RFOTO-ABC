"""Proposed RFOTO-ABC optimizer.

This thin module exists for repository readability. The complete implementation
is kept in ``rfoto_core.py`` so that the proposed method, classical baselines,
and rule baselines share exactly the same scenario evaluator and decoder.
"""

from __future__ import annotations

from .rfoto_core import AlgorithmConfig, RunResult, run_rfoto_abc

__all__ = ["AlgorithmConfig", "RunResult", "run_rfoto_abc"]
