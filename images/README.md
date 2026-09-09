# Current manuscript figures

Every listed base name has both `png/<name>.png` (600 dpi) and `pdf/<name>.pdf` (vector). Plot labels are English. The files are the exact checked manuscript figures, only renamed into a single pair of folders.

| Figure | Base name | Source |
|---|---|---|
| 1 | Fig01_Workload_Mapping | Processed workload, scenario builder, exp422 mapping validation |
| 2 | Fig02_Main_Comparison | exp48 main results |
| 3 | Fig03_Advanced_Comparison | exp423 raw objectives and paired ranks |
| 4 | Fig04_Matched_Initialization | Revision 1000-FE run traces; 20 instances/stratum |
| 5 | Fig05_Ablation | exp414 common-weight rescoring and exp420 resource skew |
| 6 | Fig06_Controlled_Ablation | Revision controlled contrasts, greedy, 1000 FE |
| 7 | Fig07_Sensitivity | exp415 fixed-objective sensitivity |
| 8 | Fig08_Frozen_Temperature | Revision test means/standard errors |
| 9 | Fig09_Scenario_Transfer | exp417 observed-state reoptimization |
| 10 | Fig10_Frozen_Test | Revision test means and paired contrasts |

Original recordings are in `../datas/`. Figure 4 uses mean relative trajectories with no uncertainty band. Figure 6 and right panel of Figure 10 use pointwise paired bootstrap intervals. Figure 8 uses standard errors. The other historical error bars use SD, as documented in the manuscript. Do not interpret an SD bar or pointwise interval as a multiple-comparison-adjusted confidence region.

Use `python tools/regenerate_figures.py` to rebuild plots in ignored `outputs/regenerated_figures/` without replacing these frozen manuscript images. Display-only preview plots with substituted values and outdated duplicate exports are excluded.
