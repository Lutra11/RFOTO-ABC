# Generated wireless-channel dataset codebook

This folder contains reproducible 3GPP-inspired Rayleigh/Rician wireless-channel
arrays for scenarios S0--S6.

## Static scenario files

Files: `static/s0_static.npz` ... `static/s6_static.npz`.

Typical static shape is `(instances, users, servers)` for link-level arrays.
For example, `s1_static.npz` contains 30 instances, 20 users, and 3 servers.

| Array | Unit | Meaning |
|---|---|---|
| `distance_2d_m` | m | Horizontal user-to-server distance. |
| `distance_3d_m` | m | Three-dimensional user-to-server distance. |
| `los_probability` | probability | 3GPP-inspired line-of-sight probability. |
| `geometric_los` | binary | LOS state sampled from the geometry model. |
| `blocked` | binary | Additional blockage indicator. |
| `effective_los` | binary | LOS state after blockage. |
| `pathloss_db` | dB | Large-scale path loss. |
| `shadow_fading_db` | dB | Shadow-fading component. |
| `blockage_loss_db` | dB | Extra loss due to blockage. |
| `large_scale_gain` | linear | Large-scale channel gain. |
| `rician_k_db` | dB | Rician K-factor; low values approximate Rayleigh fading. |
| `instantaneous_fading_power` | linear | Fast-fading power sample. |
| `instantaneous_channel_gain` | linear | Product of large-scale gain and fast fading. |
| `interference_w` | W | Interference power. |
| `q_success_grid` | probability | Packet success probability over bandwidth and SINR-threshold grids. |
| `q_ref_b1mhz_gamma3db` | probability | Reference success probability at 1 MHz and 3 dB threshold. |
| `rho_ref_k3` | probability | Finite-retransmission success probability for three attempts. |
| `link_seed` | seed | Per-link random seed for reproducibility. |
| `user_xy_m` | m | User coordinates. |
| `server_xy_m` | m | Server coordinates. |
| `tx_power_w` | W | User transmit power. |
| `bandwidth_grid_hz` | Hz | Bandwidth grid for `q_success_grid`. |
| `gamma_grid_db` | dB | SINR-threshold grid for `q_success_grid`. |
| `split_code` | categorical | Internal split label used by the generator. |
| `instance_seed` | seed | Static instance seed. |

## Dynamic scenario file

File: `dynamic/s6_dynamic.npz`.

Dynamic link arrays use shape `(episodes, slots, users, servers)`. User
positions and channel states vary across slots.

Additional dynamic arrays:

| Array | Unit | Meaning |
|---|---|---|
| `user_velocity_mps` | m/s | User mobility vector per slot. |
| `episode_seed` | seed | Dynamic episode seed. |
| `time_slot_s` | s | Slot duration. |

## Model boundary

The generator is 3GPP-inspired and reproduces the mechanisms required by the
RFOTO-ABC experiments: geometry, LOS/NLOS, path loss, shadowing, blockage,
Rayleigh/Rician fading, interference, and retransmission success probability.
It is not a measured cellular-drive-test dataset.
