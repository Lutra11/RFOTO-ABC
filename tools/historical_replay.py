"""Replay selected historical experiments under recorded seeds and budgets."""
from pathlib import Path
import argparse
import sys
from datetime import datetime, timezone
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import historical_suite as suite

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment', choices=['main', 'advanced', 'ablation', 'sensitivity', 'transfer', 'scaling'])
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    suite.RESULTS = ROOT / 'outputs' / f'historical_{args.experiment}_{stamp}'
    suite.RESULTS.mkdir(parents=True, exist_ok=False)
    functions = {'main': suite.experiment_48_49_main, 'ablation': suite.experiment_414_ablation,
                 'sensitivity': suite.experiment_415_sensitivity, 'transfer': suite.experiment_417_ood,
                 'scaling': suite.experiment_413_scaling}
    if args.experiment in functions:
        functions[args.experiment]()
    else:
        from algorithm.registry import run_algorithm
        from algorithm.rfoto_core import build_scenario, metrics_record
        names = ['RFOTO-ABC','Standard-ABC','GA','PSO','DE','Gbest-ABC','MeABC','JADE','LSHADE-lite','CMAES-lite','GWO']
        rows, traces = [], []
        for scene_index, scene in enumerate(['S1','S2','S3','S4','S5','S6']):
            for run in range(8):
                scenario = build_scenario(scene, run, 951000 + scene_index * 1000 + run)
                for alg_index, name in enumerate(names):
                    seed = 1051000 + scene_index * 10000 + run * 100 + alg_index
                    result = run_algorithm(name, scenario, 320, seed)
                    rows.append(metrics_record(result, scene, run, {'budget':320, 'comparison_suite':'advanced'}))
                    for fe, value in zip(result.trace_fe, result.trace_objective):
                        traces.append({'scenario':scene,'run':run,'algorithm':name,'fe':int(fe),'objective':float(value)})
        pd.DataFrame(rows).to_csv(suite.RESULTS / 'exp423_advanced_algorithm_comparison.csv', index=False)
        pd.DataFrame(traces).to_csv(suite.RESULTS / 'advanced_traces.csv', index=False)
    print(suite.RESULTS)
if __name__ == '__main__':
    main()
