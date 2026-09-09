"""Generate fresh instances, validate adapters, run the frozen revision protocol."""
from __future__ import annotations
import os
for _env in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_env] = "1"
import argparse
import concurrent.futures
import csv
import hashlib
import importlib.util
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from algorithm import rfoto_core as core
import revision_algorithms as alg

OUT = ROOT / "datas" / "revision_20260909"
OLD = ROOT / "datas" / "raw_results"
DOC = ROOT.parent / "docs" / "RFOTO-ABC_Telecommunication_Systems_完整论文_中文版.docx"
GEN = core.DATASETS_ROOT / "wireless_channel" / "tools" / "generate_wireless_dataset.py"

def source_label(path):
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(Path("datasets") / path.relative_to(core.DATASETS_ROOT))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def array_hash(arr):
    a = np.ascontiguousarray(arr)
    return hashlib.sha256(str(a.shape).encode() + a.dtype.str.encode() + a.tobytes()).hexdigest()

def population_hash(pop):
    h = hashlib.sha256()
    for c in pop:
        for a in (c.assignment, c.bandwidth_key, c.cpu_key):
            h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()

def load_scene(path):
    with np.load(path, allow_pickle=False) as f:
        return {k: f[k].item() if f[k].shape == () else f[k] for k in f.files}

def generator():
    spec = importlib.util.spec_from_file_location("revision_wireless_generator", GEN)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    frozen = OUT / "frozen_inputs.json"
    sources = [HERE/"PROTOCOL.md", HERE/"run_revision.py", HERE/"revision_algorithms.py", ROOT/"algorithm"/"rfoto_core.py", ROOT/"algorithm"/"advanced_metaheuristics.py", GEN, core.WORKLOAD_PROFILE]
    historic = {str(p.relative_to(ROOT)): sha(p) for p in sorted(OLD.glob("*.csv"))}
    payload = {"frozen_at_utc": datetime.now(timezone.utc).isoformat(), "source_sha256": {source_label(p): sha(p) for p in sources}, "historical_sha256": historic, "original_docx_sha256": sha(DOC), "python": sys.version, "numpy": np.__version__, "platform": platform.platform(), "protocol_publicly_registered": False}
    if frozen.exists():
        previous = json.loads(frozen.read_text(encoding="utf-8"))
        assert previous["source_sha256"] == payload["source_sha256"], "Frozen source files changed"
        assert previous["historical_sha256"] == historic
    else:
        frozen.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    gen = generator()
    manifest = []
    seen = set()
    for suite, sid, scenes in (("controlled", 1, ("S2", "S4", "S6")), ("frozen_test", 2, ("S1", "S2", "S3", "S4", "S5", "S6"))):
        for scene in scenes:
            spec = next(x for x in gen.SCENARIOS if x.name == scene)
            old_gain = core._load_wireless(scene)["instantaneous_channel_gain"].astype(np.float64)
            old_hashes = {array_hash(x) for x in old_gain}
            for run in range(20):
                seed = 909000000 + sid*1000000 + int(scene[1:])*10000 + run
                task_seed = seed + 100000000
                path = OUT / "instances" / suite / f"{scene}_{run:02d}.npz"
                if not path.exists():
                    rng = np.random.default_rng(seed)
                    users = gen.make_user_positions(spec, rng)
                    servers = gen.make_server_positions(spec, rng)
                    power = rng.uniform(0.1, 0.5, spec.users).astype(np.float32)
                    links, _ = gen.generate_link_state(spec, users, servers, power, rng, 256)
                    channel = {
                        "q_grid": links["q_success_grid"].astype(np.float64),
                        "channel_gain": links["instantaneous_channel_gain"].astype(np.float64),
                        "interference_w": links["interference_w"].astype(np.float64),
                        "distance_m": links["distance_2d_m"].astype(np.float64),
                        "blocked": links["blocked"], "effective_los": links["effective_los"],
                        "tx_power_w": power.astype(np.float64),
                        "bandwidth_grid_hz": gen.BANDWIDTH_GRID_HZ.copy(),
                        "gamma_grid_db": gen.GAMMA_GRID_DB.copy(),
                    }
                    old_extract = core._extract_channel
                    core._extract_channel = lambda *args, **kwargs: {k: v.copy() for k, v in channel.items()}
                    try:
                        s = core.build_scenario(scene, run, task_seed)
                    finally:
                        core._extract_channel = old_extract
                    s.update({"wireless_seed": seed, "task_seed": task_seed, "user_xy_m": users, "server_xy_m": servers})
                    path.parent.mkdir(parents=True, exist_ok=True)
                    np.savez_compressed(path, **s)
                s = load_scene(path)
                gain_hash = array_hash(s["channel_gain"])
                assert gain_hash not in old_hashes and gain_hash not in seen
                seen.add(gain_hash)
                manifest.append({"suite": suite, "scenario": scene, "run": run, "wireless_seed": seed, "task_seed": task_seed, "path": str(path.relative_to(OUT)), "sha256": sha(path), "gain_sha256": gain_hash})
    (OUT/"instance_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Prepared {len(manifest)} unique fresh instances; protocol and input hashes frozen", flush=True)

def validate():
    reports = []
    for scene, run in (("S2", 0), ("S4", 1), ("S6", 2)):
        s = load_scene(OUT/"instances"/"controlled"/f"{scene}_{run:02d}.npz")
        for seed in (1201, 1202):
            pop, rng = alg.initial_population(s, seed, return_rng=True)
            result = alg.run_abc(s, 1000, seed, pop, rng_state=rng.bit_generator.state)
            original = core.run_rfoto_abc(s, 1000, seed)
            assert result.solution.objective == original.solution.objective
            assert np.array_equal(result.best_candidate.assignment, original.best_candidate.assignment)
            assert np.array_equal(result.best_candidate.bandwidth_key, original.best_candidate.bandwidth_key)
            assert np.array_equal(result.trace_fe[:len(original.trace_fe)], original.trace_fe)
            assert np.array_equal(result.trace_objective[:len(original.trace_objective)], original.trace_objective)
            reports.append({"scenario": scene, "seed": seed, "original_exact_replay": True, "scouts": result.scout_count})
        for mode in ("greedy", "random"):
            pop = alg.initial_population(s, 7654321, mode)
            for c in pop:
                z = alg.centered_encode(c, s["m"])
                recovered = core.decode_vector(z, s)
                assert np.array_equal(c.assignment, recovered.assignment)
                np.testing.assert_allclose(c.bandwidth_key, recovered.bandwidth_key, rtol=0, atol=1e-14)
                assert abs(core.decode_candidate(s, c).objective - core.decode_candidate(s, recovered).objective) < 1e-12
    (OUT/"preflight_validation.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print("Preflight passed: six exact original-algorithm replays and shared encoding checks", flush=True)

def jobs():
    out = []
    for scene in ("S2", "S4", "S6"):
        for run in range(20):
            for budget in (320, 1000):
                for init, methods in (("greedy", ("RFOTO-ABC", "Plain-ABC", "No-risk-sampling", "No-fair-selection", "Random-scout", "Uniform-allocation", "DE-RK", "LSHADE-lite")), ("random", ("RFOTO-ABC", "Plain-ABC", "DE-RK", "LSHADE-lite"))):
                    for method in methods:
                        out.append(("controlled", scene, run, budget, init, method, 0.8))
    for scene in ("S1", "S2", "S3", "S4", "S5", "S6"):
        for run in range(20):
            for method, theta in (("RFOTO-ABC", 0.8), ("RFOTO-ABC-T16", 1.6), ("Plain-ABC", 0.8), ("LSHADE-lite", 0.8), ("Offload-then-Allocate", 0.8)):
                out.append(("frozen_test", scene, run, 320, "greedy", method, theta))
    return out

def run_one(job):
    suite, scene, run, budget, init, method, theta = job
    key = f"{suite}_{scene}_{run:02d}_{budget}_{init}_{method}"
    record_path = OUT/"run_records"/f"{key}.json"
    if record_path.exists():
        return json.loads(record_path.read_text(encoding="utf-8"))["metrics"]
    s = load_scene(OUT/"instances"/suite/f"{scene}_{run:02d}.npz")
    s["theta_b"] = s["theta_f"] = theta
    seed = int(s["wireless_seed"])
    pop = alg.initial_population(s, seed+200000000, init)
    phash = population_hash(pop)
    initial_values = [core.decode_candidate(s, c, "uniform" if method == "Uniform-allocation" else "softmax").objective for c in pop]
    # All algorithms receive the same numeric seed, with separate deterministic
    # streams for population creation and search.
    result = alg.run_method(s, budget, seed+300000000, pop, method)
    sol = result.solution
    assert result.evaluations == (1 if method == "Offload-then-Allocate" else budget)
    assert np.isfinite(sol.objective) and np.all(np.isfinite(sol.components))
    assert abs(sol.objective - np.dot(core.DEFAULT_WEIGHTS, sol.components)) < 1e-12
    assert np.all(sol.reliability + 1e-12 >= s["rho_min"])
    for j in range(s["m"]):
        mask = sol.assignment == j+1
        assert sol.bandwidth_hz[mask].sum() <= s["B"][j] + 1e-6
        assert sol.cpu_hz[mask].sum() <= s["F"][j] + 1e-3
    assert np.all(np.diff(result.trace_objective) <= 1e-12)
    if method != "Offload-then-Allocate":
        assert abs(result.trace_objective[0] - min(initial_values)) < 1e-12
        assert sol.objective <= min(initial_values) + 1e-12
    extra = {"suite": suite, "budget": budget, "initialization": init, "theta": theta,
             "wireless_seed": seed, "task_seed": int(s["task_seed"]), "init_seed": seed+200000000,
             "optimizer_seed": seed+300000000, "population_sha256": phash,
             "initial_objective": min(initial_values), "initial_to_final_gain_pct": 100*(min(initial_values)-sol.objective)/min(initial_values),
             "scout_count": getattr(result, "scout_count", -1), "accepted_neighbors": getattr(result, "accepted_neighbors", -1)}
    rec = core.metrics_record(result, scene, run, extra)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps({"metrics": rec, "initial_objectives": initial_values, "trace_fe": result.trace_fe.tolist(), "trace_objective": result.trace_objective.tolist()}, indent=2), encoding="utf-8")
    return rec

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    prepare()
    validate()
    if args.prepare_only:
        return
    todo = jobs()
    started = time.perf_counter()
    completed = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_one, job) for job in todo]
        for f in concurrent.futures.as_completed(futures):
            completed.append(f.result())
            if len(completed) % 40 == 0:
                print(f"Completed {len(completed)}/{len(todo)} runs in {time.perf_counter()-started:.1f} s", flush=True)
    completed.sort(key=lambda x: (x["suite"], x["scenario"], x["run"], x["budget"], x["initialization"], x["algorithm"]))
    with (OUT/"revision_raw.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(completed[0]))
        writer.writeheader()
        writer.writerows(completed)
    freeze = json.loads((OUT/"frozen_inputs.json").read_text(encoding="utf-8"))
    assert all(sha(ROOT/p) == h for p, h in freeze["historical_sha256"].items())
    assert sha(DOC) == freeze["original_docx_sha256"]
    print(f"DONE: {len(completed)} rows; all budgets, feasibility, and preservation checks passed", flush=True)

if __name__ == "__main__":
    main()
