# RFOTO-ABC 无线信道数据集 v1

这套数据由 `../tools/generate_wireless_dataset.py` 生成，用于 RFOTO-ABC 的 S0--S6 静态实验、可靠性压力测试、规模扩展和 S6 动态热启动实验。

## 数据规模

- S0--S6：每个场景 30 个独立静态实例；
- S6 动态：3 个 episode，每个 episode 50 个 1 秒时隙；
- 静态链路记录：145,200 条；
- 动态链路记录：300,000 条；
- 每条链路包含 7 个带宽点 × 5 个 SINR 门限的成功概率网格；
- Rician 成功概率使用每条LOS链路256次蒙特卡洛采样估计；Rayleigh成功概率使用解析式。

## 文件

- `static/s0_static.npz` 至 `static/s6_static.npz`：静态场景；
- `dynamic/s6_dynamic.npz`：动态场景；
- `manifest.json`：参数、随机种子、场景配置和数据文件SHA-256；
- `scenario_summary.csv`：各场景成功概率、可靠性和遮挡比例摘要。

## 关键数组

静态文件的链路数组形状为 `[instance, user, server, ...]`，动态文件为 `[episode, slot, user, server, ...]`。

| 数组 | 含义 |
|---|---|
| `user_xy_m`, `server_xy_m` | 用户和服务器二维位置 |
| `distance_2d_m`, `distance_3d_m` | 链路距离 |
| `geometric_los`, `blocked`, `effective_los` | LOS与遮挡状态 |
| `pathloss_db`, `shadow_fading_db`, `blockage_loss_db` | 各类信道损耗 |
| `large_scale_gain` | 不含快衰落的平均信道增益 |
| `instantaneous_channel_gain` | 可直接代入Shannon速率公式的瞬时增益 `h_im` |
| `rician_k_db` | LOS链路的Rician K因子；非LOS链路为NaN |
| `interference_w` | 等效干扰功率 `I_im` |
| `tx_power_w` | 终端发射功率 `p_i` |
| `q_success_grid` | 带宽和SINR门限二维网格上的单次成功概率 |
| `rho_ref_k3` | 1 MHz、3 dB门限、最多3次传输时的完成可靠性 |
| `split_code` | 静态实例划分：0调优、1验证、2测试 |

带宽网格为 `[0.1, 0.25, 0.5, 1, 2, 5, 10] MHz`，SINR门限网格为 `[-3, 0, 3, 6, 10] dB`。

## Python调用

```python
from pathlib import Path
import sys

tools = Path("datasets/wireless_channel/tools")
sys.path.insert(0, str(tools))

from wireless_dataset import (
    finite_retransmission_reliability,
    interpolate_success_probability,
    load_static,
)

root = Path("datasets/wireless_channel/generated_v1")
data = load_static(root, "S2")

# 可以传入与链路形状相同的实际带宽矩阵；这里演示统一1.5 MHz。
q_im = interpolate_success_probability(data, bandwidth_hz=1.5e6, gamma_db=3.0)
rho_im = finite_retransmission_reliability(q_im, max_transmissions=3)
h_im = data["instantaneous_channel_gain"]
interference_im = data["interference_w"]
```

不要在算法间分别重新生成信道；所有对比算法应加载同一实例和同一 `split_code`，以保证配对比较公平。
