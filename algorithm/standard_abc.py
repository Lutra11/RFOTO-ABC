"""Standard ABC baseline used in the RFOTO-ABC experiments."""

from __future__ import annotations

from .rfoto_core import AlgorithmConfig, RunResult, run_rfoto_abc


def run_standard_abc(s: dict, budget: int, seed: int) -> RunResult:
    """Run a plain ABC baseline under the RFOTO random-key decoder."""
    cfg = AlgorithmConfig(
        reliability_guidance=False,
        fairness_guidance=False,
        greedy_initialization=False,
        directed_scout=False,
    )
    return run_rfoto_abc(s, budget, seed, cfg=cfg, algorithm="Standard-ABC")


__all__ = ["run_standard_abc"]
