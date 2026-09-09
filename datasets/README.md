# Datasets

Experiments use Alibaba Cluster Trace v2018-derived compute profiles and separately simulated 3GPP-inspired Rayleigh/Rician channels. This is not an end-to-end measured wireless MEC trace.

- `processed/`: the exact 100,000-task workload pool and bounded machine-usage sample used by the scenario builder.
- `wireless_channel/generated_v1/`: static S0–S6 and S6 dynamic inputs plus parameters/codebook.
- `wireless_channel/tools/`: simulator and loader.
- `compute_workload/alibaba_cluster_trace_v2018/docs/`: original source schema and trace description.
- The revision's 180 fresh task/channel NPZ instances are in `../datas/revision_20260909/instances/`.

Raw archives are downloaded separately using [DATASET.md](DATASET.md). Default sampled machine CPU counts are all 96, mapped to the same default server CPU capacity; the sample does not independently demonstrate diverse server CPU capacities. Input sizes, deadlines, priorities, reliability requirements and task counts are scenario-generated. Arrival scale is not directly a replay of Alibaba arrival times.
