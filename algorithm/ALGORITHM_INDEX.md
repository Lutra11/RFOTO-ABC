# Algorithm index

All algorithms are evaluated through the same RFOTO scenario builder, random-key
representation, feasibility-preserving resource decoder, and objective
components. Historical initial populations differ for some methods, so this
shared model alone does not isolate search behavior. The revision supplies
matched-initialization adapters and fixed-objective interventions, as described
in `../experiments/revision_20260909/PROTOCOL.md`.

## Proposed method

| File | Entry | Role |
|---|---|---|
| `rfoto_core.py` | `run_rfoto_abc(...)` | Complete RFOTO-ABC implementation, including mixed random-key encoding, reliability-aware candidate construction, load-aware greedy seeding, risk-guided employed-bee moves, fairness-aware onlooker selection, directed scout behavior, and decoder-based allocation. |
| `rfoto_abc.py` | `run_rfoto_abc(...)` | Thin publication-facing wrapper for the proposed method. |

## Classical baselines

| File | Entry | Role |
|---|---|---|
| `standard_abc.py` | `run_standard_abc(...)` | Historical Standard-ABC adapter without RFOTO-specific guidance; not the revision Plain-ABC adapter. |
| `ga.py` | `run_ga(...)` | Genetic algorithm baseline. |
| `pso.py` | `run_pso(...)` | Particle swarm optimization baseline. |
| `de.py` | `run_de(...)` | Differential evolution baseline. |

## Advanced and related metaheuristics

| File | Entry | Role |
|---|---|---|
| `advanced_metaheuristics.py` | multiple | Shared implementation module for advanced RFOTO-aware random-key baselines. |
| `gbest_abc.py` | `run_gbest_abc(...)` | Global-best guided ABC. |
| `meabc.py` | `run_meabc(...)` | Memetic ABC with local refinement. |
| `jade.py` | `run_jade(...)` | Adaptive current-to-pbest differential evolution. |
| `lshade_lite.py` | `run_lshade_lite(...)` | Success-history DE with simple population reduction. |
| `cmaes_lite.py` | `run_cmaes_lite(...)` | Diagonal covariance evolution strategy. |
| `gwo.py` | `run_gwo(...)` | Grey wolf optimizer adapted to RFOTO random keys. |

## Rule baselines

| File | Entry | Role |
|---|---|---|
| `heuristic_baselines.py` | `run_rule(...)` | Rule methods: `Local-only`, `Random-feasible`, `Max-SINR`, `Delay-Greedy`, `Load-Aware`, and `Offload-then-Allocate`. |

## Unified dispatcher

| File | Entry | Role |
|---|---|---|
| `registry.py` | `run_algorithm(name, scenario, budget, seed)` | Single algorithm dispatcher used by multi-algorithm experiments. |

## Revision adapters

`../experiments/revision_20260909/revision_algorithms.py` accepts an externally
supplied initial population for RFOTO-ABC, Plain-ABC, DE-RK and LSHADE-lite.
It implements the individual risk-sampling, fairness-selection and scout
interventions. Uniform allocation changes initial decoded resources while
keeping the raw candidate encoding. Lite and MeABC variants are project
adapters rather than verified full original-author implementations.
