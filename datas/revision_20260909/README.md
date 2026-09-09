# Frozen revision evidence

- `frozen_inputs.json`: original locally frozen protocol/source/profile and 24 historical CSV hashes. It is not a public preregistration.
- `instance_manifest.json`: 180 unique task/channel inputs, seeds, hashes and relative paths.
- `instances/controlled/`: 60 instances for matched initialization and component interventions.
- `instances/frozen_test/`: 120 other instances for frozen configurations.
- `run_records/`: 2040 JSON files. Each includes `metrics`, `initial_objectives`, `trace_fe`, `trace_objective`.
- `revision_raw.csv`: all run metrics in one flat table.
- `analysis/`: group summaries, 84 controlled contrasts, 24 frozen contrasts, six reverse-oriented temperature contrasts from that same family, corrected historical best counts and audit metadata.
- `preflight_validation.json`: six exact original-optimizer replay checks and representation validation.

The raw CSV SHA-256 is `d9e1c943ffac3bb67ac27a105a00be981ca7c713e8bacad1435267e20b0e0f63`.
Portable replay: `python tools/core_runner.py --group all --rerun` from the repository root. Group overlap is removed by the `all` job list. Fresh means new simulator instances sharing the historical workload profile and generator, not a new measured wireless dataset.
