# Reproducibility

## Environment and commands

The revision ran on Windows with Python 3.12.14, NumPy 2.3.5 and SciPy 1.18.0. Recorded details are in `datas/revision_20260909/frozen_inputs.json` and `analysis/analysis_audit.json`. Six-worker runtime is not an isolated deployment-latency benchmark. `requirements.txt` specifies compatible dependencies.

| Purpose | Command |
|---|---|
| Verify frozen inputs and package integrity | `python tools/validate_release.py` |
| Summarize one core group | `python experiments/01_comparison.py` (or 02–04) |
| Compute a small replay without cached answers | `python experiments/01_comparison.py --rerun --max-jobs 4` |
| Compute all unique revision jobs | `python tools/core_runner.py --group all --rerun` |
| Regenerate statistics separately | `python tools/reanalyze.py` |
| Regenerate current numeric CSV tables | `python tools/build_tables.py` |
| Historical replay | `python tools/historical_replay.py main` (also advanced, ablation, sensitivity, transfer, scaling) |

Reruns use archived NPZ inputs and deterministic seeds and write to `outputs/`. `--max-jobs` is only a smoke-test limit. The 04 group includes the temperature records shown in 03; `all` uses the unique original job list.

The three immutable files `PROTOCOL.md`, `run_revision.py`, `revision_algorithms.py` under `experiments/revision_20260909/` retain their original bytes. The original runner includes a local pre-revision Word-file audit and is preserved as provenance. **Use the portable commands above on a clean clone**: they validate the frozen inputs and invoke the original job function on copied instances, without needing the author's private manuscript path.

## Revision protocol

- Controlled: S2/S4/S6, 20 fresh instances each, 320 and 1000 FE. Greedy initialization has 8 methods; random initialization has 4. Total 1,440 runs.
- Frozen test: S1–S6, 20 other fresh instances each, 5 settings. Four searches use 320 FE and the rule uses 1 FE. Total 600 runs.
- Overall: 180 distinct instances, 2,040 records (1,920 searches plus 120 rules), with seeds, population hashes, initial objectives and traces.
- Initial population 14, counted in FE. Objective weights `(0.25, 0.15, 0.20, 0.25, 0.15)`. LSHADE-lite population reduction depends on its allocated budget; the 320-FE slice of a 1000-FE run is not an independently run 320-FE result.
- Twenty paired instances per stratum. Two-sided Wilcoxon normal approximation, `zero_method=wilcox`, numerical-zero tolerance 1e-12, all-zero p=1. Holm correction in families of 84 controlled and 24 frozen-test contrasts. Bootstrap: 10,000 paired resamples, seed 20260909, pointwise 95% intervals (not simultaneous intervals).
- Temperature 1.6 was fixed before fresh testing using historical S4 exploration. Other optimizers were not evaluated at temperature 1.6.

## Historical protocols

The main comparison uses 30 instances/scenario, 500 FE in S1–S3 and 375 FE in S4–S6. Advanced comparison: 8 instances/scenario, 320 FE. Ablation: 20 S4 instances, 400 FE. Sensitivity: 6 repeats/setting, 280 FE. Transfer: 15 repeats/condition, 350 FE. Scaling: 10 repeats/size, 320 FE. Rules use 1 FE. See `tools/historical_suite.py` for settings and seeds.

Standard-ABC, Plain-ABC, MeABC and lite optimizers are stated adapters, not certified original-author implementations. Historical -F/-RF also change the search objective; common-weight rescoring does not remove that confound. The old `strong_server_heterogeneity` and `channel_estimation_shift` labels correspond to capacity/bandwidth scaling and observed link degradation, not an independently varied CPU distribution or unknown-channel prediction.

## Integrity

`frozen_inputs.json` protects 7 frozen inputs and 24 historical CSV files. `datas/release_manifest.json` covers current package files, including the run records and figures. Files are committed byte-preserving to avoid newline conversion invalidating original Windows hashes.

Historical CSVs with `win_count` remain unchanged for provenance; use `analysis/advanced_corrected_best_counts.csv` and current Table08. Display-only substituted numbers are excluded. PNGs retain 600-dpi metadata; PDFs preserve vector geometry.
