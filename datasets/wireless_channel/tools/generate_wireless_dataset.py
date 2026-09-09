#!/usr/bin/env python3
"""Generate a reproducible RFOTO-ABC wireless-channel benchmark.

The generator uses a 3GPP TR 38.901-inspired UMi Street Canyon model:

* distance-dependent LOS probability and UMi path loss;
* log-normal shadow fading;
* additional stochastic blockage loss;
* Rician fast fading for effective LOS links;
* Rayleigh fast fading for NLOS or blocked links;
* finite-retransmission reliability derived from success probability.

Only NumPy and the Python standard library are required.  The output uses
compressed NPZ files so that the complete benchmark can be loaded without a
database or optional dataframe packages.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


DATASET_VERSION = "rfoto-wireless-v1"
DEFAULT_SEED = 20260820

BANDWIDTH_GRID_HZ = np.asarray(
    [0.10e6, 0.25e6, 0.50e6, 1.00e6, 2.00e6, 5.00e6, 10.00e6],
    dtype=np.float64,
)
GAMMA_GRID_DB = np.asarray([-3.0, 0.0, 3.0, 6.0, 10.0], dtype=np.float64)
REFERENCE_BANDWIDTH_INDEX = 3
REFERENCE_GAMMA_INDEX = 2

FC_GHZ = 3.5
H_BS_M = 10.0
H_UT_M = 1.5
NOISE_FIGURE_DB = 7.0
THERMAL_NOISE_DBM_PER_HZ = -174.0
NOISE_PSD_W_PER_HZ = 10.0 ** (
    (THERMAL_NOISE_DBM_PER_HZ + NOISE_FIGURE_DB - 30.0) / 10.0
)
REFERENCE_INTERFERENCE_BANDWIDTH_HZ = 1.0e6


@dataclass(frozen=True)
class Scenario:
    name: str
    users: int
    servers: int
    area_side_m: float
    blockage_probability: float
    inr_db_low: float
    inr_db_high: float
    description: str


SCENARIOS = (
    Scenario("S0", 10, 3, 250.0, 0.01, -8.0, 0.0, "small exact-solver benchmark"),
    Scenario("S1", 20, 3, 300.0, 0.02, -7.0, 2.0, "low-load stable channel"),
    Scenario("S2", 50, 5, 400.0, 0.05, -5.0, 5.0, "regular fading main benchmark"),
    Scenario("S3", 100, 5, 500.0, 0.08, -3.0, 7.0, "high-load resource competition"),
    Scenario("S4", 100, 8, 600.0, 0.25, -2.0, 10.0, "strong fading and blockage stress"),
    Scenario("S5", 150, 8, 700.0, 0.12, -4.0, 8.0, "large heterogeneous benchmark"),
    Scenario("S6", 200, 10, 800.0, 0.15, -3.0, 10.0, "large-scale and dynamic benchmark"),
)


def parse_args() -> argparse.Namespace:
    script_path = Path(__file__).resolve()
    default_output = script_path.parents[1] / "generated_v1"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--static-instances", type=int, default=30)
    parser.add_argument("--mc-samples", type=int, default=256)
    parser.add_argument("--dynamic-episodes", type=int, default=3)
    parser.add_argument("--dynamic-slots", type=int, default=50)
    parser.add_argument("--skip-dynamic", action="store_true")
    return parser.parse_args()


def los_probability_umi(distance_2d_m: np.ndarray) -> np.ndarray:
    """3GPP UMi Street Canyon LOS probability."""
    d = np.maximum(distance_2d_m.astype(np.float64), 1.0)
    return np.minimum(18.0 / d, 1.0) * (1.0 - np.exp(-d / 36.0)) + np.exp(-d / 36.0)


def umi_pathloss_db(
    distance_2d_m: np.ndarray,
    is_los: np.ndarray,
) -> np.ndarray:
    """UMi Street Canyon path loss for 10 m <= d_2D <= 5 km."""
    d2d = np.clip(distance_2d_m.astype(np.float64), 10.0, 5000.0)
    d3d = np.sqrt(d2d**2 + (H_BS_M - H_UT_M) ** 2)
    speed_of_light = 299_792_458.0
    fc_hz = FC_GHZ * 1.0e9
    d_bp = 4.0 * (H_BS_M - 1.0) * (H_UT_M - 1.0) * fc_hz / speed_of_light

    pl_los_1 = 32.4 + 21.0 * np.log10(d3d) + 20.0 * math.log10(FC_GHZ)
    pl_los_2 = (
        32.4
        + 40.0 * np.log10(d3d)
        + 20.0 * math.log10(FC_GHZ)
        - 9.5 * math.log10(d_bp**2 + (H_BS_M - H_UT_M) ** 2)
    )
    pl_los = np.where(d2d <= d_bp, pl_los_1, pl_los_2)
    pl_nlos_raw = (
        22.4
        + 35.3 * np.log10(d3d)
        + 21.3 * math.log10(FC_GHZ)
        - 0.3 * (H_UT_M - 1.5)
    )
    pl_nlos = np.maximum(pl_los, pl_nlos_raw)
    return np.where(is_los, pl_los, pl_nlos)


def make_server_positions(scenario: Scenario, rng: np.random.Generator) -> np.ndarray:
    """Place one server near the center and the rest on two staggered rings."""
    m = scenario.servers
    center = scenario.area_side_m / 2.0
    positions = np.empty((m, 2), dtype=np.float64)
    positions[0] = (center, center)
    if m > 1:
        angles = np.linspace(0.0, 2.0 * math.pi, m - 1, endpoint=False)
        radius = scenario.area_side_m * (0.30 if m <= 5 else 0.36)
        positions[1:, 0] = center + radius * np.cos(angles)
        positions[1:, 1] = center + radius * np.sin(angles)
    jitter = rng.normal(0.0, scenario.area_side_m * 0.012, size=positions.shape)
    positions = np.clip(positions + jitter, 5.0, scenario.area_side_m - 5.0)
    return positions.astype(np.float32)


def make_user_positions(scenario: Scenario, rng: np.random.Generator) -> np.ndarray:
    margin = 5.0
    return rng.uniform(
        margin,
        scenario.area_side_m - margin,
        size=(scenario.users, 2),
    ).astype(np.float32)


def sample_rician_power(k_linear: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    z1 = rng.standard_normal(k_linear.shape)
    z2 = rng.standard_normal(k_linear.shape)
    return ((z1 + np.sqrt(2.0 * k_linear)) ** 2 + z2**2) / (2.0 * (k_linear + 1.0))


def estimate_success_grid(
    threshold_grid: np.ndarray,
    effective_los: np.ndarray,
    rician_k_db: np.ndarray,
    rng: np.random.Generator,
    mc_samples: int,
    chunk_size: int = 256,
) -> np.ndarray:
    """Estimate q=P(fading power >= threshold) over bandwidth/SINR grids."""
    original_shape = threshold_grid.shape[:-2]
    grid_shape = threshold_grid.shape[-2:]
    thresholds = threshold_grid.reshape((-1, grid_shape[0] * grid_shape[1])).astype(np.float64)
    los_flat = effective_los.reshape(-1)
    k_db_flat = rician_k_db.reshape(-1).astype(np.float64)
    q = np.exp(-np.clip(thresholds, 0.0, 745.0))
    q[thresholds > 745.0] = 0.0

    los_indices = np.flatnonzero(los_flat)
    for start in range(0, los_indices.size, chunk_size):
        idx = los_indices[start : start + chunk_size]
        k = 10.0 ** (k_db_flat[idx] / 10.0)
        z1 = rng.standard_normal((idx.size, mc_samples))
        z2 = rng.standard_normal((idx.size, mc_samples))
        power = ((z1 + np.sqrt(2.0 * k)[:, None]) ** 2 + z2**2) / (
            2.0 * (k + 1.0)[:, None]
        )
        comparison = power[:, :, None] >= thresholds[idx, None, :]
        q[idx] = comparison.mean(axis=1)

    return q.reshape(original_shape + grid_shape).astype(np.float32)


def reflect_positions(
    positions: np.ndarray,
    velocities: np.ndarray,
    lower: float,
    upper: float,
) -> tuple[np.ndarray, np.ndarray]:
    for axis in range(2):
        below = positions[:, axis] < lower
        positions[below, axis] = 2.0 * lower - positions[below, axis]
        velocities[below, axis] *= -1.0
        above = positions[:, axis] > upper
        positions[above, axis] = 2.0 * upper - positions[above, axis]
        velocities[above, axis] *= -1.0
    return positions, velocities


def generate_link_state(
    scenario: Scenario,
    user_xy_m: np.ndarray,
    server_xy_m: np.ndarray,
    tx_power_w: np.ndarray,
    rng: np.random.Generator,
    mc_samples: int,
    temporal_state: dict[str, np.ndarray] | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    delta = user_xy_m[:, None, :].astype(np.float64) - server_xy_m[None, :, :].astype(np.float64)
    distance_2d_m = np.maximum(np.linalg.norm(delta, axis=-1), 10.0)
    distance_3d_m = np.sqrt(distance_2d_m**2 + (H_BS_M - H_UT_M) ** 2)
    p_los = los_probability_umi(distance_2d_m)

    if temporal_state is None:
        los_anchor = rng.random(distance_2d_m.shape)
        blocked = rng.random(distance_2d_m.shape) < scenario.blockage_probability
        shadow_z = rng.standard_normal(distance_2d_m.shape)
        inr_db = rng.uniform(scenario.inr_db_low, scenario.inr_db_high, size=distance_2d_m.shape)
    else:
        los_anchor = temporal_state["los_anchor"]
        previous_blocked = temporal_state["blocked"]
        p_stay_blocked = 0.85
        p_enter = scenario.blockage_probability * (1.0 - p_stay_blocked) / max(
            1.0 - scenario.blockage_probability, 1.0e-9
        )
        blocked = np.where(
            previous_blocked,
            rng.random(distance_2d_m.shape) < p_stay_blocked,
            rng.random(distance_2d_m.shape) < p_enter,
        )
        shadow_z = 0.95 * temporal_state["shadow_z"] + math.sqrt(1.0 - 0.95**2) * rng.standard_normal(
            distance_2d_m.shape
        )
        inr_mid = 0.5 * (scenario.inr_db_low + scenario.inr_db_high)
        inr_db = inr_mid + 0.90 * (temporal_state["inr_db"] - inr_mid) + rng.normal(
            0.0, 1.0, size=distance_2d_m.shape
        )
        inr_db = np.clip(inr_db, scenario.inr_db_low, scenario.inr_db_high)

    geometric_los = los_anchor < p_los
    effective_los = geometric_los & ~blocked
    pathloss_db = umi_pathloss_db(distance_2d_m, geometric_los)
    shadow_sigma_db = np.where(geometric_los, 4.0, 7.82)
    shadow_fading_db = shadow_z * shadow_sigma_db
    blockage_loss_db = np.where(
        blocked,
        np.clip(rng.normal(20.0, 5.0, size=distance_2d_m.shape), 10.0, 35.0),
        0.0,
    )
    total_loss_db = pathloss_db + shadow_fading_db + blockage_loss_db
    large_scale_gain = 10.0 ** (-total_loss_db / 10.0)

    rician_k_db = np.where(
        effective_los,
        np.clip(13.0 - 0.018 * distance_2d_m + rng.normal(0.0, 2.0, distance_2d_m.shape), 0.0, 15.0),
        np.nan,
    )
    fading_power = rng.exponential(1.0, size=distance_2d_m.shape)
    if np.any(effective_los):
        k_linear = 10.0 ** (rician_k_db[effective_los] / 10.0)
        fading_power[effective_los] = sample_rician_power(k_linear, rng)
    instantaneous_gain = large_scale_gain * fading_power

    noise_ref_w = NOISE_PSD_W_PER_HZ * REFERENCE_INTERFERENCE_BANDWIDTH_HZ
    interference_w = noise_ref_w * 10.0 ** (inr_db / 10.0)
    gamma_linear = 10.0 ** (GAMMA_GRID_DB / 10.0)
    receiver_noise_w = NOISE_PSD_W_PER_HZ * BANDWIDTH_GRID_HZ
    denominator = tx_power_w[:, None] * large_scale_gain
    threshold_grid = (
        (receiver_noise_w[None, None, :, None] + interference_w[:, :, None, None])
        * gamma_linear[None, None, None, :]
        / np.maximum(denominator[:, :, None, None], 1.0e-300)
    )
    q_grid = estimate_success_grid(
        threshold_grid,
        effective_los,
        rician_k_db,
        rng,
        mc_samples,
    )
    q_ref = q_grid[..., REFERENCE_BANDWIDTH_INDEX, REFERENCE_GAMMA_INDEX]
    rho_ref_k3 = 1.0 - (1.0 - q_ref) ** 3

    next_temporal_state = {
        "los_anchor": los_anchor,
        "blocked": blocked,
        "shadow_z": shadow_z,
        "inr_db": inr_db,
    }
    arrays = {
        "distance_2d_m": distance_2d_m.astype(np.float32),
        "distance_3d_m": distance_3d_m.astype(np.float32),
        "los_probability": p_los.astype(np.float32),
        "geometric_los": geometric_los.astype(np.uint8),
        "blocked": blocked.astype(np.uint8),
        "effective_los": effective_los.astype(np.uint8),
        "pathloss_db": pathloss_db.astype(np.float32),
        "shadow_fading_db": shadow_fading_db.astype(np.float32),
        "blockage_loss_db": blockage_loss_db.astype(np.float32),
        "large_scale_gain": large_scale_gain.astype(np.float32),
        "rician_k_db": rician_k_db.astype(np.float32),
        "instantaneous_fading_power": fading_power.astype(np.float32),
        "instantaneous_channel_gain": instantaneous_gain.astype(np.float32),
        "interference_w": interference_w.astype(np.float32),
        "q_success_grid": q_grid,
        "q_ref_b1mhz_gamma3db": q_ref.astype(np.float32),
        "rho_ref_k3": rho_ref_k3.astype(np.float32),
        "link_seed": rng.integers(0, np.iinfo(np.uint32).max, size=distance_2d_m.shape, dtype=np.uint32),
    }
    return arrays, next_temporal_state


def save_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def static_split_codes(instances: int) -> np.ndarray:
    # 0=tuning, 1=validation, 2=test.  For 30 instances this gives 5/5/20.
    tune = max(1, instances // 6)
    validation = max(1, instances // 6)
    codes = np.full(instances, 2, dtype=np.uint8)
    codes[:tune] = 0
    codes[tune : tune + validation] = 1
    return codes


def generate_static_scenario(
    scenario: Scenario,
    instances: int,
    seed: int,
    mc_samples: int,
    output_dir: Path,
) -> dict[str, Any]:
    collected: dict[str, list[np.ndarray]] = {}
    users_all: list[np.ndarray] = []
    servers_all: list[np.ndarray] = []
    powers_all: list[np.ndarray] = []

    for instance_index in range(instances):
        instance_rng = np.random.default_rng(seed + instance_index)
        users = make_user_positions(scenario, instance_rng)
        servers = make_server_positions(scenario, instance_rng)
        tx_power = instance_rng.uniform(0.1, 0.5, size=scenario.users).astype(np.float32)
        link_arrays, _ = generate_link_state(
            scenario,
            users,
            servers,
            tx_power,
            instance_rng,
            mc_samples,
        )
        users_all.append(users)
        servers_all.append(servers)
        powers_all.append(tx_power)
        for key, value in link_arrays.items():
            collected.setdefault(key, []).append(value)

    arrays = {key: np.stack(values, axis=0) for key, values in collected.items()}
    arrays.update(
        {
            "user_xy_m": np.stack(users_all, axis=0),
            "server_xy_m": np.stack(servers_all, axis=0),
            "tx_power_w": np.stack(powers_all, axis=0),
            "bandwidth_grid_hz": BANDWIDTH_GRID_HZ.astype(np.float32),
            "gamma_grid_db": GAMMA_GRID_DB.astype(np.float32),
            "split_code": static_split_codes(instances),
            "instance_seed": np.arange(seed, seed + instances, dtype=np.uint64),
        }
    )
    output_path = output_dir / "static" / f"{scenario.name.lower()}_static.npz"
    save_npz(output_path, arrays)

    q_ref = arrays["q_ref_b1mhz_gamma3db"]
    summary = {
        "file": output_path.as_posix(),
        "scenario": scenario.name,
        "instances": instances,
        "users": scenario.users,
        "servers": scenario.servers,
        "links": int(instances * scenario.users * scenario.servers),
        "mean_q_ref": float(np.mean(q_ref)),
        "p05_q_ref": float(np.quantile(q_ref, 0.05)),
        "mean_rho_ref_k3": float(np.mean(arrays["rho_ref_k3"])),
        "blocked_fraction": float(np.mean(arrays["blocked"])),
        "effective_los_fraction": float(np.mean(arrays["effective_los"])),
    }
    return summary


def make_initial_velocities(users: int, rng: np.random.Generator) -> np.ndarray:
    vehicle = rng.random(users) < 0.20
    speed = np.where(vehicle, rng.uniform(5.0, 15.0, users), rng.uniform(0.5, 1.8, users))
    angle = rng.uniform(0.0, 2.0 * math.pi, users)
    return np.column_stack((speed * np.cos(angle), speed * np.sin(angle))).astype(np.float32)


def generate_dynamic_s6(
    scenario: Scenario,
    episodes: int,
    slots: int,
    seed: int,
    mc_samples: int,
    output_dir: Path,
) -> dict[str, Any]:
    episode_collections: dict[str, list[np.ndarray]] = {}
    episode_users: list[np.ndarray] = []
    episode_servers: list[np.ndarray] = []
    episode_powers: list[np.ndarray] = []
    episode_velocities: list[np.ndarray] = []

    for episode_index in range(episodes):
        rng = np.random.default_rng(seed + episode_index)
        users = make_user_positions(scenario, rng)
        servers = make_server_positions(scenario, rng)
        velocities = make_initial_velocities(scenario.users, rng)
        tx_power = rng.uniform(0.1, 0.5, size=scenario.users).astype(np.float32)
        temporal_state = None
        per_slot: dict[str, list[np.ndarray]] = {}
        user_slots: list[np.ndarray] = []
        velocity_slots: list[np.ndarray] = []

        for slot in range(slots):
            if slot > 0:
                velocities += rng.normal(0.0, 0.08, size=velocities.shape).astype(np.float32)
                users = users + velocities
                users, velocities = reflect_positions(
                    users,
                    velocities,
                    5.0,
                    scenario.area_side_m - 5.0,
                )
            link_arrays, temporal_state = generate_link_state(
                scenario,
                users,
                servers,
                tx_power,
                rng,
                mc_samples,
                temporal_state,
            )
            user_slots.append(users.copy())
            velocity_slots.append(velocities.copy())
            for key, value in link_arrays.items():
                per_slot.setdefault(key, []).append(value)

        for key, values in per_slot.items():
            episode_collections.setdefault(key, []).append(np.stack(values, axis=0))
        episode_users.append(np.stack(user_slots, axis=0))
        episode_velocities.append(np.stack(velocity_slots, axis=0))
        episode_servers.append(servers)
        episode_powers.append(tx_power)

    arrays = {key: np.stack(values, axis=0) for key, values in episode_collections.items()}
    arrays.update(
        {
            "user_xy_m": np.stack(episode_users, axis=0),
            "user_velocity_mps": np.stack(episode_velocities, axis=0),
            "server_xy_m": np.stack(episode_servers, axis=0),
            "tx_power_w": np.stack(episode_powers, axis=0),
            "bandwidth_grid_hz": BANDWIDTH_GRID_HZ.astype(np.float32),
            "gamma_grid_db": GAMMA_GRID_DB.astype(np.float32),
            "episode_seed": np.arange(seed, seed + episodes, dtype=np.uint64),
            "time_slot_s": np.asarray(1.0, dtype=np.float32),
        }
    )
    output_path = output_dir / "dynamic" / "s6_dynamic.npz"
    save_npz(output_path, arrays)
    q_ref = arrays["q_ref_b1mhz_gamma3db"]
    return {
        "file": output_path.as_posix(),
        "scenario": "S6-dynamic",
        "episodes": episodes,
        "slots": slots,
        "users": scenario.users,
        "servers": scenario.servers,
        "links": int(episodes * slots * scenario.users * scenario.servers),
        "mean_q_ref": float(np.mean(q_ref)),
        "p05_q_ref": float(np.quantile(q_ref, 0.05)),
        "mean_rho_ref_k3": float(np.mean(arrays["rho_ref_k3"])),
        "blocked_fraction": float(np.mean(arrays["blocked"])),
        "effective_los_fraction": float(np.mean(arrays["effective_los"])),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_summary_csv(path: Path, summaries: list[dict[str, Any]]) -> None:
    fields = sorted({key for summary in summaries for key in summary})
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summaries)


def main() -> None:
    args = parse_args()
    if args.static_instances < 1 or args.mc_samples < 32:
        raise ValueError("static-instances must be >=1 and mc-samples must be >=32")
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []

    seed_sequence = np.random.SeedSequence(args.seed)
    children = seed_sequence.spawn(len(SCENARIOS) + 1)
    for scenario, child in zip(SCENARIOS, children[:-1], strict=True):
        scenario_seed = int(child.generate_state(1, dtype=np.uint32)[0])
        print(f"Generating {scenario.name}: N={scenario.users}, M={scenario.servers} ...", flush=True)
        summaries.append(
            generate_static_scenario(
                scenario,
                args.static_instances,
                scenario_seed,
                args.mc_samples,
                output_dir,
            )
        )

    if not args.skip_dynamic:
        dynamic_seed = int(children[-1].generate_state(1, dtype=np.uint32)[0])
        print(
            f"Generating S6 dynamic: episodes={args.dynamic_episodes}, slots={args.dynamic_slots} ...",
            flush=True,
        )
        summaries.append(
            generate_dynamic_s6(
                SCENARIOS[-1],
                args.dynamic_episodes,
                args.dynamic_slots,
                dynamic_seed,
                args.mc_samples,
                output_dir,
            )
        )

    summary_path = output_dir / "scenario_summary.csv"
    write_summary_csv(summary_path, summaries)

    data_files = sorted(output_dir.rglob("*.npz"))
    checksums = {str(path.relative_to(output_dir)).replace("\\", "/"): sha256_file(path) for path in data_files}
    manifest = {
        "dataset_version": DATASET_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "generator": str(Path(__file__).resolve()),
        "global_seed": args.seed,
        "static_instances_per_scenario": args.static_instances,
        "dynamic_episodes": 0 if args.skip_dynamic else args.dynamic_episodes,
        "dynamic_slots_per_episode": 0 if args.skip_dynamic else args.dynamic_slots,
        "monte_carlo_samples_for_rician_q": args.mc_samples,
        "carrier_frequency_ghz": FC_GHZ,
        "channel_scenario": "3GPP TR 38.901-inspired UMi Street Canyon",
        "noise_figure_db": NOISE_FIGURE_DB,
        "noise_psd_w_per_hz": NOISE_PSD_W_PER_HZ,
        "bandwidth_grid_hz": BANDWIDTH_GRID_HZ.tolist(),
        "gamma_grid_db": GAMMA_GRID_DB.tolist(),
        "q_reference": "bandwidth=1 MHz, gamma=3 dB",
        "split_codes": {"0": "tuning", "1": "validation", "2": "test"},
        "scenarios": [asdict(scenario) for scenario in SCENARIOS],
        "summaries": summaries,
        "sha256": checksums,
    }
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

    print(f"Generated {len(data_files)} NPZ files in {output_dir}", flush=True)


if __name__ == "__main__":
    main()
