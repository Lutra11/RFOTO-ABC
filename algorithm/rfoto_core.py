#!/usr/bin/env python3
"""Core RFOTO-ABC model, decoder, baselines, and optimizers."""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATASETS_ROOT = Path(
    os.environ.get("RFOTO_DATASETS_DIR", ROOT.parent / "datasets")
).expanduser().resolve()
WIRELESS_ROOT = DATASETS_ROOT / "wireless_channel" / "generated_v1"
WORKLOAD_PROFILE = DATASETS_ROOT / "processed" / "alibaba_workload_profiles.npz"
NOISE_PSD_W_HZ = 10.0 ** ((-174.0 + 7.0 - 30.0) / 10.0)

DEFAULT_WEIGHTS = np.asarray([0.25, 0.15, 0.20, 0.25, 0.15], dtype=np.float64)


@dataclass
class Candidate:
    assignment: np.ndarray
    bandwidth_key: np.ndarray
    cpu_key: np.ndarray

    def copy(self) -> "Candidate":
        return Candidate(self.assignment.copy(), self.bandwidth_key.copy(), self.cpu_key.copy())


@dataclass
class DecodedSolution:
    objective: float
    components: np.ndarray
    assignment: np.ndarray
    bandwidth_hz: np.ndarray
    cpu_hz: np.ndarray
    delay_s: np.ndarray
    energy_j: np.ndarray
    reliability: np.ndarray
    q_success: np.ndarray
    expected_attempts: np.ndarray
    utility: np.ndarray
    violation: np.ndarray
    jain: float
    feasible: bool
    capacity_violation: float = 0.0


@dataclass
class RunResult:
    algorithm: str
    best_candidate: Candidate
    solution: DecodedSolution
    trace_fe: np.ndarray
    trace_objective: np.ndarray
    evaluations: int
    runtime_s: float


@dataclass
class AlgorithmConfig:
    population: int = 14
    abandonment_limit: int = 35
    greedy_ratio: float = 0.35
    theta_bandwidth: float = 0.8
    theta_cpu: float = 0.8
    candidate_limit: int = 4
    risk_weights: np.ndarray = field(
        default_factory=lambda: np.asarray([0.35, 0.30, 0.15, 0.20], dtype=np.float64)
    )
    fairness_strength: float = 1.0
    reliability_guidance: bool = True
    fairness_guidance: bool = True
    constraint_decoder: bool = True
    greedy_initialization: bool = True
    directed_scout: bool = True


@lru_cache(maxsize=16)
def _load_wireless(scenario: str, dynamic: bool = False) -> dict[str, np.ndarray]:
    path = (
        WIRELESS_ROOT / "dynamic" / "s6_dynamic.npz"
        if dynamic
        else WIRELESS_ROOT / "static" / f"{scenario.lower()}_static.npz"
    )
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


@lru_cache(maxsize=1)
def _load_workload() -> dict[str, np.ndarray]:
    with np.load(WORKLOAD_PROFILE, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


def _extract_channel(
    scenario: str,
    instance: int,
    n_users: int | None = None,
    n_servers: int | None = None,
    dynamic: tuple[int, int] | None = None,
) -> dict[str, np.ndarray]:
    data = _load_wireless(scenario, dynamic is not None)
    if dynamic is None:
        prefix = (instance % data["distance_2d_m"].shape[0],)
    else:
        prefix = dynamic
    n = n_users or data["distance_2d_m"].shape[len(prefix)]
    m = n_servers or data["distance_2d_m"].shape[len(prefix) + 1]
    link_slice = prefix + (slice(0, n), slice(0, m))
    user_slice = (prefix[0], slice(0, n)) if dynamic is not None else prefix + (slice(0, n),)
    out = {
        "q_grid": data["q_success_grid"][link_slice].astype(np.float64),
        "channel_gain": data["instantaneous_channel_gain"][link_slice].astype(np.float64),
        "interference_w": data["interference_w"][link_slice].astype(np.float64),
        "distance_m": data["distance_2d_m"][link_slice].astype(np.float64),
        "blocked": data["blocked"][link_slice].astype(np.uint8),
        "effective_los": data["effective_los"][link_slice].astype(np.uint8),
        "tx_power_w": data["tx_power_w"][user_slice].astype(np.float64),
        "bandwidth_grid_hz": data["bandwidth_grid_hz"].astype(np.float64),
        "gamma_grid_db": data["gamma_grid_db"].astype(np.float64),
    }
    return out


def build_scenario(
    scenario: str,
    instance: int,
    seed: int,
    n_users: int | None = None,
    n_servers: int | None = None,
    dynamic: tuple[int, int] | None = None,
    task_user_ids: np.ndarray | None = None,
    load_scale: float = 1.0,
    bandwidth_scale: float = 1.0,
    cpu_scale: float = 1.0,
    q_scale: float = 1.0,
    channel_loss_db: float = 0.0,
    weights: np.ndarray | None = None,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    channel = _extract_channel(scenario, instance, n_users, n_servers, dynamic)
    if task_user_ids is not None:
        ids = np.asarray(task_user_ids, dtype=int)
        for key in ("q_grid", "channel_gain", "interference_w", "distance_m", "blocked", "effective_los"):
            channel[key] = channel[key][ids]
        channel["tx_power_w"] = channel["tx_power_w"][ids]
    n, m = channel["channel_gain"].shape
    workload = _load_workload()
    idx = rng.integers(0, len(workload["compute_cycles"]), size=n)
    compute_cycles = np.clip(workload["compute_cycles"][idx].astype(np.float64) * load_scale, 0.2e9, 5.0e9)
    c_norm = np.clip((compute_cycles - 0.2e9) / 4.8e9, 0.0, 1.0)
    input_bits = np.clip(
        (0.5 + 6.0 * c_norm + rng.lognormal(-0.4, 0.55, n)) * 1.0e6,
        0.5e6,
        10.0e6,
    )
    priority = rng.choice(np.asarray([1.0, 2.0, 4.0]), size=n, p=[0.60, 0.30, 0.10])
    deadline_s = np.clip(0.20 + 1.45 * np.sqrt(c_norm) + rng.normal(0.0, 0.16, n), 0.10, 2.0)
    rho_min = np.where(priority >= 4, 0.99, np.where(priority >= 2, 0.95, 0.90)).astype(np.float64)
    strict = rng.random(n) < 0.12
    rho_min[strict] = np.maximum(rho_min[strict], 0.999)
    gamma_db = rng.choice(channel["gamma_grid_db"], size=n, p=[0.10, 0.20, 0.35, 0.25, 0.10])
    max_transmissions = rng.choice(np.asarray([1, 2, 3]), size=n, p=[0.15, 0.35, 0.50])
    local_freq_hz = rng.uniform(0.55e9, 1.45e9, n)
    kappa = rng.uniform(0.6e-28, 1.4e-28, n)

    cpu_profile = workload["machine_cpu_num"].astype(np.float64)
    util_profile = workload["machine_cpu_util_percent"].astype(np.float64)
    cpu_pick = rng.choice(cpu_profile, size=m, replace=True)
    util_pick = rng.choice(util_profile, size=m, replace=True)
    server_cpu_hz = np.clip(10.0e9 + (cpu_pick / max(np.quantile(cpu_profile, 0.95), 1.0)) * 90.0e9, 10e9, 100e9)
    server_cpu_hz *= cpu_scale
    server_bandwidth_hz = rng.uniform(10.0e6, 40.0e6, m) * bandwidth_scale
    queue_delay_s = 0.005 + 0.30 * (np.clip(util_pick, 0, 100) / 100.0) ** 2

    channel["q_grid"] = np.clip(channel["q_grid"] * q_scale, 0.0, 1.0)
    channel["channel_gain"] *= 10.0 ** (-channel_loss_db / 10.0)
    return {
        "id": f"{scenario}-i{instance}-seed{seed}",
        "scenario": scenario,
        "n": n,
        "m": m,
        "D": input_bits,
        "C": compute_cycles,
        "tau": deadline_s,
        "rho_min": rho_min,
        "omega": priority,
        "gamma_db": gamma_db,
        "K": max_transmissions,
        "f_local": local_freq_hz,
        "kappa": kappa,
        "p_tx": channel["tx_power_w"],
        "q_grid": channel["q_grid"],
        "channel_gain": channel["channel_gain"],
        "interference_w": channel["interference_w"],
        "distance_m": channel["distance_m"],
        "blocked": channel["blocked"],
        "effective_los": channel["effective_los"],
        "bandwidth_grid_hz": channel["bandwidth_grid_hz"],
        "gamma_grid_db": channel["gamma_grid_db"],
        "B": server_bandwidth_hz,
        "F": server_cpu_hz,
        "queue_delay": queue_delay_s,
        "weights": (DEFAULT_WEIGHTS if weights is None else np.asarray(weights, dtype=np.float64)),
        "b_min": 0.10e6,
        "f_min": 0.20e9,
        "theta_b": 0.8,
        "theta_f": 0.8,
    }


def interpolate_q(s: dict[str, Any], bandwidth: np.ndarray) -> np.ndarray:
    n, m = bandwidth.shape
    q_grid = s["q_grid"]
    b_grid = s["bandwidth_grid_hz"]
    g_grid = s["gamma_grid_db"]
    log_b = np.log(np.clip(bandwidth, b_grid[0], b_grid[-1]))
    log_grid = np.log(b_grid)
    gamma = np.broadcast_to(s["gamma_db"][:, None], (n, m))
    b_hi = np.clip(np.searchsorted(log_grid, log_b, side="right"), 1, len(log_grid) - 1)
    b_lo = b_hi - 1
    g_hi = np.clip(np.searchsorted(g_grid, gamma, side="right"), 1, len(g_grid) - 1)
    g_lo = g_hi - 1
    wb = (log_b - log_grid[b_lo]) / np.maximum(log_grid[b_hi] - log_grid[b_lo], 1e-12)
    wg = (gamma - g_grid[g_lo]) / np.maximum(g_grid[g_hi] - g_grid[g_lo], 1e-12)
    ii = np.arange(n)[:, None]
    jj = np.arange(m)[None, :]
    q00 = q_grid[ii, jj, b_lo, g_lo]
    q10 = q_grid[ii, jj, b_hi, g_lo]
    q01 = q_grid[ii, jj, b_lo, g_hi]
    q11 = q_grid[ii, jj, b_hi, g_hi]
    return np.clip((1-wb)*(1-wg)*q00 + wb*(1-wg)*q10 + (1-wb)*wg*q01 + wb*wg*q11, 0, 1)


def stable_softmax(values: np.ndarray, theta: float) -> np.ndarray:
    z = np.clip(values / max(theta, 1e-6), -30.0, 30.0)
    z -= np.max(z)
    e = np.exp(z)
    return e / max(np.sum(e), 1e-300)


def _allocate_resources(s, assignment, b_key, f_key, mode="softmax"):
    n, m = s["n"], s["m"]
    b = np.zeros((n, m), dtype=np.float64)
    f = np.zeros((n, m), dtype=np.float64)
    assignment = assignment.copy()
    for server in range(1, m + 1):
        ids = np.flatnonzero(assignment == server)
        max_count_b = int(s["B"][server-1] // s["b_min"])
        max_count_f = int(s["F"][server-1] // s["f_min"])
        max_count = min(max_count_b, max_count_f)
        if len(ids) > max_count:
            score = s["omega"][ids] / np.maximum(s["tau"][ids], 1e-9)
            keep = ids[np.argsort(score)[::-1][:max_count]]
            drop = np.setdiff1d(ids, keep, assume_unique=True)
            assignment[drop] = 0
            ids = keep
        if len(ids) == 0:
            continue
        if mode == "uniform":
            wb = np.full(len(ids), 1.0 / len(ids))
            wf = wb.copy()
        else:
            wb = stable_softmax(b_key[ids], s["theta_b"])
            wf = stable_softmax(f_key[ids], s["theta_f"])
        b_rem = max(s["B"][server-1] - len(ids)*s["b_min"], 0.0)
        f_rem = max(s["F"][server-1] - len(ids)*s["f_min"], 0.0)
        b[ids, server-1] = s["b_min"] + b_rem * wb
        f[ids, server-1] = s["f_min"] + f_rem * wf
    return assignment, b, f


def decode_candidate(
    s: dict[str, Any],
    candidate: Candidate,
    resource_mode: str = "softmax",
    enforce_reliability: bool = True,
) -> DecodedSolution:
    n, m = s["n"], s["m"]
    assignment = np.clip(candidate.assignment.astype(int), 0, m)
    rows = np.arange(n)
    for _ in range(n + 1):
        assignment, b, f = _allocate_resources(s, assignment, candidate.bandwidth_key, candidate.cpu_key, resource_mode)
        q_matrix = interpolate_q(s, np.maximum(b, s["b_min"]))
        chosen_server = np.clip(assignment - 1, 0, m - 1)
        q_chosen = np.where(assignment > 0, q_matrix[rows, chosen_server], 1.0)
        rho = np.where(assignment > 0, 1.0 - (1.0 - q_chosen) ** s["K"], 1.0)
        if not enforce_reliability:
            break
        invalid = (assignment > 0) & (rho + 1e-12 < s["rho_min"])
        if not np.any(invalid):
            break
        assignment[invalid] = 0

    q_safe = np.maximum(q_chosen, 1e-12)
    expected_attempts = np.where(assignment > 0, (1.0 - (1.0-q_chosen)**s["K"]) / q_safe, 0.0)
    local_delay = s["C"] / s["f_local"]
    local_energy = s["kappa"] * s["C"] * s["f_local"] ** 2
    delay = local_delay.copy()
    energy = local_energy.copy()
    if np.any(assignment > 0):
        off = np.flatnonzero(assignment > 0)
        srv = assignment[off] - 1
        b_sel = b[off, srv]
        f_sel = f[off, srv]
        h_sel = s["channel_gain"][off, srv]
        i_sel = s["interference_w"][off, srv]
        sinr = s["p_tx"][off] * h_sel / np.maximum(NOISE_PSD_W_HZ*b_sel + i_sel, 1e-300)
        rate = b_sel * np.log2(1.0 + np.maximum(sinr, 0.0))
        tx_delay = expected_attempts[off] * s["D"][off] / np.maximum(rate, 1e-9)
        exe_delay = s["C"][off] / np.maximum(f_sel, 1e-9)
        delay[off] = tx_delay + s["queue_delay"][srv] + exe_delay
        energy[off] = s["p_tx"][off] * tx_delay

    violation = np.maximum(delay - s["tau"], 0.0) / s["tau"]
    utility = rho * np.minimum(1.0, s["tau"] / np.maximum(delay, 1e-12))
    jain = float(np.sum(utility) ** 2 / (n*np.sum(utility**2) + 1e-12))
    normalized_weight = s["omega"] / np.sum(s["omega"])
    t_hat = float(np.sum(normalized_weight * delay / s["tau"]))
    e_hat = float(np.mean(energy / np.maximum(local_energy, 1e-12)))
    r_hat = float(np.mean(1.0 - rho))
    v_hat = float(np.sum(normalized_weight * violation))
    components = np.asarray([t_hat, e_hat, r_hat, v_hat, 1.0-jain])
    objective = float(np.dot(s["weights"], components))
    feasible = bool(np.all(rho[assignment > 0] + 1e-9 >= s["rho_min"][assignment > 0]))
    return DecodedSolution(
        objective, components, assignment, b, f, delay, energy, rho, q_chosen,
        expected_attempts, utility, violation, jain, feasible
    )


def random_candidate(s, rng):
    n, m = s["n"], s["m"]
    return Candidate(rng.integers(0, m+1, n), rng.normal(0, 1, n), rng.normal(0, 1, n))


def greedy_candidate(s, mode="load"):
    n, m = s["n"], s["m"]
    assignment = np.zeros(n, dtype=int)
    counts = np.zeros(m, dtype=float)
    b_est = np.broadcast_to((s["B"] / max(n/m, 1.0))[None, :], (n, m))
    q = interpolate_q(s, np.maximum(b_est, s["b_min"]))
    rho = 1.0 - (1.0-q) ** s["K"][:, None]
    local = s["C"] / s["f_local"]
    for i in np.argsort(s["omega"]*(s["C"]+s["D"])/s["tau"])[::-1]:
        if mode == "sinr":
            assignment[i] = int(np.argmax(s["channel_gain"][i])) + 1
            continue
        remote = s["D"][i] / np.maximum(b_est[i]*np.log2(1+s["p_tx"][i]*s["channel_gain"][i]/np.maximum(NOISE_PSD_W_HZ*b_est[i]+s["interference_w"][i],1e-300)),1e-9)
        remote += s["C"][i] / np.maximum(s["F"]/(counts+1.0), 1e-9) + s["queue_delay"]
        if mode == "load":
            remote *= 1.0 + 0.20 * counts
        remote = np.where(rho[i] >= s["rho_min"][i], remote, np.inf)
        best = int(np.argmin(remote))
        if remote[best] < local[i] * 1.25:
            assignment[i] = best + 1
            counts[best] += 1
    urgency = np.log1p(s["omega"]*(s["C"]/1e9+s["D"]/1e6)/s["tau"])
    return Candidate(assignment, urgency.copy(), urgency.copy())


def mutate_candidate(s, c, sol, rng, cfg, full_method=True):
    out = c.copy()
    n, m = s["n"], s["m"]
    if full_method and cfg.reliability_guidance:
        load = np.zeros(n)
        for server in range(1, m+1):
            ids = sol.assignment == server
            load[ids] = np.mean(ids)
        risk = (
            cfg.risk_weights[0]*(1-sol.reliability)
            + cfg.risk_weights[1]*sol.violation
            + cfg.risk_weights[2]*load
            + cfg.risk_weights[3]*(1-sol.utility)
        )
        prob = risk + 1e-6
        prob /= np.sum(prob)
        i = int(rng.choice(n, p=prob))
    elif full_method and cfg.fairness_guidance and rng.random() < 0.5:
        threshold = np.quantile(sol.utility, 0.25)
        ids = np.flatnonzero(sol.utility <= threshold)
        i = int(rng.choice(ids))
    else:
        i = int(rng.integers(0, n))
    if rng.random() < 0.55:
        if full_method and cfg.reliability_guidance:
            b_ref = np.broadcast_to(s["B"][None, :] / max(n/m, 1), (n,m))
            q = interpolate_q(s, np.maximum(b_ref, s["b_min"]))[i]
            rho = 1-(1-q)**s["K"][i]
            feasible = np.flatnonzero(rho >= s["rho_min"][i])
            choices = np.concatenate(([0], feasible+1))
            if len(choices) > cfg.candidate_limit:
                channel_rank = np.argsort(s["channel_gain"][i, feasible])[::-1][:cfg.candidate_limit-1]
                choices = np.concatenate(([0], feasible[channel_rank]+1))
            out.assignment[i] = int(rng.choice(choices))
        else:
            out.assignment[i] = int(rng.integers(0, m+1))
    else:
        out.bandwidth_key[i] = np.clip(out.bandwidth_key[i] + rng.normal(0, 0.7), -5, 5)
        out.cpu_key[i] = np.clip(out.cpu_key[i] + rng.normal(0, 0.7), -5, 5)
    return out


def _trace_append(trace_fe, trace_obj, fe, obj):
    if not trace_fe or fe == 1 or fe - trace_fe[-1] >= 5:
        trace_fe.append(fe); trace_obj.append(obj)


def run_rfoto_abc(s, budget, seed, cfg=None, algorithm="RFOTO-ABC", warm_candidate=None):
    cfg = cfg or AlgorithmConfig()
    rng = np.random.default_rng(seed)
    start = time.perf_counter()
    pop_size = max(4, min(cfg.population, budget))
    population = []
    if warm_candidate is not None and len(warm_candidate.assignment) == s["n"]:
        population.append(warm_candidate.copy())
    greedy = greedy_candidate(s, "load")
    if cfg.greedy_initialization and len(population) < pop_size:
        population.append(greedy.copy())
    while len(population) < pop_size:
        if cfg.greedy_initialization and len(population) < max(1, int(pop_size*cfg.greedy_ratio)):
            c = greedy.copy()
            flip = rng.random(s["n"]) < 0.10
            c.assignment[flip] = rng.integers(0, s["m"]+1, np.sum(flip))
            c.bandwidth_key += rng.normal(0, 0.35, s["n"])
            c.cpu_key += rng.normal(0, 0.35, s["n"])
        else:
            c = random_candidate(s, rng)
        population.append(c)
    resource_mode = "softmax" if cfg.constraint_decoder else "uniform"
    solutions = [decode_candidate(s, c, resource_mode) for c in population]
    fe = len(solutions)
    trials = np.zeros(pop_size, dtype=int)
    best_idx = int(np.argmin([x.objective for x in solutions]))
    best_c, best_s = population[best_idx].copy(), solutions[best_idx]
    trace_fe, trace_obj = [fe], [best_s.objective]
    full = algorithm != "Standard-ABC"
    while fe < budget:
        values = np.asarray([x.objective for x in solutions])
        ranks = np.argsort(np.argsort(values))
        fair = np.asarray([x.jain for x in solutions])
        score = np.exp(-2.0*ranks/max(pop_size-1,1) + (cfg.fairness_strength*fair if cfg.fairness_guidance and full else 0))
        idx = int(rng.choice(pop_size, p=score/score.sum())) if fe % 2 else int((fe//2) % pop_size)
        neighbor = mutate_candidate(s, population[idx], solutions[idx], rng, cfg, full)
        new_sol = decode_candidate(s, neighbor, resource_mode)
        fe += 1
        if new_sol.objective < solutions[idx].objective:
            population[idx], solutions[idx], trials[idx] = neighbor, new_sol, 0
        else:
            trials[idx] += 1
        if trials[idx] >= cfg.abandonment_limit and fe < budget:
            if cfg.directed_scout and full:
                scout = population[idx].copy()
                risk = (1-solutions[idx].utility) + solutions[idx].violation
                high = risk >= np.quantile(risk, 0.70)
                scout.assignment[high] = rng.integers(0, s["m"]+1, np.sum(high))
                scout.bandwidth_key[high] = rng.normal(0,1,np.sum(high))
                scout.cpu_key[high] = rng.normal(0,1,np.sum(high))
            else:
                scout = random_candidate(s, rng)
            population[idx] = scout
            solutions[idx] = decode_candidate(s, scout, resource_mode)
            trials[idx] = 0
            fe += 1
        current = int(np.argmin([x.objective for x in solutions]))
        if solutions[current].objective < best_s.objective:
            best_c, best_s = population[current].copy(), solutions[current]
        _trace_append(trace_fe, trace_obj, fe, best_s.objective)
    return RunResult(algorithm, best_c, best_s, np.asarray(trace_fe), np.asarray(trace_obj), fe, time.perf_counter()-start)


def encode_candidate(c, m):
    return np.concatenate([c.assignment/(m+1), c.bandwidth_key/5.0, c.cpu_key/5.0])


def decode_vector(z, s):
    n, m = s["n"], s["m"]
    z = np.asarray(z)
    assignment = np.clip(np.floor(np.clip(z[:n],0,0.999999)*(m+1)),0,m).astype(int)
    return Candidate(assignment, np.clip(z[n:2*n]*5,-5,5), np.clip(z[2*n:3*n]*5,-5,5))


def run_ga(s, budget, seed, pop_size=14):
    rng=np.random.default_rng(seed); start=time.perf_counter(); pop_size=min(pop_size,budget)
    pop=[random_candidate(s,rng) for _ in range(pop_size)]; sols=[decode_candidate(s,c) for c in pop]; fe=pop_size
    bi=int(np.argmin([x.objective for x in sols])); best_c,best_s=pop[bi].copy(),sols[bi]; tf,to=[fe],[best_s.objective]
    while fe<budget:
        ids=rng.choice(pop_size,4,replace=True); a=ids[0] if sols[ids[0]].objective<sols[ids[1]].objective else ids[1]; b=ids[2] if sols[ids[2]].objective<sols[ids[3]].objective else ids[3]
        mask=rng.random(s["n"])<0.5; child=pop[a].copy(); child.assignment[mask]=pop[b].assignment[mask]; child.bandwidth_key[mask]=pop[b].bandwidth_key[mask]; child.cpu_key[mask]=pop[b].cpu_key[mask]
        mut=rng.random(s["n"])<max(1/s["n"],0.03); child.assignment[mut]=rng.integers(0,s["m"]+1,np.sum(mut)); child.bandwidth_key+=rng.normal(0,0.15,s["n"]); child.cpu_key+=rng.normal(0,0.15,s["n"])
        sol=decode_candidate(s,child); fe+=1; worst=int(np.argmax([x.objective for x in sols]));
        if sol.objective<sols[worst].objective: pop[worst],sols[worst]=child,sol
        cur=int(np.argmin([x.objective for x in sols]));
        if sols[cur].objective<best_s.objective: best_c,best_s=pop[cur].copy(),sols[cur]
        _trace_append(tf,to,fe,best_s.objective)
    return RunResult("GA",best_c,best_s,np.asarray(tf),np.asarray(to),fe,time.perf_counter()-start)


def run_de(s,budget,seed,pop_size=14):
    rng=np.random.default_rng(seed); start=time.perf_counter(); nvar=3*s["n"]; pop_size=max(4,min(pop_size,budget)); z=rng.uniform(-1,1,(pop_size,nvar)); z[:,:s["n"]]=rng.random((pop_size,s["n"])); sols=[decode_candidate(s,decode_vector(v,s)) for v in z]; fe=pop_size
    bi=int(np.argmin([x.objective for x in sols])); best_z=z[bi].copy(); best_s=sols[bi]; tf,to=[fe],[best_s.objective]
    while fe<budget:
        i=(fe-pop_size)%pop_size; choices=np.delete(np.arange(pop_size),i); a,b,c=rng.choice(choices,3,replace=False); mutant=z[a]+0.65*(z[b]-z[c]); cross=rng.random(nvar)<0.7; cross[rng.integers(0,nvar)]=True; trial=np.where(cross,mutant,z[i]); trial[:s["n"]]=np.clip(trial[:s["n"]],0,0.999999); trial[s["n"]:]=np.clip(trial[s["n"]:],-1,1); sol=decode_candidate(s,decode_vector(trial,s)); fe+=1
        if sol.objective<sols[i].objective: z[i],sols[i]=trial,sol
        cur=int(np.argmin([x.objective for x in sols]));
        if sols[cur].objective<best_s.objective: best_z,best_s=z[cur].copy(),sols[cur]
        _trace_append(tf,to,fe,best_s.objective)
    return RunResult("DE",decode_vector(best_z,s),best_s,np.asarray(tf),np.asarray(to),fe,time.perf_counter()-start)


def run_pso(s,budget,seed,pop_size=14):
    rng=np.random.default_rng(seed); start=time.perf_counter(); nvar=3*s["n"]; pop_size=max(4,min(pop_size,budget)); z=rng.uniform(-1,1,(pop_size,nvar)); z[:,:s["n"]]=rng.random((pop_size,s["n"])); vel=np.zeros_like(z); sols=[decode_candidate(s,decode_vector(v,s)) for v in z]; fe=pop_size; pbest=z.copy(); psol=list(sols); bi=int(np.argmin([x.objective for x in sols])); gbest=z[bi].copy(); best_s=sols[bi]; tf,to=[fe],[best_s.objective]
    while fe<budget:
        i=(fe-pop_size)%pop_size; vel[i]=0.55*vel[i]+1.35*rng.random(nvar)*(pbest[i]-z[i])+1.35*rng.random(nvar)*(gbest-z[i]); z[i]+=vel[i]; z[i,:s["n"]]=np.clip(z[i,:s["n"]],0,0.999999); z[i,s["n"]:]=np.clip(z[i,s["n"]:],-1,1); sol=decode_candidate(s,decode_vector(z[i],s)); fe+=1
        if sol.objective<psol[i].objective: pbest[i],psol[i]=z[i].copy(),sol
        cur=int(np.argmin([x.objective for x in psol]));
        if psol[cur].objective<best_s.objective: gbest,best_s=pbest[cur].copy(),psol[cur]
        _trace_append(tf,to,fe,best_s.objective)
    return RunResult("PSO",decode_vector(gbest,s),best_s,np.asarray(tf),np.asarray(to),fe,time.perf_counter()-start)


def run_rule(s, algorithm, seed=0):
    start=time.perf_counter(); rng=np.random.default_rng(seed)
    if algorithm=="Local-only": c=Candidate(np.zeros(s["n"],int),np.zeros(s["n"]),np.zeros(s["n"])); mode="uniform"
    elif algorithm=="Random-feasible": c=random_candidate(s,rng); mode="softmax"
    elif algorithm=="Max-SINR": c=greedy_candidate(s,"sinr"); mode="uniform"
    elif algorithm=="Delay-Greedy": c=greedy_candidate(s,"delay"); mode="softmax"
    elif algorithm=="Load-Aware": c=greedy_candidate(s,"load"); mode="softmax"
    elif algorithm=="Offload-then-Allocate": c=greedy_candidate(s,"delay"); mode="uniform"
    else: raise ValueError(algorithm)
    sol=decode_candidate(s,c,mode); return RunResult(algorithm,c,sol,np.asarray([1]),np.asarray([sol.objective]),1,time.perf_counter()-start)


def metrics_record(result: RunResult, scenario: str, run: int, extra: dict[str,Any]|None=None):
    sol=result.solution; srec={
        "scenario":scenario,"run":run,"algorithm":result.algorithm,"objective":sol.objective,
        "delay_mean_s":float(np.mean(sol.delay_s)),"delay_p95_s":float(np.quantile(sol.delay_s,0.95)),
        "energy_mean_j":float(np.mean(sol.energy_j)),"success_rate":float(np.mean(sol.violation<=1e-12)),
        "violation_rate":float(np.mean(sol.violation>1e-12)),"violation_mean":float(np.mean(sol.violation)),
        "reliability_mean":float(np.mean(sol.reliability)),"link_failure_rate":float(np.mean(1-sol.reliability)),
        "attempts_mean":float(np.mean(sol.expected_attempts[sol.assignment>0])) if np.any(sol.assignment>0) else 0.0,
        "jain":sol.jain,"utility_p05":float(np.quantile(sol.utility,0.05)),"utility_min":float(np.min(sol.utility)),
        "utility_cv":float(np.std(sol.utility)/max(np.mean(sol.utility),1e-12)),"offload_rate":float(np.mean(sol.assignment>0)),
        "runtime_s":result.runtime_s,"evaluations":result.evaluations,"feasible":int(sol.feasible),
        "t_hat":sol.components[0],"e_hat":sol.components[1],"r_hat":sol.components[2],"v_hat":sol.components[3],"fairness_loss":sol.components[4],
    }
    if extra: srec.update(extra)
    return srec
