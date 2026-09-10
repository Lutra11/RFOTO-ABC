# Reproducibility

## Environment and external data

The revision ran on Windows with Python 3.12.14, NumPy 2.3.5, and SciPy 1.18.0. Install compatible packages with `requirements.txt` or `environment.yml`.

Large dataset payloads are distributed separately. Follow [`datasets/DATASET.md`](datasets/DATASET.md); the code reads the repository's sibling `datasets/` directory by default and accepts `RFOTO_DATASETS_DIR` as an override.

## Commands

| Purpose | Command |
|---|---|
| Validate frozen evidence, figures, and manuscript tables | `python tools/validate_release.py` |
| Summarize a core group | `python experiments/01_comparison.py` (or 02–04) |
| Run a bounded fresh replay | `python experiments/01_comparison.py --rerun --max-jobs 4` |
| Replay all unique revision jobs | `python tools/core_runner.py --group all --rerun` |
| Recompute statistical summaries | `python tools/reanalyze.py` |
| Replay a historical group | `python tools/historical_replay.py main` |

Reruns write to ignored `outputs/` paths and do not replace archived evidence or manuscript assets.

## Revision protocol

- Controlled groups: S2, S4, and S6; 20 fresh instances each; 320 and 1,000 FEs. Greedy initialization has eight methods and random initialization has four.
- Frozen test: S1–S6; 20 independent instances each; five settings. Searches use 320 FEs and the rule uses one evaluation.
- Total: 180 instances and 2,040 records, including 1,920 searches and 120 rules.
- The initial population has 14 candidates and counts toward the FE budget.
- Paired tests use a two-sided Wilcoxon normal approximation with numerical-zero tolerance `1e-12`. Holm correction covers the prespecified 84 controlled and 24 frozen-test contrasts. Pointwise bootstrap intervals use 10,000 paired resamples and seed 20260909.
- Temperature 1.6 was selected before the fresh test using historical S4 exploration. Other optimizers were not evaluated at 1.6.

## Historical protocols

The main comparison uses 30 instances per scenario, with 500 FEs in S1–S3 and 375 FEs in S4–S6. The advanced comparison uses eight instances per scenario and 320 FEs. Ablation uses 20 S4 instances and 400 FEs. Sensitivity uses six repeats per setting and 280 FEs. Transfer uses 15 repeats per condition and 350 FEs. Scaling uses 10 repeats per size and 320 FEs. Rule methods use one evaluation.

The rolling experiment contains three independent 50-slot episodes. Episode-level means, rather than 150 correlated slots, determine the SD in Table 15. The raw dynamic label `Standard-ABC` invoked RFOTO cold-start optimization with another seed and is reported as `Cold-RFOTO (alternative seed)`; raw static Standard-ABC records are unaffected.

## Integrity and interpretation

- `frozen_inputs.json` protects seven frozen sources/inputs and all 24 historical CSVs; `instance_manifest.json` protects the 180 revision inputs.
- `tools/validate_release.py` verifies all 2,040 record summaries, figure-set completeness, exact manuscript PDF hashes, PNG preview resolution, and Table 5–15 coverage.
- Historical adapters and lite optimizers are not certified original-author implementations.
- Common-weight rescoring does not remove the changed-search-objective confound in historical `-F` and `-RF` ablations.
- Stored negative results and boundary cases remain part of the evidence package.
