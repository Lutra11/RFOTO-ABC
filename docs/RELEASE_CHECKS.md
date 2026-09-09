# Checks for the 9 September 2026 release

The following checks were executed during packaging, not inferred from filenames:

- Seven frozen source/input hashes, 24 historical CSV hashes and all 180 revision-instance hashes matched the original freeze.
- All 2,040 recorded rows matched their JSON metrics, prescribed evaluation counts and non-increasing best-objective traces.
- Seventeen fresh replay executions (13 unique jobs across the four entry points) matched archived initial values, traces and non-runtime metrics. These are smoke checks, not a newly rerun 2,040-job experiment.
- All five regenerated statistical CSV outputs matched the archived tables within numerical tolerance 1e-12.
- Both Excel workbooks were checked cell-by-cell against their numeric input payload: 829 main-result cells and 82,206 supplementary cells. Every styled cell was verified white with black text; no spreadsheet errors, macros or external workbook connections were found. All 15 sheets were visually inspected.
- Ten release PNG/PDF pairs were verified, with PNG metadata at 600 dpi. The portable figure command was executed into a separate output directory without changing release images.
- Python sources parsed successfully. A bounded scan for common credential/private-key patterns found no matches. This is not a general security audit.
- The latest manuscript hash matched the value in `docs/README.md`.

The repository-wide checksum inventory is `datas/release_manifest.json`. Excluded local QA output, runtime caches, duplicate older exports and display-only mockups are recoverable from the author's local pre-cleanup backup. Preserving raw negative results and software-assistance disclosure was part of the evidence-bounded publication check.
