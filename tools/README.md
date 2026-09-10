# Reproduction utilities

- `validate_release.py`: verify the retained CSV count, absence of data JSON files, exact manuscript PDF hashes, PNG previews, and the Tables 5–15 workbook.
- `core_runner.py`: print Tables 5–15 from the Excel workbook by experiment group.
- `historical_suite.py`, `historical_replay.py`: run the documented historical protocols without overwriting recorded results.
- `regenerate_figures.py`, `historical_figures.py`, `workload_figure.py`: create diagnostic figure reproductions under ignored `outputs/`; author-approved manuscript figures remain unchanged.
- `preprocess_alibaba.py`: rebuild workload profiles from the external Alibaba archives.

Runtime caches, LaTeX build products, spreadsheet previews, generated package inventories, and other internal QA artifacts are not versioned.
