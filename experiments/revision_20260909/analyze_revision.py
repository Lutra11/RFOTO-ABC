"""Prespecified paired analyses and honest best/tie counting for the revision."""
from pathlib import Path
import hashlib
import json
import sys
import warnings
import numpy as np
import pandas as pd
sys.path.append('C:/RFOTO-ABC/pydeps_clean')
from scipy import stats
import scipy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT/'datas/revision_20260909'
ANALYSIS = OUT/'analysis'
ANALYSIS.mkdir(parents=True, exist_ok=True)

def holm(values):
    values = np.asarray(values)
    order = np.argsort(values)
    adjusted = np.minimum(1, np.maximum.accumulate(values[order]*(len(values)-np.arange(len(values)))))
    result = np.empty_like(adjusted)
    result[order] = adjusted
    return result

def paired(ref, comp, metadata):
    ref, comp = np.asarray(ref, float), np.asarray(comp, float)
    assert len(ref) == len(comp) == 20
    delta = comp-ref
    delta[np.abs(delta) <= 1e-12] = 0
    rel = 100*delta/comp
    rng = np.random.default_rng(20260909)
    ids = rng.integers(0, len(ref), (10000, len(ref)))
    ci = np.quantile(rel[ids].mean(axis=1), [0.025, 0.975])
    if np.all(delta == 0):
        p = 1.
    else:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            p = float(stats.wilcoxon(delta, alternative='two-sided', zero_method='wilcox', method='approx').pvalue)
    return {**metadata, 'n': len(ref), 'reference_mean': ref.mean(), 'comparator_mean': comp.mean(),
            'mean_paired_difference': delta.mean(), 'mean_relative_gain_pct': rel.mean(),
            'ci_low_pct': ci[0], 'ci_high_pct': ci[1], 'p_raw': p,
            'wins': int(np.sum(delta > 0)), 'ties': int(np.sum(delta == 0)), 'losses': int(np.sum(delta < 0))}

def correct_best_counts():
    old = pd.read_csv(ROOT/'datas/raw_results/exp423_advanced_algorithm_comparison.csv')
    pivot = old.pivot(index=['scenario', 'run'], columns='algorithm', values='objective')
    best = np.isclose(pivot.to_numpy(), pivot.min(axis=1).to_numpy()[:, None], atol=1e-12, rtol=0)
    tied = best.sum(axis=1) > 1
    ranks = pivot.rank(axis=1, method='average')
    rows = []
    for j, method in enumerate(pivot.columns):
        x = old[old.algorithm == method]
        rows.append({'algorithm': method, 'objective_mean': x.objective.mean(), 'mean_rank': ranks[method].mean(),
                     'unique_best': int(np.sum(best[:, j] & ~tied)), 'tied_best': int(np.sum(best[:, j] & tied)),
                     'not_best': int(np.sum(~best[:, j])), 'runtime_s': x.runtime_s.mean()})
    output = pd.DataFrame(rows).sort_values('mean_rank')
    output.to_csv(ANALYSIS/'advanced_corrected_best_counts.csv', index=False)
    details = [{'scenario': scene, 'run': int(run), 'tied_methods': list(pivot.columns[best[i]]), 'objective': float(pivot.iloc[i].min())} for i, (scene, run) in enumerate(pivot.index) if tied[i]]
    (ANALYSIS/'historical_ties.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
    return output

def main():
    df = pd.read_csv(OUT/'revision_raw.csv')
    assert len(df) == 2040
    group = ['suite', 'scenario', 'run', 'budget', 'initialization']
    assert df.groupby(group).population_sha256.nunique().max() == 1
    shared = df[(df.algorithm != 'Uniform-allocation') & (df.algorithm != 'RFOTO-ABC-T16') & (df.algorithm != 'Offload-then-Allocate')]
    assert shared.groupby(group).initial_objective.agg(lambda x: x.max()-x.min()).max() < 1e-12
    numeric = ['objective', 'violation_rate', 'jain', 'r_hat', 'initial_objective', 'initial_to_final_gain_pct', 'scout_count', 'accepted_neighbors', 'runtime_s']
    summary = df.groupby(['suite', 'scenario', 'budget', 'initialization', 'algorithm', 'theta'])[numeric].agg(['mean', 'std'])
    summary.columns = ['_'.join(x) for x in summary.columns]
    summary.reset_index().to_csv(ANALYSIS/'group_summary.csv', index=False)
    controlled = []
    cdf = df[df.suite == 'controlled']
    for (scene, budget, init), g in cdf.groupby(['scenario', 'budget', 'initialization']):
        p = g.pivot(index='run', columns='algorithm', values='objective').sort_index()
        for method in p.columns:
            if method == 'RFOTO-ABC':
                continue
            controlled.append(paired(p['RFOTO-ABC'], p[method], {'suite': 'controlled', 'contrast': 'matched_search', 'scenario': scene, 'budget': budget, 'initialization': init, 'reference': 'RFOTO-ABC', 'comparator': method}))
    for (scene, budget, method), g in cdf[cdf.algorithm.isin(['RFOTO-ABC', 'Plain-ABC', 'DE-RK', 'LSHADE-lite'])].groupby(['scenario', 'budget', 'algorithm']):
        p = g.pivot(index='run', columns='initialization', values='objective').sort_index()
        controlled.append(paired(p.greedy, p.random, {'suite': 'controlled', 'contrast': 'initialization', 'scenario': scene, 'budget': budget, 'initialization': 'paired greedy versus random', 'reference': method+' greedy', 'comparator': method+' random'}))
    controlled = pd.DataFrame(controlled)
    assert len(controlled) == 84
    controlled['p_holm'] = holm(controlled.p_raw)
    controlled.to_csv(ANALYSIS/'controlled_contrasts.csv', index=False)
    holdout = []
    for scene, g in df[df.suite == 'frozen_test'].groupby('scenario'):
        p = g.pivot(index='run', columns='algorithm', values='objective').sort_index()
        for method in p.columns:
            if method != 'RFOTO-ABC':
                holdout.append(paired(p['RFOTO-ABC'], p[method], {'suite': 'frozen_test', 'contrast': 'frozen_parameters', 'scenario': scene, 'budget': 320, 'initialization': 'greedy', 'reference': 'RFOTO-ABC', 'comparator': method}))
    holdout = pd.DataFrame(holdout)
    assert len(holdout) == 24
    holdout['p_holm'] = holm(holdout.p_raw)
    holdout.to_csv(ANALYSIS/'frozen_test_contrasts.csv', index=False)
    temperature = []
    for scene, g in df[df.suite == 'frozen_test'].groupby('scenario'):
        p = g.pivot(index='run', columns='algorithm', values='objective').sort_index()
        # Same six predeclared paired hypotheses, reverse the orientation only
        # so the denominator is the original 0.8 configuration. No extra tests.
        row = paired(p['RFOTO-ABC-T16'], p['RFOTO-ABC'], {'scenario': scene, 'reference': 'RFOTO-ABC-T16', 'comparator': 'RFOTO-ABC'})
        row['p_holm'] = float(holdout[(holdout.scenario==scene) & (holdout.comparator=='RFOTO-ABC-T16')].p_holm.iloc[0])
        temperature.append(row)
    pd.DataFrame(temperature).to_csv(ANALYSIS/'frozen_temperature_contrasts.csv', index=False)
    corrected = correct_best_counts()
    audit = {'rows': len(df), 'controlled_runs': int((df.suite=='controlled').sum()), 'frozen_test_runs': int((df.suite=='frozen_test').sum()),
             'controlled_contrasts': len(controlled), 'frozen_test_contrasts': len(holdout),
             'initial_population_hash_check': True, 'identical_initial_objective_check': True,
             'all_reliability_feasible': bool(df.feasible.eq(1).all()), 'scipy': scipy.__version__,
             'bootstrap': '10000 paired resamples; percentile 95%; seed 20260909',
             'paired_test': 'two-sided Wilcoxon, zero_method=wilcox, normal approximation; all-zero p=1; Holm by suite',
             'analysis_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'raw_sha256': hashlib.sha256((OUT/'revision_raw.csv').read_bytes()).hexdigest()}
    (ANALYSIS/'analysis_audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print(json.dumps(audit, indent=2))
    print('\nCorrected historical winners\n'+corrected.to_string(index=False))
    print('\nControlled comparisons\n'+controlled[controlled.contrast=='matched_search'].to_string(index=False))
    print('\nFrozen test\n'+holdout.to_string(index=False))

if __name__ == '__main__':
    main()
