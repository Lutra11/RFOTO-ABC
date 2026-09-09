"""Portable replay of frozen jobs, without modifying archival outputs."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'datas/revision_20260909'
BACKEND = ROOT / 'experiments/revision_20260909'
GROUPS = ('comparison', 'ablation', 'sensitivity', 'generalization', 'all')

def verify_frozen():
    frozen = json.loads((ARCHIVE / 'frozen_inputs.json').read_text(encoding='utf-8'))
    for field in ('source_sha256', 'historical_sha256'):
        for relative, expected in frozen[field].items():
            path = ROOT / relative.replace('\\', '/')
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError(f'Frozen input changed: {relative}')
    for item in json.loads((ARCHIVE / 'instance_manifest.json').read_text()):
        path = ARCHIVE / item['path'].replace('\\', '/')
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f'Instance changed: {path}')

def selected(job, group):
    suite, scene, run, budget, init, method, theta = job
    if group == 'all':
        return True
    if group == 'comparison':
        return suite == 'controlled' and method in ('RFOTO-ABC', 'Plain-ABC', 'DE-RK', 'LSHADE-lite')
    if group == 'ablation':
        return suite == 'controlled' and init == 'greedy' and method not in ('DE-RK', 'LSHADE-lite')
    if group == 'sensitivity':
        return suite == 'frozen_test' and method in ('RFOTO-ABC', 'RFOTO-ABC-T16')
    return suite == 'frozen_test'

def main(default_group=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=GROUPS, default=default_group or 'all')
    parser.add_argument('--rerun', action='store_true', help='Compute afresh in a separate output directory')
    parser.add_argument('--max-jobs', type=int, help='Smoke-test limit; omit for all jobs')
    args = parser.parse_args()
    if args.max_jobs is not None and args.max_jobs < 1:
        parser.error('--max-jobs must be positive')
    verify_frozen()
    import pandas as pd
    sys.path.insert(0, str(BACKEND))
    import run_revision as runner
    jobs = [job for job in runner.jobs() if selected(job, args.group)]
    if args.max_jobs:
        jobs = jobs[:args.max_jobs]
    if args.rerun:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        dest = ROOT / 'outputs' / f'{args.group}_{stamp}'
        dest.mkdir(parents=True, exist_ok=False)
        for suite, scene, run, *_ in jobs:
            relative = Path('instances') / suite / f'{scene}_{run:02d}.npz'
            (dest / relative).parent.mkdir(parents=True, exist_ok=True)
            if not (dest / relative).exists():
                shutil.copy2(ARCHIVE / relative, dest / relative)
        runner.OUT = dest
        rows = []
        for index, job in enumerate(jobs, 1):
            rows.append(runner.run_one(job))
            if index % 20 == 0 or index == len(jobs):
                print(f'Computed {index}/{len(jobs)}', flush=True)
        data = pd.DataFrame(rows)
        data.to_csv(dest / 'replay_raw.csv', index=False)
        metadata = {'group': args.group, 'computed_jobs': len(rows), 'smoke_test': bool(args.max_jobs),
                    'input_source': 'datas/revision_20260909/instances', 'seed_schedule': 'immutable run_revision.py jobs()',
                    'cached_answers_used': False}
        (dest / 'replay_protocol.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    else:
        data = pd.read_csv(ARCHIVE / 'revision_raw.csv')
        keys = set(jobs)
        fields = ['suite', 'scenario', 'run', 'budget', 'initialization', 'algorithm', 'theta']
        data = data.loc[[tuple(row) in keys for row in data[fields].itertuples(index=False, name=None)]]
        dest = ROOT / 'outputs' / f'summary_{args.group}'
        dest.mkdir(parents=True, exist_ok=True)
    summary = data.groupby(['suite', 'scenario', 'budget', 'initialization', 'algorithm'], as_index=False).agg(
        n=('objective', 'size'), objective_mean=('objective', 'mean'), objective_sd=('objective', 'std'))
    summary.to_csv(dest / 'summary.csv', index=False)
    print(summary.to_string(index=False))
    print(f'{len(data)} records; outputs: {dest}')

if __name__ == '__main__':
    main()
