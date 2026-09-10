# Algorithm module

This folder contains the RFOTO-ABC optimizer, classical baselines, advanced
metaheuristic baselines, rule baselines, and a unified experiment-facing
registry.

The source layout follows the release style of the SHDMS-ABC package: a compact
core implementation is retained for consistency, while publication-facing
wrapper modules make each compared algorithm easy to locate.

| File | Contents |
|---|---|
| `rfoto_core.py` | Core scenario model, decoder, RFOTO-ABC implementation, Standard-ABC, GA, PSO, DE, rule baselines, and metric evaluation. |
| `rfoto_abc.py` | Wrapper for the proposed RFOTO-ABC method. |
| `standard_abc.py` | Wrapper for the Standard-ABC baseline configuration. |
| `ga.py`, `pso.py`, `de.py` | Classical metaheuristic wrappers. |
| `advanced_metaheuristics.py` | Advanced or closely related search baselines: Gbest-ABC, MeABC, JADE, LSHADE-lite, CMAES-lite, and GWO. |
| `gbest_abc.py`, `meabc.py`, `jade.py`, `lshade_lite.py`, `cmaes_lite.py`, `gwo.py` | One-file-per-algorithm wrappers for the advanced comparison. |
| `heuristic_baselines.py` | Rule baseline wrapper. |
| `registry.py` | Unified `run_algorithm(...)` dispatcher used by comparison experiments. |
| `__init__.py` | Public package exports. |

Advanced methods share the random-key representation, decoder and objective.
Historical initialization differs for some methods, so equal budgets alone do
not isolate search behavior. The manuscript workbook reports the retained
matched-initialization and component-intervention results.

The lite and MeABC implementations are documented adapters, not verified full
original-author implementations. A documented path-only migration lets
`rfoto_core.py` load the external sibling dataset directory.
