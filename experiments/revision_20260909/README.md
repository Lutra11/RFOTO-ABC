# Revision experiment package

This package supplements the historical RFOTO-ABC experiments. It does not overwrite them.

Read `PROTOCOL.md` first. The 180 instances, all 2040 records, traces, hashes and analyses are under `../../datas/revision_20260909`. Current figures are in `../../images/{png,pdf}` (Figures 04, 06, 08, 10). PNG files are rendered at 600 dpi and PDFs retain vector geometry and embedded fonts.

## Reproduce

Use Python 3.12 with NumPy, pandas, SciPy and matplotlib. In the recorded desktop runtime NumPy was 2.3.5 and SciPy 1.18.0. The archived generator requires the existing Alibaba-derived NPZ profile; raw Alibaba archive downloads are not repeated here.

```text
python tools/core_runner.py --group all --rerun
python tools/reanalyze.py
python tools/regenerate_figures.py
```

The original runner is retained unchanged as provenance, including its local manuscript audit. The portable commands above avoid that external manuscript dependency and write replay outputs separately. Do not overwrite the archived evidence. The frozen hashes prevent silently changing the original protocol. Reporting scripts retain harmless recorded-environment fallback paths; a standard installed environment needs none of those directories. Do not modify frozen optimizer/runner files for report-only changes.

## Main interpretation

- Controlling initial candidates confirms some additional search gain relative to LSHADE-lite under greedy initialization, but not a universal advantage from all starting states.
- Fixed-objective one-operation ablations do not establish stable independent benefit for every guidance component.
- Uniform allocation remains a consequential simpler alternative, not an infeasible ablation.
- The temperature 1.6 configuration was specified before the 120-instance test and improves mean objective relative to the original 0.8 setting in all six scenes. This is a within-RFOTO configuration comparison; the other optimizers were not evaluated at temperature 1.6.
- Fresh synthetic instances are distinct from historical wireless states but share the original empirical workload profile and generator. This is not a new real-world test dataset.
- Historical unique/tied best counts are corrected separately in `analysis/advanced_corrected_best_counts.csv`: RFOTO has 45 unique, 2 tied best and 1 non-best result. No historical objectives are changed.

All paired tests, including null and reversed effects, are retained. Bootstrap intervals are pointwise, whereas p values use full-suite Holm correction. Parallel-process runtime is not an isolated latency benchmark. The manuscript is intentionally bounded by these findings.
