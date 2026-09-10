# Manuscript figures

This directory contains the **14 figures used by the 10 September 2026 English LaTeX manuscript**. Files under `pdf/` are the exact one-page vector assets referenced by LaTeX. Files under `png/` are matching GitHub previews: experimental plots retain 600 dpi metadata and the large framework preview is 150 dpi.

| Manuscript figure | File base name | Recorded source or role |
|---:|---|---|
| 1 | `Framework` | System model and RFOTO-ABC solution workflow |
| 2 | `Fig01_Workload_Mapping` | Alibaba-derived profiles and mapping validation |
| 3 | `Fig02_Main_Comparison` | `exp48_main_comparison.csv`; updated panel-specific y-axis |
| 4 | `Fig03_Advanced_Comparison_a_Replaced` | Author-retained panel plus `exp423` ranks and aggregate gaps |
| 5 | `Fig04_Matched_Initialization` | Revision traces with identical initial populations |
| 6 | `Fig05_Ablation_Single_Panel` | `exp414_ablation.csv`; single retained panel |
| 7 | `Fig06_Controlled_Ablation` | Revision controlled contrasts |
| 8 | `Fig07_Parameter_Sensitivity` | `exp415_sensitivity.csv` |
| 9 | `Fig08_Prespecified_Temperature` | Frozen-temperature contrasts and revision records |
| 10 | `Fig09_Resource_Scarcity` | `exp412_resource_scarcity.csv` |
| 11 | `Fig10_Scenario_Transfer` | `exp417_ood.csv` |
| 12 | `Fig11_Prespecified_Configurations` | Six new-instance groups in revision records |
| 13 | `Fig12_Scalability` | `exp413_scalability.csv` |
| 14 | `Fig13_Dynamic_Warm_Start` | `exp416_dynamic.csv`; corrected dynamic labels |

The validation command verifies every PDF against the SHA-256 recorded by the LaTeX source manifest, checks the one-to-one PDF/PNG filename set, and checks preview resolution. `python tools/regenerate_figures.py` writes diagnostic recreations to ignored `outputs/`; it does not overwrite these author-approved manuscript assets.

Figure 4 and Table 6 retain the author-selected presentation while source-record reconciliation remains pending. Figure 14 summarizes three independent episodes; its 150 correlated slots are not treated as 150 independent replicates.
