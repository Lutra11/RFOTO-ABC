# Dataset setup

This repository keeps code and large datasets separate. The `git-content/datasets/` directory contains only this guide. Raw archives, processed arrays, wireless-channel files, and third-party specifications are not stored in Git.

Download the complete dataset package from [Google Drive](https://drive.google.com/drive/folders/170xFNEo1FpDJooKtJf-NQGi5fYDOoK-M). The terms and citation requirements of Alibaba Cluster Trace, 3GPP documents, and the individual files in the package continue to apply.

## Directory layout

The recommended Windows layout is:

```text
C:\RFOTO-ABC\
├── git-content\                 # GitHub repository
│   ├── algorithm\
│   ├── experiments\
│   ├── datasets\
│   │   └── DATASET.md           # the only dataset file tracked by Git
│   └── ...
└── datasets\                    # complete downloaded package, outside Git
    ├── compute_workload\
    ├── processed\
    ├── wireless_channel\
    └── README.md
```

`C:\RFOTO-ABC\git-content\datasets` is the public setup guide. `C:\RFOTO-ABC\datasets` contains the files read by experiments. The code uses the sibling `../datasets` directory by default, so the recommended layout requires no code changes.

If the package is stored elsewhere, set `RFOTO_DATASETS_DIR`.

```powershell
Set-Location C:\RFOTO-ABC\git-content
$env:RFOTO_DATASETS_DIR = 'D:\research-data\RFOTO-ABC-datasets'
python tools/validate_release.py
```

```bash
cd /path/to/RFOTO-ABC/git-content
export RFOTO_DATASETS_DIR=/path/to/RFOTO-ABC/datasets
python tools/validate_release.py
```

## Installation

1. Download the complete folder from Google Drive.
2. Extract it without adding an extra nested directory.
3. Confirm that the dataset root directly contains `compute_workload/`, `processed/`, and `wireless_channel/`.
4. Place the directory at `C:\RFOTO-ABC\datasets`, or set `RFOTO_DATASETS_DIR` to its location.
5. Run the validation command from the `git-content` repository root.

The minimum structure required by the experiments is:

```text
datasets/
├── processed/
│   ├── alibaba_workload_profiles.npz
│   └── alibaba_workload_profiles.json
└── wireless_channel/
    ├── generated_v1/
    │   ├── static/s0_static.npz ... s6_static.npz
    │   └── dynamic/s6_dynamic.npz
    └── tools/generate_wireless_dataset.py
```

The complete package also contains optional upstream material:

```text
compute_workload/alibaba_cluster_trace_v2018/
├── raw/batch_task.tar.gz
├── raw/machine_meta.tar.gz
├── raw/machine_usage.tar.gz
└── docs/

wireless_channel/3gpp_tr_38_901/spec/tr_138901v190200p.pdf
```

## Dataset roles

| File or directory | Role | Required |
|---|---|---|
| `processed/alibaba_workload_profiles.npz` | Task-compute demand and background server-load profiles derived from Alibaba Cluster Trace v2018 | Yes |
| `wireless_channel/generated_v1/static/*.npz` | Channel and reliability inputs for static scenarios S0–S6 | Yes |
| `wireless_channel/generated_v1/dynamic/s6_dynamic.npz` | Input for the dynamic S6 experiment | Dynamic experiment only |
| `wireless_channel/tools/generate_wireless_dataset.py` | Wireless-scenario generation and frozen-input verification | Full validation only |
| `compute_workload/.../raw/*.tar.gz` | Original Alibaba archives used to rebuild the processed workload pool | Rebuilding only |
| `tr_138901v190200p.pdf` | Reference for the 3GPP TR 38.901 model | No |

Alibaba traces provide task arrivals, computation demand, and background server load. Wireless topology, channels, and reliability are independently simulated using 3GPP-inspired models with Rayleigh and Rician fading. The wireless inputs are not field measurements from a deployed MEC system.

## Validation and experiments

Run these commands from `git-content`:

```powershell
python -c "from algorithm.rfoto_core import DATASETS_ROOT; print(DATASETS_ROOT)"
python tools/validate_release.py
python experiments/01_comparison.py
python experiments/02_ablation.py
python experiments/03_sensitivity.py
python experiments/04_generalization.py
```

The default experiment commands print the corresponding result tables from the Excel workbook.

To rebuild the workload pool from the original Alibaba archives:

```powershell
python tools/preprocess_alibaba.py
```

The preprocessing script reads `compute_workload/alibaba_cluster_trace_v2018/raw/` and writes to `processed/` under the external dataset root. Use `--raw-dir` and `--output-dir` to override those paths.

## Integrity checks

| File | SHA-256 |
|---|---|
| `processed/alibaba_workload_profiles.npz` | `3fa1f367419fc8fe2e288159979effa7897b425ab133a6a24fd61937f66d32a6` |
| `wireless_channel/tools/generate_wireless_dataset.py` | `9b2e10d6145ed56d4afa869982cdc723574d70fe4601e0489800f5872bb40d5e` |

Alibaba archive checksums:

| File | Bytes | SHA-256 |
|---|---:|---|
| `batch_task.tar.gz` | 130,310,549 | `7c4b32361bd1ec2083647a8f52a6854a03bc125ca5c202652316c499fbf978c6` |
| `machine_meta.tar.gz` | 92,432 | `b5b1b786b22cd413a3674b8f2ebfb2f02fac991c95df537f363ef2797c8f6d55` |
| `machine_usage.tar.gz` | 1,774,523,160 | `3e6ee87fd204bb85b9e234c5c75a5096580fdabc8f085b224033080090753a7a` |

Upstream references: [Alibaba Cluster Trace v2018](https://github.com/alibaba/clusterdata/tree/master/cluster-trace-v2018), [3GPP TR 38.901 archive](https://www.3gpp.org/ftp/Specs/archive/38_series/38.901/), and [ETSI V19.2.0 PDF](https://www.etsi.org/deliver/etsi_tr/138900_138999/138901/19.02.00_60/tr_138901v190200p.pdf).
