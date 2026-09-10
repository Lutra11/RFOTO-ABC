# Reproduction utilities

- `validate_release.py`: verify frozen inputs, raw records, exact manuscript PDF hashes, PNG previews, and the Tables 5–15 workbook.
- `core_runner.py`: summarize or replay the four revision groups on frozen instances.
- `reanalyze.py`: recompute paired tests and corrected best counts under `outputs/`.
- `historical_suite.py`, `historical_replay.py`: run the documented historical protocols without overwriting recorded results.
- `regenerate_figures.py`, `historical_figures.py`, `workload_figure.py`: create diagnostic figure reproductions under ignored `outputs/`; author-approved manuscript figures remain unchanged.
- `preprocess_alibaba.py`: rebuild workload profiles from the external Alibaba archives.

The immutable revision protocol/backend remains under `../experiments/revision_20260909/`. Runtime caches, LaTeX build products, spreadsheet previews, generated package inventories, and other internal QA artifacts are not versioned.
