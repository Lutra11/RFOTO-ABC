# Manuscript table mapping

| Table | CSV | Upstream evidence | Transformation |
|---:|---|---|---|
| 5 | `tables/Table05_Main.csv` | `raw_results/exp48_main_comparison.csv` | Scenario/method mean composite objective |
| 6 | `tables/Table06_Advanced.csv` | `exp423` results and corrected best-count analysis | Aggregate objective, ranks, exclusive/tied best counts, runtime |
| 7 | `tables/Table07_Matched.csv` | `revision_20260909/revision_raw.csv` | Means by scenario, budget, initialization, and method |
| 8 | `tables/Table08_Ablation.csv` | `raw_results/exp414_ablation.csv` | Saved components rescored under common objective weights |
| 9 | `tables/Table09_Controlled_Ablation.csv` | revision records | Greedy-initialized fixed-objective intervention means |
| 10 | `tables/Table10_Sensitivity.csv` | `raw_results/exp415_sensitivity.csv` | Fixed-objective parameter sweep means and SDs |
| 11 | `tables/Table11_Temperature.csv` | frozen-temperature contrasts and revision records | Paired gains, pointwise CI, Holm p, and deadline rates |
| 12 | `tables/Table12_Transfer.csv` | `raw_results/exp417_ood.csv` | Means and SDs with condition labels aligned to the implemented intervention |
| 13 | `tables/Table13_New_Instances.csv` | revision records | Mean and SD by scenario, method, and temperature |
| 14 | `tables/Table14_Scalability.csv` | `raw_results/exp413_scalability.csv` | RFOTO-ABC objective and runtime by problem scale |
| 15 | `tables/Table15_Dynamic.csv` | `raw_results/exp416_dynamic.csv` | Slot means computed within each episode, then mean/SD across three episodes |

`Table15_Dynamic.csv` reports rates as fractions. The manuscript multiplies deadline rates by 100 for percentage display. Its labels `Cold-RFOTO (alternative seed)` and `Max-gain` correct the implemented meaning of raw labels `Standard-ABC` and `Max-SINR`; raw values are unchanged.

Field definitions are in [`../CODEBOOK.md`](../CODEBOOK.md). `table_index.json` stores the exact table title, upstream paths, sample size, evaluation budget, and interpretation note used by the exporter.
