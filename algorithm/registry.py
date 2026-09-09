#!/usr/bin/env python3
"""Common algorithm registry for RFOTO-ABC experiments."""

from __future__ import annotations

try:
    from .advanced_metaheuristics import ADVANCED_ALGORITHMS, run_advanced_algorithm
    from .rfoto_core import (
        AlgorithmConfig,
        RunResult,
        run_de,
        run_ga,
        run_pso,
        run_rfoto_abc,
        run_rule,
    )
except ImportError:
    from advanced_metaheuristics import ADVANCED_ALGORITHMS, run_advanced_algorithm  # type: ignore
    from rfoto_core import (  # type: ignore
        AlgorithmConfig,
        RunResult,
        run_de,
        run_ga,
        run_pso,
        run_rfoto_abc,
        run_rule,
    )


CLASSIC_METAHEURISTICS = ["GA", "PSO", "DE"]
RULE_BASELINES = ["Local-only", "Random-feasible", "Max-SINR", "Delay-Greedy", "Load-Aware", "Offload-then-Allocate"]
ABC_FAMILY = ["RFOTO-ABC", "Standard-ABC", "Gbest-ABC", "MeABC"]
ALL_ALGORITHMS = ["RFOTO-ABC", "Standard-ABC"] + CLASSIC_METAHEURISTICS + ADVANCED_ALGORITHMS + RULE_BASELINES


def run_algorithm(name: str, scenario: dict, budget: int, seed: int) -> RunResult:
    """Run an algorithm under the shared RFOTO scenario evaluator."""
    if name == "RFOTO-ABC":
        return run_rfoto_abc(scenario, budget, seed, algorithm=name)
    if name == "Standard-ABC":
        cfg = AlgorithmConfig(
            reliability_guidance=False,
            fairness_guidance=False,
            greedy_initialization=False,
            directed_scout=False,
        )
        return run_rfoto_abc(scenario, budget, seed, cfg=cfg, algorithm=name)
    if name == "GA":
        return run_ga(scenario, budget, seed)
    if name == "PSO":
        return run_pso(scenario, budget, seed)
    if name == "DE":
        return run_de(scenario, budget, seed)
    if name in ADVANCED_ALGORITHMS:
        return run_advanced_algorithm(name, scenario, budget, seed)
    if name in RULE_BASELINES:
        return run_rule(scenario, name, seed)
    raise ValueError(f"Unknown algorithm: {name}")
