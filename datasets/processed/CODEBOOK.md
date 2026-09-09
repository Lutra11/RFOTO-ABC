# Alibaba-derived workload profile codebook

`alibaba_workload_profiles.npz` is a compact sampling pool derived from Alibaba
Cluster Trace v2018. It is used to construct compute demand and background-load
heterogeneity for the RFOTO-ABC scenarios.

## Arrays

| Array | Shape in packaged file | Unit | Meaning |
|---|---:|---|---|
| `start_time_s` | `(100000,)` | s | Task start time in the Alibaba trace sampling window. |
| `duration_s` | `(100000,)` | s | Task duration after clipping/cleaning. |
| `plan_cpu` | `(100000,)` | normalized/requested CPU | Planned CPU demand from batch-task records. |
| `plan_mem` | `(100000,)` | normalized/requested memory | Planned memory demand from batch-task records. |
| `instance_num` | `(100000,)` | count | Number of instances associated with a task record. |
| `task_type` | `(100000,)` | categorical | Alibaba task type code. |
| `independent_task` | `(100000,)` | binary | Indicator for independent task records used in sampling. |
| `compute_cycles` | `(100000,)` | cycles | RFOTO scenario compute demand derived from Alibaba task profiles. |
| `machine_cpu_num` | `(4034,)` | core-equivalent | Machine CPU capacity profile. |
| `machine_mem_size` | `(4034,)` | memory unit | Machine memory capacity profile. |
| `usage_timestamp_s` | `(100000,)` | s | Timestamp samples from machine-usage records. |
| `machine_cpu_util_percent` | `(100000,)` | % | Background CPU utilization samples used for queue-delay mapping. |
| `machine_mem_util_percent` | `(100000,)` | % | Background memory utilization samples. |
| `machine_net_in` | `(100000,)` | trace unit | Inbound network-use samples. |
| `machine_net_out` | `(100000,)` | trace unit | Outbound network-use samples. |

## Interpretation

The Alibaba-derived profile is not a mobile wireless trace. In the RFOTO-ABC
experiments it provides compute-cycle demand, server capacity heterogeneity, and
background-load/queue-delay heterogeneity. Wireless channels are generated
separately under `datasets/wireless_channel/generated_v1/`.
