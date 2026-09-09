"""Loading and interpolation helpers for RFOTO wireless-channel NPZ files."""

from __future__ import annotations

from pathlib import Path

import numpy as np


def load_static(dataset_root: str | Path, scenario: str) -> dict[str, np.ndarray]:
    """Load S0--S6 static data without enabling pickle."""
    scenario_id = scenario.strip().lower()
    if scenario_id not in {f"s{i}" for i in range(7)}:
        raise ValueError("scenario must be one of S0, S1, ..., S6")
    path = Path(dataset_root) / "static" / f"{scenario_id}_static.npz"
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name] for name in archive.files}


def load_dynamic(dataset_root: str | Path) -> dict[str, np.ndarray]:
    """Load the S6 dynamic data."""
    path = Path(dataset_root) / "dynamic" / "s6_dynamic.npz"
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name] for name in archive.files}


def interpolate_success_probability(
    data: dict[str, np.ndarray],
    bandwidth_hz: float | np.ndarray,
    gamma_db: float | np.ndarray,
) -> np.ndarray:
    """Interpolate q over log-bandwidth and linear SINR-threshold grids.

    ``bandwidth_hz`` and ``gamma_db`` may be scalars or arrays broadcastable to
    the link shape, which is ``q_success_grid.shape[:-2]``.
    """
    q_grid = np.asarray(data["q_success_grid"], dtype=np.float64)
    bandwidth_grid = np.asarray(data["bandwidth_grid_hz"], dtype=np.float64)
    gamma_grid = np.asarray(data["gamma_grid_db"], dtype=np.float64)
    link_shape = q_grid.shape[:-2]

    bandwidth = np.broadcast_to(np.asarray(bandwidth_hz, dtype=np.float64), link_shape)
    gamma = np.broadcast_to(np.asarray(gamma_db, dtype=np.float64), link_shape)
    log_grid = np.log(bandwidth_grid)
    log_bandwidth = np.log(np.clip(bandwidth, bandwidth_grid[0], bandwidth_grid[-1]))
    gamma = np.clip(gamma, gamma_grid[0], gamma_grid[-1])

    b_hi = np.searchsorted(log_grid, log_bandwidth, side="right")
    b_hi = np.clip(b_hi, 1, len(log_grid) - 1)
    b_lo = b_hi - 1
    g_hi = np.searchsorted(gamma_grid, gamma, side="right")
    g_hi = np.clip(g_hi, 1, len(gamma_grid) - 1)
    g_lo = g_hi - 1

    b_weight = (log_bandwidth - log_grid[b_lo]) / np.maximum(log_grid[b_hi] - log_grid[b_lo], 1.0e-12)
    g_weight = (gamma - gamma_grid[g_lo]) / np.maximum(gamma_grid[g_hi] - gamma_grid[g_lo], 1.0e-12)

    flat_q = q_grid.reshape((-1, q_grid.shape[-2], q_grid.shape[-1]))
    row = np.arange(flat_q.shape[0])
    b_lo_f = b_lo.reshape(-1)
    b_hi_f = b_hi.reshape(-1)
    g_lo_f = g_lo.reshape(-1)
    g_hi_f = g_hi.reshape(-1)
    q00 = flat_q[row, b_lo_f, g_lo_f]
    q10 = flat_q[row, b_hi_f, g_lo_f]
    q01 = flat_q[row, b_lo_f, g_hi_f]
    q11 = flat_q[row, b_hi_f, g_hi_f]
    wb = b_weight.reshape(-1)
    wg = g_weight.reshape(-1)
    q = (
        (1.0 - wb) * (1.0 - wg) * q00
        + wb * (1.0 - wg) * q10
        + (1.0 - wb) * wg * q01
        + wb * wg * q11
    )
    return np.clip(q.reshape(link_shape), 0.0, 1.0).astype(np.float32)


def finite_retransmission_reliability(
    q_success: np.ndarray,
    max_transmissions: int | np.ndarray,
) -> np.ndarray:
    q = np.clip(np.asarray(q_success, dtype=np.float64), 0.0, 1.0)
    k = np.asarray(max_transmissions, dtype=np.int64)
    if np.any(k < 1):
        raise ValueError("max_transmissions must be >= 1")
    return (1.0 - (1.0 - q) ** k).astype(np.float32)


def expected_transmission_attempts(
    q_success: np.ndarray,
    max_transmissions: int | np.ndarray,
) -> np.ndarray:
    q = np.clip(np.asarray(q_success, dtype=np.float64), 0.0, 1.0)
    k = np.asarray(max_transmissions, dtype=np.int64)
    if np.any(k < 1):
        raise ValueError("max_transmissions must be >= 1")
    numerator = 1.0 - (1.0 - q) ** k
    result = np.where(q > 1.0e-12, numerator / np.maximum(q, 1.0e-12), k)
    return result.astype(np.float32)

