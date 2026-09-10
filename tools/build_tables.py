"""Export manuscript Tables 5--15 from recorded data without rerunning experiments."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'datas/raw_results'
REV = ROOT / 'datas/revision_20260909'
DEST = ROOT / 'datas/tables'

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for path in DEST.glob('Table*.csv'):
        path.unlink()
    new = pd.read_csv(REV / 'revision_raw.csv')
    control = new[new.suite == 'controlled']
    test = new[new.suite == 'frozen_test']
    tables = []
    def add(number, name, title, data, sources, note):
        file = f'Table{number:02d}_{name}.csv'
        data.to_csv(
            DEST / file,
            index=False,
            float_format='%.15g',
            lineterminator='\n',
        )
        tables.append({'table':number, 'title':title, 'file':f'datas/tables/{file}',
            'upstream':sources, 'note':note})
    old = pd.read_csv(RAW / 'exp48_main_comparison.csv')
    names = ['RFOTO-ABC','Offload-then-Allocate','Load-Aware','Delay-Greedy','GA','Standard-ABC','PSO','DE','Max-SINR','Random-feasible','Local-only']
    data = old.pivot_table(index='algorithm',columns='scenario',values='objective',aggfunc='mean').reindex(names).reset_index()
    add(5,'Main','Mean composite objective in the main scenarios',data,['datas/raw_results/exp48_main_comparison.csv'],
        'n=30 per scene/method. Search FE: 500 S1-S3, 375 S4-S6. Rules: 1 FE. Lower is better.')
    add(6,'Advanced','Extended search comparison and exclusive/tied best counts',pd.read_csv(REV/'analysis/advanced_corrected_best_counts.csv'),
        ['datas/raw_results/exp423_advanced_algorithm_comparison.csv','datas/revision_20260909/analysis/advanced_corrected_best_counts.csv'],
        '48 paired instances, 320 FE. Unique/tied/non-best are separate; tolerance 1e-12.')
    data = control[control.algorithm.isin(['RFOTO-ABC','Plain-ABC','DE-RK','LSHADE-lite'])].pivot_table(
        index=['scenario','budget','initialization'],columns='algorithm',values='objective',aggfunc='mean').reset_index()
    add(7,'Matched','Search methods and budgets with identical initial populations',data,['datas/revision_20260909/revision_raw.csv'],
        'n=20 paired instances per stratum. Same initial population and same decoder; 14 initial evaluations included.')
    old = pd.read_csv(RAW/'exp414_ablation.csv')
    old['common_objective'] = old[['t_hat','e_hat','r_hat','v_hat','fairness_loss']].to_numpy() @ np.array([.25,.15,.20,.25,.15])
    data = old.groupby('algorithm',as_index=False).agg(n=('objective','size'),objective_mean=('common_objective','mean'),objective_sd=('common_objective','std'),deadline_rate=('violation_rate','mean'),jain_mean=('jain','mean'))
    add(8,'Ablation','Ablation variants reevaluated with common objective weights',data,['datas/raw_results/exp414_ablation.csv'],
        'S4; n=20; 400 FE. -F/-RF also changed the search objective. Common rescoring does not remove that confound.')
    group = control[(control.initialization=='greedy') & ~control.algorithm.isin(['DE-RK','LSHADE-lite'])]
    data = group.pivot_table(index='algorithm',columns=['budget','scenario'],values='objective',aggfunc='mean')
    data.columns=[f'{s}_{b}FE' for b,s in data.columns]
    add(9,'Controlled_Ablation','Component interventions with the same objective and initial encoding',data.reset_index(),['datas/revision_20260909/revision_raw.csv'],
        'n=20 per stratum. Uniform allocation changes decoded initial resources, not raw initial encodings.')
    old = pd.read_csv(RAW/'exp415_sensitivity.csv')
    old = old[old.parameter!='objective_reliability_weight']
    data = old.groupby(['parameter','value'],as_index=False).agg(n=('objective','size'),objective_mean=('objective','mean'),objective_sd=('objective','std'))
    add(10,'Sensitivity','Parameter sensitivity under a fixed objective',data,['datas/raw_results/exp415_sensitivity.csv'],
        'S4; n=6; 280 FE. The objective-weight sweep changes the metric scale and remains supplementary.')
    data = pd.read_csv(REV/'analysis/frozen_temperature_contrasts.csv')
    data = data[['scenario','reference_mean','comparator_mean','mean_relative_gain_pct','ci_low_pct','ci_high_pct','p_holm','wins','ties','losses']].rename(columns={'reference_mean':'theta_1_6_mean','comparator_mean':'theta_0_8_mean'})
    data = data[['scenario','theta_0_8_mean','theta_1_6_mean','mean_relative_gain_pct','ci_low_pct','ci_high_pct','p_holm','wins','ties','losses']]
    for name,label in [('RFOTO-ABC','deadline_rate_0_8'),('RFOTO-ABC-T16','deadline_rate_1_6')]:
        data[label]=data.scenario.map(test[test.algorithm==name].groupby('scenario').violation_rate.mean())
    add(11,'Temperature','New-instance tests of prespecified resource-allocation temperatures',data,['datas/revision_20260909/analysis/frozen_temperature_contrasts.csv','datas/revision_20260909/revision_raw.csv'],
        'n=20 per scene; 320 FE. Gain denominator is each 0.8 result. Pointwise paired 95% CI; Holm p in 24-test family.')
    old = pd.read_csv(RAW/'exp417_ood.csv')
    data = old.groupby(['ood_case','algorithm'],as_index=False).agg(n=('objective','size'),objective_mean=('objective','mean'),objective_sd=('objective','std'),deadline_rate=('violation_rate','mean'),jain_mean=('jain','mean'))
    data['ood_case']=data.ood_case.replace({'in_distribution':'S2 baseline','bursty_heavy_load':'S3 heavy load','strong_server_heterogeneity':'S5 CPU reduction and bandwidth increase','channel_estimation_shift':'S4 observed link degradation'})
    add(12,'Transfer','Scenario-wise reoptimization with a fixed algorithm configuration',data,['datas/raw_results/exp417_ood.csv'],
        'n=15; 350 FE searches, 1 FE rule. Optimization and evaluation both observe the changed state.')
    data = test.groupby(['scenario','algorithm','theta'],as_index=False).agg(n=('objective','size'),objective_mean=('objective','mean'),objective_sd=('objective','std'))
    add(13,'New_Instances','Composite objective on six new-instance groups with prespecified configurations',data,['datas/revision_20260909/revision_raw.csv'],
        'n=20; 320 FE searches, 1 FE rule. Only RFOTO-ABC was evaluated at theta 1.6; not a decoder-controlled cross-temperature ranking.')
    old = pd.read_csv(RAW/'exp413_scalability.csv')
    data = old[old.algorithm=='RFOTO-ABC'].groupby(['n_users','n_servers'],as_index=False).agg(n=('objective','size'),objective_mean=('objective','mean'),objective_sd=('objective','std'),runtime_mean_s=('runtime_s','mean'),runtime_sd_s=('runtime_s','std'))
    add(14,'Scalability','RFOTO-ABC problem scale and runtime',data,['datas/raw_results/exp413_scalability.csv'],
        'n=10; 320 FE. Scenario also changes with scale, so this is not an isolated complexity-order estimate.')
    old = pd.read_csv(RAW/'exp416_dynamic.csv')
    episodes = old.groupby(['algorithm','episode'],as_index=False).agg(
        objective=('objective','mean'), runtime_s=('runtime_s','mean'),
        deadline_rate=('violation_rate','mean'))
    data = episodes.groupby('algorithm',as_index=False).agg(
        n_episodes=('episode','nunique'), objective_mean=('objective','mean'),
        objective_sd=('objective','std'), runtime_mean_s=('runtime_s','mean'),
        runtime_sd_s=('runtime_s','std'), deadline_rate_mean=('deadline_rate','mean'),
        deadline_rate_sd=('deadline_rate','std'))
    data['algorithm'] = data.algorithm.replace({
        'Standard-ABC':'Cold-RFOTO (alternative seed)', 'Max-SINR':'Max-gain'})
    order = ['Cold-RFOTO','Warm-RFOTO','Cold-RFOTO (alternative seed)','Delay-Greedy','Max-gain']
    data = data.set_index('algorithm').reindex(order).reset_index()
    add(15,'Dynamic','Independent-episode summaries of rolling optimization',data,
        ['datas/raw_results/exp416_dynamic.csv'],
        'Three independent 50-slot episodes; episode means are the independent units. Searches use 110 FE per slot; rules use 1 FE.')
    (DEST/'table_index.json').write_text(
        json.dumps(tables,indent=2), encoding='utf-8', newline='\n')
    print(f'Exported {len(tables)} manuscript data tables to {DEST}')

if __name__=='__main__':
    main()
