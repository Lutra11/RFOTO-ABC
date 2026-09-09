# Statistical analysis files

`group_summary.csv` contains mean/SD by suite, scenario, budget, initialization, algorithm and resource temperature. `controlled_contrasts.csv` contains 84 paired contrasts (60 method contrasts and 24 initialization contrasts). `frozen_test_contrasts.csv` contains 24 contrasts. `frozen_temperature_contrasts.csv` reverses the orientation of six existing frozen contrasts and uses their original Holm-adjusted p values; it is not a new six-test family.

`advanced_corrected_best_counts.csv` and `historical_ties.json` correct the old row-order tie counting without modifying historical objectives. Counts distinguish unique best, tied best and non-best.

`analysis_audit.json` records the original analysis execution, software version, raw-data hash and original analysis-script hash. For new recomputation use `python tools/reanalyze.py` from the repository root; regenerated files go to `outputs/reanalysis/` for independent comparison.
