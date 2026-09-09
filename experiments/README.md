# Four core experiments

1. `01_comparison.py`: Section 4.3.1, overall performance and matched initialization.
2. `02_ablation.py`: Section 4.3.2, fixed-objective interventions and uniform allocation.
3. `03_sensitivity.py`: Section 4.3.3, sensitivity and frozen temperature validation.
4. `04_generalization.py`: Section 4.3.4, fresh scenarios and applicability boundaries.

Run without arguments to summarize archived records. Add `--rerun` for fresh computation of revision jobs and `--max-jobs N` for a smoke test. Outputs remain separate from recorded data. The shared portable dispatcher is `../tools/core_runner.py`; the immutable original protocol/backend is in `revision_20260909/`.

Historical raw diagnostics remain supplementary evidence rather than additional top-level launchers. See `../REPRODUCIBILITY.md` for historical replay and budgets.
