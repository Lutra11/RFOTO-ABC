"""Matched-initialization adapters. Original algorithm files remain unchanged."""
from __future__ import annotations
import copy
import time
import numpy as np
from algorithm import rfoto_core as core
from algorithm import advanced_metaheuristics as advanced


def initial_population(s, seed, mode="greedy", population=14, return_rng=False):
    rng = np.random.default_rng(seed)
    pop = []
    greedy = core.greedy_candidate(s, "load")
    if mode == "greedy":
        pop.append(greedy.copy())
    while len(pop) < population:
        if mode == "greedy" and len(pop) < max(1, int(population * 0.35)):
            c = greedy.copy()
            flip = rng.random(s["n"]) < 0.10
            c.assignment[flip] = rng.integers(0, s["m"] + 1, np.sum(flip))
            c.bandwidth_key += rng.normal(0, 0.35, s["n"])
            c.cpu_key += rng.normal(0, 0.35, s["n"])
        else:
            c = core.random_candidate(s, rng)
        pop.append(c)
    return (pop, rng) if return_rng else pop


def centered_encode(c, m):
    return np.concatenate(((c.assignment + 0.5) / (m + 1), c.bandwidth_key / 5, c.cpu_key / 5))


def run_abc(s, budget, seed, initial, name="RFOTO-ABC", cfg=None, rng_state=None):
    """Original RFOTO loop with externally supplied population and optional RNG state.

    Only initialization is replaced. Scout count and search diagnostics are added
    without making random draws. A replay regression checks original equivalence.
    """
    cfg = cfg or core.AlgorithmConfig()
    rng = np.random.default_rng(seed)
    if rng_state is not None:
        rng.bit_generator.state = copy.deepcopy(rng_state)
    start = time.perf_counter()
    population = [c.copy() for c in initial]
    pop_size = len(population)
    assert 4 <= pop_size <= budget
    resource_mode = "softmax" if cfg.constraint_decoder else "uniform"
    solutions = [core.decode_candidate(s, c, resource_mode) for c in population]
    fe = len(solutions)
    trials = np.zeros(pop_size, dtype=int)
    best_idx = int(np.argmin([x.objective for x in solutions]))
    best_c, best_s = population[best_idx].copy(), solutions[best_idx]
    trace_fe, trace_obj = [fe], [best_s.objective]
    full = name not in {"Plain-ABC", "Standard-ABC"}
    scout_count = 0
    accepted_neighbors = 0
    while fe < budget:
        values = np.asarray([x.objective for x in solutions])
        ranks = np.argsort(np.argsort(values))
        fair = np.asarray([x.jain for x in solutions])
        score = np.exp(-2.0 * ranks / max(pop_size-1, 1) + (cfg.fairness_strength * fair if cfg.fairness_guidance and full else 0))
        idx = int(rng.choice(pop_size, p=score/score.sum())) if fe % 2 else int((fe//2) % pop_size)
        neighbor = core.mutate_candidate(s, population[idx], solutions[idx], rng, cfg, full)
        new_sol = core.decode_candidate(s, neighbor, resource_mode)
        fe += 1
        if new_sol.objective < solutions[idx].objective:
            population[idx], solutions[idx], trials[idx] = neighbor, new_sol, 0
            accepted_neighbors += 1
        else:
            trials[idx] += 1
        if trials[idx] >= cfg.abandonment_limit and fe < budget:
            if cfg.directed_scout and full:
                scout = population[idx].copy()
                risk = (1-solutions[idx].utility) + solutions[idx].violation
                high = risk >= np.quantile(risk, 0.70)
                scout.assignment[high] = rng.integers(0, s["m"]+1, np.sum(high))
                scout.bandwidth_key[high] = rng.normal(0, 1, np.sum(high))
                scout.cpu_key[high] = rng.normal(0, 1, np.sum(high))
            else:
                scout = core.random_candidate(s, rng)
            population[idx] = scout
            solutions[idx] = core.decode_candidate(s, scout, resource_mode)
            trials[idx] = 0
            fe += 1
            scout_count += 1
        current = int(np.argmin([x.objective for x in solutions]))
        if solutions[current].objective < best_s.objective:
            best_c, best_s = population[current].copy(), solutions[current]
        core._trace_append(trace_fe, trace_obj, fe, best_s.objective)
    if trace_fe[-1] != fe:
        trace_fe.append(fe)
        trace_obj.append(best_s.objective)
    result = core.RunResult(name, best_c, best_s, np.asarray(trace_fe), np.asarray(trace_obj), fe, time.perf_counter()-start)
    result.scout_count = scout_count
    result.accepted_neighbors = accepted_neighbors
    return result


def run_de(s, budget, seed, initial):
    rng = np.random.default_rng(seed)
    start = time.perf_counter()
    nvar = 3 * s["n"]
    z = np.stack([centered_encode(c, s["m"]) for c in initial])
    sols = [core.decode_candidate(s, core.decode_vector(v, s)) for v in z]
    pop_size = len(initial)
    fe = pop_size
    bi = int(np.argmin([x.objective for x in sols]))
    best_z, best_s = z[bi].copy(), sols[bi]
    tf, to = [fe], [best_s.objective]
    while fe < budget:
        i = (fe-pop_size) % pop_size
        choices = np.delete(np.arange(pop_size), i)
        a, b, c = rng.choice(choices, 3, replace=False)
        mutant = z[a] + 0.65*(z[b]-z[c])
        cross = rng.random(nvar) < 0.7
        cross[rng.integers(0, nvar)] = True
        trial = np.where(cross, mutant, z[i])
        trial[:s["n"]] = np.clip(trial[:s["n"]], 0, 0.999999)
        trial[s["n"]:] = np.clip(trial[s["n"]:], -1, 1)
        sol = core.decode_candidate(s, core.decode_vector(trial, s))
        fe += 1
        if sol.objective < sols[i].objective:
            z[i], sols[i] = trial, sol
        cur = int(np.argmin([x.objective for x in sols]))
        if sols[cur].objective < best_s.objective:
            best_z, best_s = z[cur].copy(), sols[cur]
        core._trace_append(tf, to, fe, best_s.objective)
    if tf[-1] != fe:
        tf.append(fe)
        to.append(best_s.objective)
    return core.RunResult("DE-RK", core.decode_vector(best_z, s), best_s, np.asarray(tf), np.asarray(to), fe, time.perf_counter()-start)


def run_lshade(s, budget, seed, initial):
    # Patch only the initializer for the duration of this call. Each process
    # executes one optimizer at a time, so the override cannot race.
    old_initializer = advanced._init_population
    def supplied_population(scene, rng, pop_size):
        assert pop_size == len(initial)
        return [advanced._evaluate(scene, centered_encode(c, scene["m"])) for c in initial]
    advanced._init_population = supplied_population
    try:
        result = advanced.run_lshade_lite(s, budget, seed, pop_size=len(initial))
    finally:
        advanced._init_population = old_initializer
    if result.trace_fe[-1] != result.evaluations:
        result.trace_fe = np.append(result.trace_fe, result.evaluations)
        result.trace_objective = np.append(result.trace_objective, result.solution.objective)
    return result


def run_method(s, budget, seed, initial, name):
    if name == "DE-RK":
        return run_de(s, budget, seed, initial)
    if name == "LSHADE-lite":
        return run_lshade(s, budget, seed, initial)
    if name == "Offload-then-Allocate":
        return core.run_rule(s, name, seed)
    cfg = core.AlgorithmConfig(population=len(initial))
    if name == "No-risk-sampling":
        cfg.risk_weights = np.zeros(4)
    elif name == "No-fair-selection":
        cfg.fairness_guidance = False
    elif name == "Random-scout":
        cfg.directed_scout = False
    elif name == "Uniform-allocation":
        cfg.constraint_decoder = False
    elif name == "Plain-ABC":
        cfg.reliability_guidance = False
        cfg.fairness_guidance = False
        cfg.directed_scout = False
    return run_abc(s, budget, seed, initial, name, cfg)
