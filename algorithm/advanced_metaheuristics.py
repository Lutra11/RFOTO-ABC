#!/usr/bin/env python3
"""Advanced metaheuristic baselines for the RFOTO-ABC scenario model.

The algorithms in this module share the RFOTO-ABC random-key representation:

    z = [assignment_key, bandwidth_key, cpu_key]

where the first ``n`` variables are mapped to discrete execution locations and
the remaining variables are decoded into bandwidth/CPU allocation priorities.
All methods call the same RFOTO decoder and objective evaluator, so differences
come from the search strategy rather than from the constraint handling.

Implemented baselines:

* Gbest-ABC      -- global-best-guided artificial bee colony.
* MeABC         -- memetic ABC with local refinement around the best solution.
* JADE          -- adaptive differential evolution current-to-pbest variant.
* LSHADE-lite   -- success-history DE with simple linear population reduction.
* CMAES-lite    -- diagonal covariance evolution strategy for random keys.
* GWO           -- grey wolf optimizer adapted to the RFOTO random-key space.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable

import numpy as np

try:  # Package import when used from git-content.
    from .rfoto_core import (
        Candidate,
        DecodedSolution,
        RunResult,
        decode_candidate,
        decode_vector,
        encode_candidate,
        greedy_candidate,
        random_candidate,
    )
except ImportError:  # Direct script/debug import.
    from rfoto_core import (  # type: ignore
        Candidate,
        DecodedSolution,
        RunResult,
        decode_candidate,
        decode_vector,
        encode_candidate,
        greedy_candidate,
        random_candidate,
    )


ADVANCED_ALGORITHMS = [
    "Gbest-ABC",
    "MeABC",
    "JADE",
    "LSHADE-lite",
    "CMAES-lite",
    "GWO",
]


@dataclass
class EvalRecord:
    z: np.ndarray
    candidate: Candidate
    solution: DecodedSolution

    @property
    def objective(self) -> float:
        return self.solution.objective


def _bounds(s: dict) -> tuple[np.ndarray, np.ndarray]:
    n = s["n"]
    lower = np.concatenate([np.zeros(n), -np.ones(2 * n)])
    upper = np.concatenate([np.full(n, 0.999999), np.ones(2 * n)])
    return lower, upper


def _clip(z: np.ndarray, s: dict) -> np.ndarray:
    lower, upper = _bounds(s)
    return np.minimum(np.maximum(z, lower), upper)


def _random_vector(s: dict, rng: np.random.Generator) -> np.ndarray:
    c = random_candidate(s, rng)
    return _clip(encode_candidate(c, s["m"]), s)


def _greedy_vector(s: dict) -> np.ndarray:
    return _clip(encode_candidate(greedy_candidate(s, "load"), s["m"]), s)


def _key_jitter(
    z: np.ndarray,
    s: dict,
    rng: np.random.Generator,
    assignment_prob: float = 0.04,
    resource_prob: float = 0.04,
    resource_sigma: float = 0.22,
) -> np.ndarray:
    """Add random-key perturbations that can cross discrete assignment bins."""
    out = z.copy()
    n = s["n"]
    assign_mask = rng.random(n) < assignment_prob
    if np.any(assign_mask):
        out[:n][assign_mask] = rng.random(np.sum(assign_mask))
    resource_mask = rng.random(2 * n) < resource_prob
    if np.any(resource_mask):
        out[n:][resource_mask] += rng.normal(0.0, resource_sigma, np.sum(resource_mask))
    return _clip(out, s)


def _evaluate(s: dict, z: np.ndarray) -> EvalRecord:
    z = _clip(z, s)
    candidate = decode_vector(z, s)
    solution = decode_candidate(s, candidate)
    return EvalRecord(z, candidate, solution)


def _init_population(s: dict, rng: np.random.Generator, pop_size: int) -> list[EvalRecord]:
    greedy = _greedy_vector(s)
    pop = [_evaluate(s, greedy)]
    seeded = max(1, int(0.35 * pop_size))
    while len(pop) < seeded:
        z = _key_jitter(greedy, s, rng, assignment_prob=0.08, resource_prob=0.18, resource_sigma=0.35)
        pop.append(_evaluate(s, z))
    while len(pop) < pop_size:
        pop.append(_evaluate(s, _random_vector(s, rng)))
    return pop


def _best(pop: list[EvalRecord]) -> EvalRecord:
    return min(pop, key=lambda item: item.objective)


def _trace_append(trace_fe: list[int], trace_obj: list[float], fe: int, obj: float) -> None:
    if not trace_fe or fe == 1 or fe - trace_fe[-1] >= 5:
        trace_fe.append(int(fe))
        trace_obj.append(float(obj))


def _result(name: str, best: EvalRecord, trace_fe: list[int], trace_obj: list[float], fe: int, started: float) -> RunResult:
    return RunResult(
        name,
        best.candidate.copy(),
        best.solution,
        np.asarray(trace_fe, dtype=int),
        np.asarray(trace_obj, dtype=float),
        int(fe),
        time.perf_counter() - started,
    )


def _distinct_indices(rng: np.random.Generator, size: int, exclude: set[int], count: int) -> list[int]:
    pool = [idx for idx in range(size) if idx not in exclude]
    if len(pool) < count:
        pool = list(range(size))
    return list(rng.choice(pool, count, replace=False))


def run_gbest_abc(s: dict, budget: int, seed: int, pop_size: int = 16, limit: int = 30) -> RunResult:
    rng = np.random.default_rng(seed)
    started = time.perf_counter()
    pop_size = max(4, min(pop_size, budget))
    pop = _init_population(s, rng, pop_size)
    fe = len(pop)
    trials = np.zeros(pop_size, dtype=int)
    gbest = _best(pop)
    trace_fe, trace_obj = [fe], [gbest.objective]
    lower, upper = _bounds(s)
    span = upper - lower

    while fe < budget:
        for i in range(pop_size):
            if fe >= budget:
                break
            k = _distinct_indices(rng, pop_size, {i}, 1)[0]
            phi = rng.uniform(-1.0, 1.0, size=len(pop[i].z))
            psi = rng.uniform(0.0, 0.55, size=len(pop[i].z))
            trial_z = pop[i].z + phi * (pop[i].z - pop[k].z) + psi * (gbest.z - pop[i].z)
            trial_z = _key_jitter(trial_z, s, rng, assignment_prob=0.025, resource_prob=0.035, resource_sigma=0.20)
            if rng.random() < 0.12:
                trial_z += rng.normal(0.0, 0.05, size=len(trial_z)) * span
            trial = _evaluate(s, trial_z)
            fe += 1
            if trial.objective < pop[i].objective:
                pop[i] = trial
                trials[i] = 0
                if trial.objective < gbest.objective:
                    gbest = trial
            else:
                trials[i] += 1
            if trials[i] >= limit and fe < budget:
                restart_z = gbest.z + rng.normal(0.0, 0.18, size=len(gbest.z)) * span
                if rng.random() < 0.35:
                    restart_z = _random_vector(s, rng)
                pop[i] = _evaluate(s, restart_z)
                fe += 1
                trials[i] = 0
                if pop[i].objective < gbest.objective:
                    gbest = pop[i]
            _trace_append(trace_fe, trace_obj, fe, gbest.objective)
    return _result("Gbest-ABC", gbest, trace_fe, trace_obj, fe, started)


def run_meabc(s: dict, budget: int, seed: int, pop_size: int = 16, limit: int = 26) -> RunResult:
    rng = np.random.default_rng(seed)
    started = time.perf_counter()
    pop_size = max(4, min(pop_size, budget))
    pop = _init_population(s, rng, pop_size)
    fe = len(pop)
    trials = np.zeros(pop_size, dtype=int)
    best = _best(pop)
    trace_fe, trace_obj = [fe], [best.objective]
    lower, upper = _bounds(s)
    span = upper - lower

    while fe < budget:
        for i in range(pop_size):
            if fe >= budget:
                break
            a, b = _distinct_indices(rng, pop_size, {i}, 2)
            phi = rng.uniform(-0.75, 0.75, size=len(pop[i].z))
            trial_z = pop[i].z + phi * (pop[a].z - pop[b].z) + 0.35 * rng.random(len(pop[i].z)) * (best.z - pop[i].z)
            trial_z = _key_jitter(trial_z, s, rng, assignment_prob=0.025, resource_prob=0.04, resource_sigma=0.20)
            trial = _evaluate(s, trial_z)
            fe += 1
            if trial.objective < pop[i].objective:
                pop[i] = trial
                trials[i] = 0
            else:
                trials[i] += 1

            if pop[i].objective < best.objective:
                best = pop[i]

            if fe < budget and (fe % max(5, pop_size // 2) == 0):
                sigma = max(0.012, 0.20 * (1.0 - fe / max(budget, 1)))
                local_z = best.z + rng.normal(0.0, sigma, size=len(best.z)) * span
                local_z = _key_jitter(local_z, s, rng, assignment_prob=0.015, resource_prob=0.04, resource_sigma=0.16)
                local = _evaluate(s, local_z)
                fe += 1
                worst = int(np.argmax([item.objective for item in pop]))
                if local.objective < pop[worst].objective:
                    pop[worst] = local
                if local.objective < best.objective:
                    best = local

            if trials[i] >= limit and fe < budget:
                pop[i] = _evaluate(s, _random_vector(s, rng))
                fe += 1
                trials[i] = 0
                if pop[i].objective < best.objective:
                    best = pop[i]
            _trace_append(trace_fe, trace_obj, fe, best.objective)
    return _result("MeABC", best, trace_fe, trace_obj, fe, started)


def _sample_f(rng: np.random.Generator, mean_f: float) -> float:
    for _ in range(20):
        value = mean_f + 0.10 * rng.standard_cauchy()
        if value > 0:
            return float(min(value, 1.0))
    return 0.5


def _sample_cr(rng: np.random.Generator, mean_cr: float) -> float:
    return float(np.clip(rng.normal(mean_cr, 0.10), 0.0, 1.0))


def run_jade(s: dict, budget: int, seed: int, pop_size: int = 20, p: float = 0.20) -> RunResult:
    rng = np.random.default_rng(seed)
    started = time.perf_counter()
    pop_size = max(6, min(pop_size, budget))
    pop = _init_population(s, rng, pop_size)
    archive: list[np.ndarray] = []
    fe = len(pop)
    best = _best(pop)
    trace_fe, trace_obj = [fe], [best.objective]
    mean_f = 0.50
    mean_cr = 0.50

    while fe < budget:
        improvements_f: list[float] = []
        improvements_cr: list[float] = []
        order = np.argsort([item.objective for item in pop])
        top_count = max(2, int(math.ceil(p * len(pop))))
        for i in range(len(pop)):
            if fe >= budget:
                break
            f = _sample_f(rng, mean_f)
            cr = _sample_cr(rng, mean_cr)
            pbest = pop[int(rng.choice(order[:top_count]))].z
            r1_idx = _distinct_indices(rng, len(pop), {i}, 1)[0]
            combined = [item.z for item in pop] + archive
            r2_pool = [idx for idx in range(len(combined)) if not (idx == i or idx == r1_idx)]
            r2 = combined[int(rng.choice(r2_pool))]
            mutant = pop[i].z + f * (pbest - pop[i].z) + f * (pop[r1_idx].z - r2)
            mutant = _key_jitter(mutant, s, rng, assignment_prob=0.02, resource_prob=0.035, resource_sigma=0.18)
            cross = rng.random(len(mutant)) < cr
            cross[int(rng.integers(0, len(mutant)))] = True
            trial_z = np.where(cross, mutant, pop[i].z)
            trial = _evaluate(s, trial_z)
            fe += 1
            if trial.objective < pop[i].objective:
                archive.append(pop[i].z.copy())
                pop[i] = trial
                improvements_f.append(f)
                improvements_cr.append(cr)
                if trial.objective < best.objective:
                    best = trial
            _trace_append(trace_fe, trace_obj, fe, best.objective)
        if len(archive) > len(pop):
            keep = rng.choice(len(archive), len(pop), replace=False)
            archive = [archive[int(idx)] for idx in keep]
        if improvements_f:
            sf = np.asarray(improvements_f)
            scr = np.asarray(improvements_cr)
            mean_f = 0.90 * mean_f + 0.10 * float(np.sum(sf * sf) / max(np.sum(sf), 1e-12))
            mean_cr = 0.90 * mean_cr + 0.10 * float(np.mean(scr))
    return _result("JADE", best, trace_fe, trace_obj, fe, started)


def run_lshade_lite(s: dict, budget: int, seed: int, pop_size: int = 24, memory_size: int = 5) -> RunResult:
    rng = np.random.default_rng(seed)
    started = time.perf_counter()
    max_pop = max(8, min(pop_size, budget))
    min_pop = 6
    pop = _init_population(s, rng, max_pop)
    archive: list[np.ndarray] = []
    fe = len(pop)
    best = _best(pop)
    trace_fe, trace_obj = [fe], [best.objective]
    mem_f = np.full(memory_size, 0.50)
    mem_cr = np.full(memory_size, 0.50)
    mem_pos = 0

    while fe < budget and len(pop) >= min_pop:
        success_f: list[float] = []
        success_cr: list[float] = []
        improvements: list[float] = []
        order = np.argsort([item.objective for item in pop])
        top_count = max(2, int(math.ceil(0.15 * len(pop))))
        for i in range(len(pop)):
            if fe >= budget:
                break
            mem_idx = int(rng.integers(0, memory_size))
            f = _sample_f(rng, mem_f[mem_idx])
            cr = _sample_cr(rng, mem_cr[mem_idx])
            pbest = pop[int(rng.choice(order[:top_count]))].z
            r1_idx = _distinct_indices(rng, len(pop), {i}, 1)[0]
            combined = [item.z for item in pop] + archive
            r2_pool = [idx for idx in range(len(combined)) if idx not in {i, r1_idx}]
            r2 = combined[int(rng.choice(r2_pool))]
            mutant = pop[i].z + f * (pbest - pop[i].z) + f * (pop[r1_idx].z - r2)
            mutant = _key_jitter(mutant, s, rng, assignment_prob=0.02, resource_prob=0.035, resource_sigma=0.18)
            cross = rng.random(len(mutant)) < cr
            cross[int(rng.integers(0, len(mutant)))] = True
            trial = _evaluate(s, np.where(cross, mutant, pop[i].z))
            fe += 1
            if trial.objective < pop[i].objective:
                improvement = pop[i].objective - trial.objective
                archive.append(pop[i].z.copy())
                pop[i] = trial
                success_f.append(f)
                success_cr.append(cr)
                improvements.append(improvement)
                if trial.objective < best.objective:
                    best = trial
            _trace_append(trace_fe, trace_obj, fe, best.objective)

        if success_f:
            w = np.asarray(improvements, dtype=float)
            w = w / max(np.sum(w), 1e-12)
            sf = np.asarray(success_f)
            scr = np.asarray(success_cr)
            mem_f[mem_pos] = float(np.sum(w * sf * sf) / max(np.sum(w * sf), 1e-12))
            mem_cr[mem_pos] = float(np.sum(w * scr))
            mem_pos = (mem_pos + 1) % memory_size

        if len(archive) > len(pop):
            keep = rng.choice(len(archive), len(pop), replace=False)
            archive = [archive[int(idx)] for idx in keep]

        target_size = int(round(max_pop - (max_pop - min_pop) * fe / max(budget, 1)))
        target_size = max(min_pop, min(max_pop, target_size))
        while len(pop) > target_size:
            worst = int(np.argmax([item.objective for item in pop]))
            pop.pop(worst)
    return _result("LSHADE-lite", best, trace_fe, trace_obj, fe, started)


def run_cmaes_lite(s: dict, budget: int, seed: int, pop_size: int = 18) -> RunResult:
    rng = np.random.default_rng(seed)
    started = time.perf_counter()
    lower, upper = _bounds(s)
    span = upper - lower
    dim = len(lower)
    lam = max(6, min(pop_size, budget))
    mu = max(3, lam // 2)
    weights = np.log(mu + 0.5) - np.log(np.arange(1, mu + 1))
    weights = weights / weights.sum()
    mean = _greedy_vector(s)
    diag = np.ones(dim)
    sigma = 0.28
    best = _evaluate(s, mean)
    fe = 1
    trace_fe, trace_obj = [fe], [best.objective]
    no_improve = 0

    while fe < budget:
        samples = []
        for _ in range(min(lam, budget - fe)):
            eps = rng.normal(0.0, 1.0, dim)
            z = mean + sigma * eps * np.sqrt(diag) * span
            z = _key_jitter(z, s, rng, assignment_prob=0.018, resource_prob=0.035, resource_sigma=0.18)
            rec = _evaluate(s, z)
            samples.append((rec, eps))
            fe += 1
            if rec.objective < best.objective:
                best = rec
                no_improve = 0
            _trace_append(trace_fe, trace_obj, fe, best.objective)
        if not samples:
            break
        samples.sort(key=lambda item: item[0].objective)
        elite = samples[: min(mu, len(samples))]
        elite_weights = weights[: len(elite)]
        elite_weights = elite_weights / elite_weights.sum()
        old_mean = mean.copy()
        mean = np.sum([w * item[0].z for w, item in zip(elite_weights, elite)], axis=0)
        centered = np.vstack([(item[0].z - old_mean) / np.maximum(span, 1e-12) for item in elite])
        diag = 0.85 * diag + 0.15 * np.sum(elite_weights[:, None] * centered * centered, axis=0) / max(sigma * sigma, 1e-12)
        diag = np.clip(diag, 0.05, 5.0)
        if elite[0][0].objective < best.objective + 1e-14:
            sigma *= 0.985
        else:
            no_improve += 1
            sigma *= 1.02 if no_improve > 4 else 0.995
        sigma = float(np.clip(sigma, 0.025, 0.55))
        mean = _clip(mean, s)
    return _result("CMAES-lite", best, trace_fe, trace_obj, fe, started)


def run_gwo(s: dict, budget: int, seed: int, pop_size: int = 18) -> RunResult:
    rng = np.random.default_rng(seed)
    started = time.perf_counter()
    pop_size = max(6, min(pop_size, budget))
    wolves = _init_population(s, rng, pop_size)
    fe = len(wolves)
    wolves.sort(key=lambda item: item.objective)
    alpha, beta, delta = wolves[0], wolves[1], wolves[2]
    best = alpha
    trace_fe, trace_obj = [fe], [best.objective]

    while fe < budget:
        progress = fe / max(budget, 1)
        a = 2.0 * (1.0 - progress)
        for i in range(pop_size):
            if fe >= budget:
                break
            x = wolves[i].z
            positions = []
            for leader in (alpha, beta, delta):
                r1 = rng.random(len(x))
                r2 = rng.random(len(x))
                a_vec = 2.0 * a * r1 - a
                c_vec = 2.0 * r2
                d_vec = np.abs(c_vec * leader.z - x)
                positions.append(leader.z - a_vec * d_vec)
            trial_z = _key_jitter(np.mean(positions, axis=0), s, rng, assignment_prob=0.018, resource_prob=0.030, resource_sigma=0.16)
            trial = _evaluate(s, trial_z)
            fe += 1
            wolves[i] = trial
            _trace_append(trace_fe, trace_obj, fe, best.objective)
        wolves.sort(key=lambda item: item.objective)
        alpha, beta, delta = wolves[0], wolves[1], wolves[2]
        if alpha.objective < best.objective:
            best = alpha
            _trace_append(trace_fe, trace_obj, fe, best.objective)
    return _result("GWO", best, trace_fe, trace_obj, fe, started)


RUNNERS: dict[str, Callable[[dict, int, int], RunResult]] = {
    "Gbest-ABC": run_gbest_abc,
    "MeABC": run_meabc,
    "JADE": run_jade,
    "LSHADE-lite": run_lshade_lite,
    "CMAES-lite": run_cmaes_lite,
    "GWO": run_gwo,
}


def run_advanced_algorithm(name: str, s: dict, budget: int, seed: int) -> RunResult:
    """Run one advanced baseline by name."""
    if name not in RUNNERS:
        raise ValueError(f"unknown advanced algorithm: {name}")
    return RUNNERS[name](s, budget, seed)
