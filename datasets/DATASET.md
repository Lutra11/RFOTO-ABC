# Data acquisition and preprocessing

The checked-in processed data and generated inputs suffice to replay the experiments. To rebuild the workload pool, obtain only the following three archives from the [Alibaba v2018 source](https://github.com/alibaba/clusterdata/tree/master/cluster-trace-v2018). Its official download script is [fetchData.sh](https://github.com/alibaba/clusterdata/blob/master/cluster-trace-v2018/fetchData.sh). Consult its current download endpoints; the full six-file dataset is unnecessary.

| File | Bytes in the original local download | SHA-256 |
|---|---:|---|
| batch_task.tar.gz | 130310549 | `7c4b32361bd1ec2083647a8f52a6854a03bc125ca5c202652316c499fbf978c6` |
| machine_meta.tar.gz | 92432 | `b5b1b786b22cd413a3674b8f2ebfb2f02fac991c95df537f363ef2797c8f6d55` |
| machine_usage.tar.gz | 1774523160 | `3e6ee87fd204bb85b9e234c5c75a5096580fdabc8f085b224033080090753a7a` |

Place them in a local raw-data directory, then run:

```bash
python tools/preprocess_alibaba.py --raw-dir /path/to/raw --output-dir outputs/rebuilt_profiles
```

Verify rebuilt arrays against `datasets/processed/alibaba_workload_profiles.npz` before substituting data. ZIP container timestamps can differ even when NPZ arrays match. The frozen experiment requires the exact archived profile. Seed=20260820; 100,000 valid terminated tasks are sampled from 13,289,030 valid records in 14,295,731 scanned rows. Machine usage takes a reservoir of 100,000 from the first configured 2,000,000 valid rows (294 machines). See the JSON processing metadata for clipping/normalization quantiles.

Compute mapping: `log1p(plan_cpu/100 * duration)`, sample 1st/99th percentile scaling, mapped to 0.2–5 Gcycles. Queue delays are transformed from CPU utilization. Other workload attributes remain scenario-generated.

Wireless model reference: [3GPP TR 38.901 archive](https://www.3gpp.org/ftp/Specs/archive/38_series/38.901/) and the [ETSI V19.2.0 PDF](https://www.etsi.org/deliver/etsi_tr/138900_138999/138901/19.02.00_60/tr_138901v190200p.pdf). The document is linked, not redistributed. The generator and seed/configuration manifests are in `wireless_channel/`. Rayleigh/Rician realizations are generated data, not downloadable measured channel traces.

Raw archives were removed from the publication package to avoid large-file and redistribution issues. They remain in the author's local backup. Do not describe `machine_usage`'s bounded scan as a full eight-day unbiased sample.
