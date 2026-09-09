# Dataset location and usage / 数据集位置与使用说明

本 Git 仓库采用“代码与大数据分离”的发布方式。`git-content/datasets/` 只跟踪本说明文件，不保存原始数据、处理后的数组、无线信道文件或第三方规范文档。

完整数据集已单独上传至 [Google Drive 数据集目录](https://drive.google.com/drive/folders/170xFNEo1FpDJooKtJf-NQGi5fYDOoK-M)。请遵守 Alibaba Cluster Trace、3GPP 文档及 Google Drive 中各文件适用的许可与引用要求。

## 目录关系

本项目的推荐 Windows 布局如下：

```text
C:\RFOTO-ABC\
├── git-content\                 # GitHub 代码仓库
│   ├── algorithm\
│   ├── experiments\
│   ├── datasets\
│   │   └── DATASET.md           # Git 中唯一的数据集文件
│   └── ...
└── datasets\                    # 从 Google Drive 下载的完整数据，不纳入 Git
    ├── compute_workload\
    ├── processed\
    ├── wireless_channel\
    └── README.md
```

也就是说：

- `C:\RFOTO-ABC\git-content\datasets` 是公开仓库中的说明目录；
- `C:\RFOTO-ABC\datasets` 是实验实际读取的外部数据目录；
- 两者名称相同但用途不同，互为“说明入口”和“数据实体”，不是重复副本；
- `.gitignore` 会阻止下载或链接到仓库目录中的数据文件被误提交。

代码默认将仓库同级的 `../datasets` 作为数据根目录。因此，在上述布局下无需修改代码。若数据放在其他磁盘或目录，请设置环境变量 `RFOTO_DATASETS_DIR`。

PowerShell 示例：

```powershell
Set-Location C:\RFOTO-ABC\git-content
$env:RFOTO_DATASETS_DIR = 'D:\research-data\RFOTO-ABC-datasets'
python tools/validate_release.py
```

Bash 示例：

```bash
cd /path/to/RFOTO-ABC/git-content
export RFOTO_DATASETS_DIR=/path/to/RFOTO-ABC/datasets
python tools/validate_release.py
```

`RFOTO_DATASETS_DIR` 只需在数据不位于仓库同级 `datasets/` 时设置。

## 下载与放置

1. 从上述 Google Drive 链接下载完整目录。
2. 解压后确认数据根目录直接包含 `compute_workload/`、`processed/` 和 `wireless_channel/`，不要多套一层同名压缩包目录。
3. 将该目录放在 `C:\RFOTO-ABC\datasets`，或通过 `RFOTO_DATASETS_DIR` 指向它。
4. 在仓库根目录运行验证命令。

最低运行所需结构如下：

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

完整包还包括以下可选来源材料：

```text
compute_workload/alibaba_cluster_trace_v2018/
├── raw/batch_task.tar.gz
├── raw/machine_meta.tar.gz
├── raw/machine_usage.tar.gz
└── docs/

wireless_channel/3gpp_tr_38_901/spec/tr_138901v190200p.pdf
```

## 数据用途

| 数据 | 项目中的用途 | 是否为运行必需 |
|---|---|---|
| `processed/alibaba_workload_profiles.npz` | 提供由 Alibaba Cluster Trace v2018 构建的任务计算需求与服务器背景负载池 | 是 |
| `wireless_channel/generated_v1/static/*.npz` | S0--S6 静态场景的信道与可靠性输入 | 是 |
| `wireless_channel/generated_v1/dynamic/s6_dynamic.npz` | S6 动态场景输入 | 动态实验需要 |
| `wireless_channel/tools/generate_wireless_dataset.py` | 生成/核对无线场景并复核冻结输入 | 完整验证需要 |
| `compute_workload/.../raw/*.tar.gz` | 从 Alibaba 原始轨迹重建处理后负载池 | 仅重建时需要 |
| `tr_138901v190200p.pdf` | 3GPP TR 38.901 模型参考 | 否 |

Alibaba 数据只用于构造任务到达、计算需求和服务器背景负载。无线拓扑、信道和可靠性由 3GPP 启发的模型以及 Rayleigh/Rician 随机实现独立生成；生成的无线输入不是外部实测 MEC 数据集。

## 验证与运行

在 `git-content` 根目录执行：

```powershell
python -c "from algorithm.rfoto_core import DATASETS_ROOT; print(DATASETS_ROOT)"
python tools/validate_release.py
python experiments/01_comparison.py
python experiments/02_ablation.py
python experiments/03_sensitivity.py
python experiments/04_generalization.py
```

默认实验命令汇总仓库中已有证据；重新计算冻结输入上的实验可使用：

```powershell
python experiments/01_comparison.py --rerun --max-jobs 4
python tools/core_runner.py --group all --rerun
```

若需要从 Alibaba 原始压缩包重建负载池：

```powershell
python tools/preprocess_alibaba.py
```

该脚本默认从外部数据根目录的 `compute_workload/alibaba_cluster_trace_v2018/raw/` 读取，并将结果写入外部数据根目录的 `processed/`。可用 `--raw-dir` 和 `--output-dir` 显式覆盖。

## 完整性检查

冻结实验所用的两个关键文件应满足：

| 文件 | SHA-256 |
|---|---|
| `processed/alibaba_workload_profiles.npz` | `3fa1f367419fc8fe2e288159979effa7897b425ab133a6a24fd61937f66d32a6` |
| `wireless_channel/tools/generate_wireless_dataset.py` | `9b2e10d6145ed56d4afa869982cdc723574d70fe4601e0489800f5872bb40d5e` |

Alibaba 原始压缩包的校验值：

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| `batch_task.tar.gz` | 130,310,549 | `7c4b32361bd1ec2083647a8f52a6854a03bc125ca5c202652316c499fbf978c6` |
| `machine_meta.tar.gz` | 92,432 | `b5b1b786b22cd413a3674b8f2ebfb2f02fac991c95df537f363ef2797c8f6d55` |
| `machine_usage.tar.gz` | 1,774,523,160 | `3e6ee87fd204bb85b9e234c5c75a5096580fdabc8f085b224033080090753a7a` |

上游来源：[Alibaba Cluster Trace v2018](https://github.com/alibaba/clusterdata/tree/master/cluster-trace-v2018)、[3GPP TR 38.901 archive](https://www.3gpp.org/ftp/Specs/archive/38_series/38.901/) 和 [ETSI V19.2.0 PDF](https://www.etsi.org/deliver/etsi_tr/138900_138999/138901/19.02.00_60/tr_138901v190200p.pdf)。
