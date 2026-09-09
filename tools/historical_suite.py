#!/usr/bin/env python3
"""Run the RFOTO-ABC evidence suite corresponding to Sections 4.7--4.18."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithm.rfoto_core import (
    AlgorithmConfig,
    Candidate,
    build_scenario,
    metrics_record,
    random_candidate,
    run_de,
    run_ga,
    run_pso,
    run_rfoto_abc,
    run_rule,
)


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "process" / "results"
SEED_BASE = 731_000


def save(df: pd.DataFrame, name: str):
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / name
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"saved {path} ({len(df)} rows)", flush=True)
    return df


def run_optimizer(name, s, budget, seed, cfg=None, warm=None):
    if name == "RFOTO-ABC":
        return run_rfoto_abc(s, budget, seed, cfg=cfg, algorithm=name, warm_candidate=warm)
    if name == "Standard-ABC":
        baseline_cfg = cfg or AlgorithmConfig(
            reliability_guidance=False,
            fairness_guidance=False,
            greedy_initialization=False,
            directed_scout=False,
        )
        return run_rfoto_abc(s, budget, seed, cfg=baseline_cfg, algorithm=name)
    if name == "GA": return run_ga(s, budget, seed)
    if name == "PSO": return run_pso(s, budget, seed)
    if name == "DE": return run_de(s, budget, seed)
    return run_rule(s, name, seed)


def experiment_47_small_reference(runs=10):
    rows=[]
    for run in range(runs):
        s=build_scenario("S0",run,SEED_BASE+run,n_users=6,n_servers=2)
        ref_candidates=[run_de(s,3500,9000+run),run_rfoto_abc(s,3500,9100+run)]
        high_budget_reference=min(ref_candidates,key=lambda x:x.solution.objective)
        run_rows=[]
        for alg in ["RFOTO-ABC","Standard-ABC","GA","PSO","DE","Delay-Greedy"]:
            result=run_optimizer(alg,s,600,10_000+run)
            run_rows.append(metrics_record(result,"S0-small",run))
        best_observed=min(
            high_budget_reference.solution.objective,
            min(rec["objective"] for rec in run_rows),
        )
        for rec in run_rows:
            rec["reference_objective"]=best_observed
            rec["reference_type"]="best observed: high-budget DE/RFOTO-ABC plus compared runs"
            rec["reference_gap_percent"]=100*(rec["objective"]-best_observed)/max(abs(best_observed),1e-12)
            rows.append(rec)
    return save(pd.DataFrame(rows),"exp47_small_reference.csv")


def experiment_48_49_main(runs=30,budget=500):
    rows=[]; trace_rows=[]
    algorithms=["RFOTO-ABC","Standard-ABC","GA","PSO","DE","Local-only","Random-feasible","Max-SINR","Delay-Greedy","Load-Aware","Offload-then-Allocate"]
    for scene_idx,scene in enumerate(["S1","S2","S3","S4","S5","S6"]):
        print(f"main {scene}",flush=True)
        scene_budget=budget if scene in {"S1","S2","S3"} else int(budget*0.75)
        for run in range(runs):
            s=build_scenario(scene,run,SEED_BASE+scene_idx*1000+run)
            for alg in algorithms:
                result=run_optimizer(alg,s,scene_budget,20_000+scene_idx*1000+run)
                rows.append(metrics_record(result,scene,run))
                if alg in {"RFOTO-ABC","Standard-ABC","GA","PSO","DE"} and run<10 and scene in {"S2","S4","S6"}:
                    for fe,obj in zip(result.trace_fe,result.trace_objective):
                        trace_rows.append({"scenario":scene,"run":run,"algorithm":alg,"fe":int(fe),"objective":float(obj)})
    save(pd.DataFrame(trace_rows),"exp49_convergence.csv")
    return save(pd.DataFrame(rows),"exp48_main_comparison.csv")


def experiment_410_reliability(runs=15,budget=350):
    rows=[]
    levels=[0.0,0.10,0.20,0.30,0.40]
    for level in levels:
        for run in range(runs):
            s=build_scenario("S4",run,SEED_BASE+3000+run,q_scale=1-level,channel_loss_db=8*level)
            cfg_r=AlgorithmConfig(reliability_guidance=False)
            variants=[("RFOTO-ABC",None),("RFOTO-ABC-R",cfg_r),("Standard-ABC",None),("Max-SINR",None)]
            for name,cfg in variants:
                if name=="RFOTO-ABC-R": result=run_rfoto_abc(s,budget,30_000+run,cfg=cfg,algorithm=name)
                else: result=run_optimizer(name,s,budget,30_000+run)
                rows.append(metrics_record(result,"S4",run,{"additional_blockage_probability":level}))
    return save(pd.DataFrame(rows),"exp410_reliability_stress.csv")


def experiment_411_fairness(runs=15,budget=350):
    rows=[]; base=np.asarray([0.25,0.15,0.20,0.25],float)
    for wf in [0,0.05,0.10,0.20,0.30,0.40]:
        w=np.concatenate([base/base.sum()*(1-wf),[wf]])
        for run in range(runs):
            s=build_scenario("S3",run,SEED_BASE+4000+run,weights=w)
            result=run_rfoto_abc(s,budget,40_000+run)
            rows.append(metrics_record(result,"S3",run,{"w_fairness":wf}))
    return save(pd.DataFrame(rows),"exp411_fairness_tradeoff.csv")


def experiment_412_resource(runs=8,budget=280):
    rows=[]
    for b_scale in [0.5,0.75,1.0,1.25,1.5]:
        for f_scale in [0.5,0.75,1.0,1.25,1.5]:
            for run in range(runs):
                s=build_scenario("S3",run,SEED_BASE+5000+run,bandwidth_scale=b_scale,cpu_scale=f_scale)
                result=run_rfoto_abc(s,budget,50_000+run)
                rows.append(metrics_record(result,"S3",run,{"bandwidth_scale":b_scale,"cpu_scale":f_scale}))
    return save(pd.DataFrame(rows),"exp412_resource_scarcity.csv")


def experiment_413_scaling(runs=10,budget=320):
    rows=[]
    settings=[("S1",20,3),("S2",50,5),("S3",100,5),("S5",150,8),("S6",200,10)]
    for scene,n,m in settings:
        for run in range(runs):
            s=build_scenario(scene,run,SEED_BASE+6000+run,n_users=n,n_servers=m)
            for alg in ["RFOTO-ABC","Standard-ABC","Delay-Greedy"]:
                result=run_optimizer(alg,s,budget,60_000+run)
                rows.append(metrics_record(result,scene,run,{"n_users":n,"n_servers":m,"candidate_limit":4}))
    return save(pd.DataFrame(rows),"exp413_scalability.csv")


def experiment_414_ablation(runs=20,budget=400):
    variants={
        "RFOTO-ABC":AlgorithmConfig(),
        "RFOTO-ABC-R":AlgorithmConfig(reliability_guidance=False),
        "RFOTO-ABC-F":AlgorithmConfig(fairness_guidance=False,fairness_strength=0.0),
        "RFOTO-ABC-D":AlgorithmConfig(constraint_decoder=False),
        "RFOTO-ABC-G":AlgorithmConfig(greedy_initialization=False),
        "RFOTO-ABC-S":AlgorithmConfig(directed_scout=False),
        "RFOTO-ABC-RF":AlgorithmConfig(reliability_guidance=False,fairness_guidance=False,fairness_strength=0.0),
        "RFOTO-ABC-DG":AlgorithmConfig(constraint_decoder=False,greedy_initialization=False),
    }
    rows=[]
    for run in range(runs):
        base_s=build_scenario("S4",run,SEED_BASE+7000+run)
        for name,cfg in variants.items():
            s=base_s.copy()
            if name in {"RFOTO-ABC-F","RFOTO-ABC-RF"}:
                w=s["weights"].copy(); w[:4]=w[:4]/w[:4].sum(); w[4]=0.0; s["weights"]=w
            result=run_rfoto_abc(s,budget,70_000+run,cfg=cfg,algorithm=name)
            rows.append(metrics_record(result,"S4",run))
    return save(pd.DataFrame(rows),"exp414_ablation.csv")


def experiment_415_sensitivity(runs=6,budget=280):
    settings=[]
    for value in [8,14,20,28]: settings.append(("population",value,AlgorithmConfig(population=value),None))
    for value in [15,35,55]: settings.append(("abandonment_limit",value,AlgorithmConfig(abandonment_limit=value),None))
    for value in [0.15,0.35,0.55,0.75]: settings.append(("greedy_ratio",value,AlgorithmConfig(greedy_ratio=value),None))
    for value in [2,4,6,8]: settings.append(("candidate_limit",value,AlgorithmConfig(candidate_limit=value),None))
    for value in [0.4,0.8,1.2,1.6]: settings.append(("resource_temperature",value,AlgorithmConfig(theta_bandwidth=value,theta_cpu=value),None))
    for value in [0.15,0.35,0.55]:
        rw=np.asarray([value,0.30,0.15,0.20]); rw/=rw.sum(); settings.append(("reliability_risk_weight",value,AlgorithmConfig(risk_weights=rw),None))
    for value in [0.0,0.5,1.0,2.0]: settings.append(("fairness_strength",value,AlgorithmConfig(fairness_strength=value),None))
    for value in [0.10,0.20,0.30]:
        w=np.asarray([0.25,0.15,value,0.25,0.15]); w/=w.sum(); settings.append(("objective_reliability_weight",value,AlgorithmConfig(),w))
    rows=[]
    for group,value,cfg,weights in settings:
        for run in range(runs):
            s=build_scenario("S4",run,SEED_BASE+8000+run,weights=weights)
            s["theta_b"]=cfg.theta_bandwidth; s["theta_f"]=cfg.theta_cpu
            result=run_rfoto_abc(s,budget,80_000+run,cfg=cfg)
            rows.append(metrics_record(result,"S4",run,{"parameter":group,"value":value}))
    return save(pd.DataFrame(rows),"exp415_sensitivity.csv")


def map_warm(prev_candidate,prev_ids,current_ids,s,rng):
    warm=random_candidate(s,rng)
    if prev_candidate is None: return warm
    prev_map={int(uid):idx for idx,uid in enumerate(prev_ids)}
    for idx,uid in enumerate(current_ids):
        if int(uid) in prev_map:
            old=prev_map[int(uid)]; warm.assignment[idx]=min(prev_candidate.assignment[old],s["m"]); warm.bandwidth_key[idx]=prev_candidate.bandwidth_key[old]; warm.cpu_key[idx]=prev_candidate.cpu_key[old]
    return warm


def experiment_416_dynamic(budget=110):
    rows=[]; rng=np.random.default_rng(SEED_BASE+9000)
    for episode in range(3):
        state=0; prev_ids=np.asarray([],int); prev_warm=None; prev_assign={}
        for slot in range(50):
            state = int(rng.random() < (0.12 if state==0 else 0.82))
            active_n=int(rng.integers(45,75) if state==0 else rng.integers(115,155))
            ids=np.sort(rng.choice(200,active_n,replace=False))
            s=build_scenario("S6",slot,SEED_BASE+episode*1000+slot,dynamic=(episode,slot),task_user_ids=ids,load_scale=0.85 if state==0 else 1.20)
            warm=map_warm(prev_warm,prev_ids,ids,s,rng)
            variants=[]
            cold=run_rfoto_abc(s,budget,90_000+episode*100+slot,algorithm="Cold-RFOTO")
            warm_result=run_rfoto_abc(s,budget,90_000+episode*100+slot,warm_candidate=warm,algorithm="Warm-RFOTO")
            rolling=run_rfoto_abc(s,budget,91_000+episode*100+slot,algorithm="Standard-ABC")
            variants.extend([cold,warm_result,rolling,run_rule(s,"Delay-Greedy"),run_rule(s,"Max-SINR")])
            for result in variants:
                changes=0
                if result.algorithm=="Warm-RFOTO":
                    current={int(uid):int(a) for uid,a in zip(ids,result.solution.assignment)}
                    changes=sum(current[uid]!=prev_assign[uid] for uid in current.keys()&prev_assign.keys())
                rec=metrics_record(result,"S6-dynamic",slot,{"episode":episode,"slot":slot,"load_state":"high" if state else "low","active_users":active_n,"assignment_changes":changes})
                rows.append(rec)
            prev_warm=warm_result.best_candidate.copy(); prev_ids=ids.copy(); prev_assign={int(uid):int(a) for uid,a in zip(ids,warm_result.solution.assignment)}
    return save(pd.DataFrame(rows),"exp416_dynamic.csv")


def experiment_417_ood(runs=15,budget=350):
    cases=[
        ("in_distribution",dict(scenario="S2")),
        ("bursty_heavy_load",dict(scenario="S3",load_scale=1.35)),
        ("strong_server_heterogeneity",dict(scenario="S5",cpu_scale=0.70,bandwidth_scale=1.20)),
        ("channel_estimation_shift",dict(scenario="S4",q_scale=0.80,channel_loss_db=2.0)),
    ]
    rows=[]
    for case,kwargs in cases:
        scene=kwargs.pop("scenario")
        for run in range(runs):
            s=build_scenario(scene,run,SEED_BASE+10_000+run,**kwargs)
            for alg in ["RFOTO-ABC","Standard-ABC","Delay-Greedy"]:
                result=run_optimizer(alg,s,budget,100_000+run)
                rows.append(metrics_record(result,scene,run,{"ood_case":case}))
    return save(pd.DataFrame(rows),"exp417_ood.csv")


def vargha_delaney_smaller(x,y):
    x=np.asarray(x); y=np.asarray(y); u=stats.mannwhitneyu(x,y,alternative="two-sided").statistic
    return float(1-u/(len(x)*len(y)))


def bootstrap_a12_ci(x,y,seed=2026,reps=2000):
    rng=np.random.default_rng(seed); x=np.asarray(x); y=np.asarray(y); values=[]
    for _ in range(reps):
        ix=rng.integers(0,len(x),len(x)); iy=rng.integers(0,len(y),len(y)); values.append(vargha_delaney_smaller(x[ix],y[iy]))
    return np.quantile(values,[0.025,0.975])


def experiment_418_statistics(main_df):
    algs=["RFOTO-ABC","Standard-ABC","GA","PSO","DE","Delay-Greedy"]
    pivot=main_df[main_df.algorithm.isin(algs)].pivot_table(index=["scenario","run"],columns="algorithm",values="objective",aggfunc="mean").dropna()
    friedman=stats.friedmanchisquare(*[pivot[a].to_numpy() for a in algs])
    comparisons=[]
    for alg in algs[1:]:
        x=pivot["RFOTO-ABC"].to_numpy(); y=pivot[alg].to_numpy(); w=stats.wilcoxon(x,y,alternative="two-sided",zero_method="pratt")
        ci=bootstrap_a12_ci(x,y,seed=SEED_BASE+len(comparisons))
        comparisons.append({"comparison":f"RFOTO-ABC vs {alg}","p_raw":float(w.pvalue),"a12_rfoto_smaller":vargha_delaney_smaller(x,y),"a12_ci_low":float(ci[0]),"a12_ci_high":float(ci[1])})
    order=np.argsort([r["p_raw"] for r in comparisons]); running=0.0; m=len(comparisons)
    for rank,idx in enumerate(order):
        adj=min(1.0,(m-rank)*comparisons[idx]["p_raw"]); running=max(running,adj); comparisons[idx]["p_holm"]=running; comparisons[idx]["reject_0_05"]=int(running<0.05)
    rank_df=pivot.rank(axis=1,method="average").mean().sort_values().reset_index(); rank_df.columns=["algorithm","mean_rank"]
    out={"friedman_statistic":float(friedman.statistic),"friedman_p":float(friedman.pvalue),"blocks":len(pivot),"algorithms":algs,"average_ranks":rank_df.to_dict("records"),"pairwise":comparisons,"a12_direction":"values above 0.5 favor smaller RFOTO-ABC objective"}
    path=RESULTS/"exp418_statistics.json"; path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8"); print(f"saved {path}",flush=True)
    save(pd.DataFrame(comparisons),"exp418_pairwise.csv"); save(rank_df,"exp418_ranks.csv")
    return out


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--skip-dynamic",action="store_true"); args=parser.parse_args()
    RESULTS.mkdir(parents=True,exist_ok=True)
    started=time.time()
    metadata={"started":time.strftime("%Y-%m-%d %H:%M:%S"),"python":sys.version,"platform":platform.platform(),"numpy":np.__version__,"pandas":pd.__version__}
    (RESULTS/"run_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    experiment_47_small_reference()
    main_df=experiment_48_49_main()
    experiment_410_reliability(); experiment_411_fairness(); experiment_412_resource(); experiment_413_scaling(); experiment_414_ablation(); experiment_415_sensitivity()
    if not args.skip_dynamic: experiment_416_dynamic()
    experiment_417_ood(); experiment_418_statistics(main_df)
    metadata["elapsed_s"]=time.time()-started; metadata["completed"]=time.strftime("%Y-%m-%d %H:%M:%S")
    (RESULTS/"run_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    print(f"all experiments complete in {metadata['elapsed_s']:.1f}s",flush=True)


if __name__=="__main__": main()
