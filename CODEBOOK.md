# Data and implementation codebook

All composite objectives are minimized. Raw rates are fractions in [0,1] unless the column explicitly ends in `pct` or `percent`. Delay is in seconds, terminal energy in joules, bandwidth in Hz and CPU in cycles/s. `run` identifies a paired task/channel instance and one optimization seed, not a repeated evaluation of identical data. The two controlled budgets reuse instances.

| Field | Actual implementation meaning |
|---|---|
| `objective` | Dot product of five normalized components and the run's objective weights |
| `t_hat`, `e_hat` | Normalized delay and terminal energy terms |
| `r_hat`, `link_failure_rate` | Mean modeled residual failure probability, `mean(1-reliability)`; not threshold-violation frequency |
| `v_hat` | Normalized deadline-violation penalty |
| `fairness_loss` | `1-jain` for service utilities |
| `success_rate` | Fraction with deadline violation <=1e-12; not empirical packet-delivery success |
| `violation_rate` | Fraction with deadline violation >1e-12 |
| `reliability_mean` | Mean finite-retransmission success probability |
| `feasible` | Reliability-threshold flag in the core; revision runner separately asserts capacity constraints |
| `evaluations` | Actual objective evaluations; includes initialization; rule baseline uses one |
| `initial_objective` | Best decoded objective in the initial candidate population |
| `population_sha256` | Hash of assignment, bandwidth-key and CPU-key arrays |
| `initial_to_final_gain_pct` | 100 × (initial best − final best) / initial best |
| `scout_count`, `accepted_neighbors` | Adapter diagnostics; -1 means unavailable for that method, not a negative count |
| `mean_relative_gain_pct` | Mean over paired instances of 100 × (comparator − reference) / comparator |
| `ci_low_pct`, `ci_high_pct` | Pointwise paired bootstrap 95% interval for that mean relative gain |
| `p_raw`, `p_holm` | Two-sided paired p value and prespecified family-wise Holm adjustment |
| `wins`, `ties`, `losses` | Paired reference versus comparator outcomes; numerical zero tolerance 1e-12 |
| `unique_best`, `tied_best`, `not_best` | Corrected historical multi-method best counts; each row sums to 48 |

`RFOTO-ABC-T16` changes both resource temperatures to 1.6. `Plain-ABC` disables three search-guidance operations, while the decoder and reliability filtering remain shared. `No-risk-sampling` removes task-risk bias but not the feasibility filter. `Uniform-allocation` keeps the original encoding and feasibility repair but changes the resource decoder, including its initial objective.

The historical `Standard-ABC` label is an adapter and is not interchangeable with the revision `Plain-ABC`. Historical `Max-SINR` uses channel-gain ranking. Historical OOD labels describe observed-state interventions as detailed in `REPRODUCIBILITY.md`. `additional_blockage_probability` in the historical stress CSV is an intervention level controlling probability scaling and channel loss, not a separate unobserved blockage draw.

Input arrays: [workload codebook](datasets/processed/CODEBOOK.md), [channel codebook](datasets/wireless_channel/generated_v1/CODEBOOK.md). Current result mapping: [datas/DATA_DICTIONARY.md](datas/DATA_DICTIONARY.md).
