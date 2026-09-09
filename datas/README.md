# Recorded results and current tables

| Location | Contents |
|---|---|
| `raw_results/` | All 24 historical CSV files plus original metadata; original bytes retained |
| `revision_20260909/` | 180 fresh inputs, 2040 run records, raw results, paired statistics and frozen hashes |
| `tables/` | Numeric CSV equivalents of current manuscript experimental Tables 7–16 and their source index |
| `excel/RFOTO_ABC_Main_Results.xlsx` | Ten sheets for Tables 7–16; numeric means, SDs, counts and test results |
| `excel/RFOTO_ABC_Supplementary_Statistics.xlsx` | Full revision records, 84 controlled contrasts, 24 frozen contrasts, the six temperature contrasts and objective-weight sweep |
| `release_manifest.json` | SHA-256/size inventory for the release; excludes itself and local outputs |

Both workbooks use white backgrounds and black fonts. Tables 1–6 are literature/model/setup tables, not new experimental result files. Workbook notes and `tables/table_index.json` preserve sample sizes, budgets and interpretation boundaries.

Old scattershot Excel exports were replaced by these two current workbooks. Historical raw CSVs are not deleted. In particular, the old advanced summary's `win_count` is superseded by `revision_20260909/analysis/advanced_corrected_best_counts.csv`; the original summary remains only to preserve its audit trail.
