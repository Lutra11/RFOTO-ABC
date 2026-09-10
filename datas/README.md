# Experimental evidence

The data package preserves full recorded evidence while exposing a small manuscript-facing layer.

| Location | Contents |
|---|---|
| `tables/` | Eleven numeric CSV exports matching manuscript Tables 5–15, plus `table_index.json` |
| `raw_results/` | All 24 historical CSV files and their original metadata |
| `revision_20260909/` | 180 frozen instances, 2,040 run records, raw revision results, paired statistics, and source hashes |

Tables 1–4 describe literature, notation, scenarios, and default parameters, so they are not duplicated as experimental CSVs. `tools/build_tables.py` deterministically rebuilds Tables 5–15 without executing an optimizer.

The previous Excel copies and repository-wide generated manifest were removed because they duplicated authoritative CSV/JSON evidence and increased maintenance noise. No historical observations, negative results, frozen instances, traces, or statistical contrasts were removed.

The old advanced summary's `win_count` is superseded by `revision_20260909/analysis/advanced_corrected_best_counts.csv`; the original file remains for provenance. Dynamic manuscript labels are corrected at export time without changing the underlying `exp416_dynamic.csv` values.
