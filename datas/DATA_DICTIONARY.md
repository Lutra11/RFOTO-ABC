# Result-file mapping

| Current table | Source | Transformation |
|---|---|---|
| 7 Main | `raw_results/exp48_main_comparison.csv` | Scenario/method mean objective |
| 8 Advanced | `revision_20260909/analysis/advanced_corrected_best_counts.csv` | Corrected unique/tied/non-best counts; 48 paired blocks |
| 9 Matched | `revision_20260909/revision_raw.csv` | Controlled means by scene, budget, initialization and method |
| 10 Historical ablation | `raw_results/exp414_ablation.csv` | Saved components rescored with (0.25,0.15,0.20,0.25,0.15) |
| 11 Controlled ablation | `revision_20260909/revision_raw.csv` | Greedy-initialized fixed-objective intervention means |
| 12 Sensitivity | `raw_results/exp415_sensitivity.csv` | Fixed-objective sweep means/SDs; objective-weight sweep is separate |
| 13 Temperature | `revision_20260909/analysis/frozen_temperature_contrasts.csv` and raw revision | Paired gains, pointwise CI, Holm p, deadline rates |
| 14 Transfer | `raw_results/exp417_ood.csv` | Means/SDs with condition labels aligned to actual intervention |
| 15 Frozen test | `revision_20260909/revision_raw.csv` | Mean/SD by scene/method/temperature, all five settings |
| 16 Scale | `raw_results/exp413_scalability.csv` | RFOTO objective/runtime mean/SD by scale |

Other historical files retain small-reference validation, convergence, reliability stress, fairness tradeoffs, resource scarcity, dynamic warm-start, paired statistics and failure/mapping diagnostics. They are supplementary evidence and must not be represented as extra independent replications of the core revision.

Field definitions are in `../CODEBOOK.md`. `table_index.json` records current table notes and source paths. `tools/build_tables.py` is the executable mapping.
