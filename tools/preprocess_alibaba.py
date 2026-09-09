#!/usr/bin/env python3
"""Build compact RFOTO-ABC workload profiles from Alibaba Trace v2018."""

from __future__ import annotations

import argparse
import csv
import json
import os
import tarfile
from pathlib import Path

import numpy as np


SEED = 20260820
ROOT = Path(__file__).resolve().parents[1]
DATASETS_ROOT = Path(
    os.environ.get("RFOTO_DATASETS_DIR", ROOT.parent / "datasets")
).expanduser().resolve()


def reservoir_append(reservoir, item, seen, limit, rng):
    if len(reservoir) < limit:
        reservoir.append(item)
    else:
        j = int(rng.integers(0, seen + 1))
        if j < limit:
            reservoir[j] = item


def sample_tasks(path: Path, limit: int, rng: np.random.Generator):
    sampled = []
    valid_seen = 0
    total_rows = 0
    with tarfile.open(path, "r:gz") as archive:
        stream = archive.extractfile("batch_task.csv")
        assert stream is not None
        text = (line.decode("utf-8", "replace") for line in stream)
        for row in csv.reader(text):
            total_rows += 1
            if len(row) != 9:
                continue
            try:
                task_name, instance_num, _, task_type, status, start, end, plan_cpu, plan_mem = row
                instance_num = int(float(instance_num))
                start = int(float(start))
                end = int(float(end))
                plan_cpu = float(plan_cpu)
                plan_mem = float(plan_mem)
                task_type = int(float(task_type))
            except (TypeError, ValueError):
                continue
            duration = end - start
            if status != "Terminated" or duration <= 0 or plan_cpu <= 0 or instance_num <= 0:
                continue
            item = (start, duration, plan_cpu, plan_mem, instance_num, task_type, task_name.startswith("task_"))
            reservoir_append(sampled, item, valid_seen, limit, rng)
            valid_seen += 1
    return sampled, total_rows, valid_seen


def load_machine_meta(path: Path):
    rows = []
    with tarfile.open(path, "r:gz") as archive:
        stream = archive.extractfile("machine_meta.csv")
        assert stream is not None
        text = (line.decode("utf-8", "replace") for line in stream)
        for row in csv.reader(text):
            if len(row) != 7:
                continue
            try:
                machine_id, ts, fd1, fd2, cpu_num, mem_size, status = row
                rows.append((machine_id, int(float(ts)), int(float(cpu_num)), float(mem_size), status))
            except (TypeError, ValueError):
                continue
    return rows


def sample_machine_usage(path: Path, limit: int, max_rows: int, rng: np.random.Generator):
    sampled = []
    valid_seen = 0
    total_rows = 0
    machines = set()
    with tarfile.open(path, "r:gz") as archive:
        stream = archive.extractfile("machine_usage.csv")
        assert stream is not None
        text = (line.decode("utf-8", "replace") for line in stream)
        for row in csv.reader(text):
            total_rows += 1
            if total_rows > max_rows:
                break
            if len(row) != 9:
                continue
            try:
                machine_id = row[0]
                timestamp = float(row[1])
                cpu_util = float(row[2])
                mem_util = float(row[3])
                net_in = float(row[6]) if row[6] else np.nan
                net_out = float(row[7]) if row[7] else np.nan
            except (TypeError, ValueError):
                continue
            if not (0.0 <= cpu_util <= 100.0 and 0.0 <= mem_util <= 100.0):
                continue
            machines.add(machine_id)
            reservoir_append(
                sampled,
                (timestamp, cpu_util, mem_util, net_in, net_out),
                valid_seen,
                limit,
                rng,
            )
            valid_seen += 1
    return sampled, total_rows, valid_seen, len(machines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DATASETS_ROOT
        / "compute_workload"
        / "alibaba_cluster_trace_v2018"
        / "raw",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DATASETS_ROOT / "processed",
    )
    parser.add_argument("--task-sample", type=int, default=100_000)
    parser.add_argument("--usage-sample", type=int, default=100_000)
    parser.add_argument("--max-usage-rows", type=int, default=2_000_000)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    print("Sampling batch_task.csv ...", flush=True)
    tasks, task_total, task_valid = sample_tasks(
        args.raw_dir / "batch_task.tar.gz", args.task_sample, rng
    )
    print("Reading machine_meta.csv ...", flush=True)
    meta = load_machine_meta(args.raw_dir / "machine_meta.tar.gz")
    print("Sampling machine_usage.csv ...", flush=True)
    usage, usage_total, usage_valid, usage_machines = sample_machine_usage(
        args.raw_dir / "machine_usage.tar.gz",
        args.usage_sample,
        args.max_usage_rows,
        rng,
    )

    task_arr = np.asarray(tasks, dtype=object)
    start_time = task_arr[:, 0].astype(np.int64)
    duration_s = task_arr[:, 1].astype(np.float64)
    plan_cpu = task_arr[:, 2].astype(np.float64)
    plan_mem = task_arr[:, 3].astype(np.float64)
    instance_num = task_arr[:, 4].astype(np.int64)
    task_type = task_arr[:, 5].astype(np.int16)
    independent = task_arr[:, 6].astype(bool)
    raw_work = np.maximum((plan_cpu / 100.0) * duration_s, 1.0e-9)
    log_work = np.log1p(raw_work)
    q01, q99 = np.quantile(log_work, [0.01, 0.99])
    normalized = np.clip((log_work - q01) / max(q99 - q01, 1.0e-12), 0.0, 1.0)
    compute_cycles = 0.2e9 + normalized * 4.8e9

    latest_meta = {}
    for machine_id, ts, cpu_num, mem_size, status in meta:
        if machine_id not in latest_meta or ts >= latest_meta[machine_id][0]:
            latest_meta[machine_id] = (ts, cpu_num, mem_size, status)
    cpu_num = np.asarray(
        [value[1] for value in latest_meta.values() if value[1] > 0], dtype=np.float32
    )
    mem_size = np.asarray(
        [value[2] for value in latest_meta.values() if 0 <= value[2] <= 100], dtype=np.float32
    )

    usage_arr = np.asarray(usage, dtype=np.float64)
    output_npz = args.output_dir / "alibaba_workload_profiles.npz"
    np.savez_compressed(
        output_npz,
        start_time_s=start_time,
        duration_s=duration_s.astype(np.float32),
        plan_cpu=plan_cpu.astype(np.float32),
        plan_mem=plan_mem.astype(np.float32),
        instance_num=instance_num.astype(np.int32),
        task_type=task_type,
        independent_task=independent.astype(np.uint8),
        compute_cycles=compute_cycles.astype(np.float32),
        machine_cpu_num=cpu_num,
        machine_mem_size=mem_size,
        usage_timestamp_s=usage_arr[:, 0].astype(np.float64),
        machine_cpu_util_percent=usage_arr[:, 1].astype(np.float32),
        machine_mem_util_percent=usage_arr[:, 2].astype(np.float32),
        machine_net_in=usage_arr[:, 3].astype(np.float32),
        machine_net_out=usage_arr[:, 4].astype(np.float32),
    )
    metadata = {
        "source": "Alibaba Cluster Trace v2018",
        "seed": SEED,
        "task_rows_scanned": task_total,
        "valid_tasks_seen": task_valid,
        "task_reservoir_size": len(tasks),
        "machine_meta_rows": len(meta),
        "unique_machines_meta": len(latest_meta),
        "usage_rows_scanned": usage_total,
        "valid_usage_rows_seen": usage_valid,
        "usage_reservoir_size": len(usage),
        "unique_machines_in_usage_scan": usage_machines,
        "compute_mapping": "log1p(plan_cpu/100*duration), winsorized at sample q01/q99, mapped to [0.2,5] Gcycle",
        "log_work_q01": float(q01),
        "log_work_q99": float(q99),
        "limitations": [
            "Trace provides data-center workload heterogeneity, not MEC radio measurements.",
            "Input size, deadlines, priority and reliability requirements are generated conditionally in the scenario builder.",
            "Machine usage is a bounded reservoir sample from the first configured scan window.",
        ],
    }
    with (args.output_dir / "alibaba_workload_profiles.json").open("w", encoding="utf-8") as stream:
        json.dump(metadata, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"Wrote {output_npz}", flush=True)


if __name__ == "__main__":
    main()
