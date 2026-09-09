"""Export the latest manuscript's numeric experimental tables from recorded data.

No optimizer is executed and no source observation is changed. Complex statistical
results come from the prespecified analysis CSVs. Excel uses the exported payload.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'datas/raw_results'
REV = ROOT / 'datas/revision_20260909'
DEST = ROOT / 'datas/tables'

def matrix(frame):
    return json.loads(frame.to_json(orient='values', double_precision=15))

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    new = pd.read_csv(REV / 'revision_raw.csv')
    control = new[new.suite == 'controlled']
    test = new[new.suite == 'frozen_test']
    tables = []
    def add(number, name, title, data, sources, note):
        file = f'Table{number:02d}_{name}.csv'
        data.to_csv(DEST / file, index=False, float_format='%.15g')
        tables.append({'sheet':f'T{number:02d}_{name}'[:31], 'title':title,
            'source': f'Source: datas/tables/{file}', 'upstream':sources, 'note':note,
            'headers': list(data.columns), 'rows':matrix(data), 'csv':f'datas/tables/{file}'})
    old = pd.read_csv(RAW / 'exp48_main_comparison.csv')
    names = ['RFOTO-ABC','Offload-then-Allocate','Load-Aware','Delay-Greedy','GA','Standard-ABC','PSO','DE','Max-SINR','Random-feasible','Local-only']
    data = old.pivot_table(index='algorithm',columns='scenario',values='objective',aggfunc='mean').reindex(names).reset_index()
    add(7,'Main','Main comparison: mean objective',data,['datas/raw_results/exp48_main_comparison.csv'],
        'n=30 per scene/method. Search FE: 500 S1-S3, 375 S4-S6. Rules: 1 FE. Lower is better.')
    add(8,'Advanced','Advanced comparison: corrected best counts',pd.read_csv(REV/'analysis/advanced_corrected_best_counts.csv'),
        ['datas/raw_results/exp423_advanced_algorithm_comparison.csv','datas/revision_20260909/analysis/advanced_corrected_best_counts.csv'],
        '48 paired instances, 320 FE. Unique/tied/non-best are separate; tolerance 1e-12.')
    data = control[control.algorithm.isin(['RFOTO-ABC','Plain-ABC','DE-RK','LSHADE-lite'])].pivot_table(
        index=['scenario','budget','initialization'],columns='algorithm',values='objective',aggfunc='mean').reset_index()
    add(9,'Matched','Matched initialization: mean objective',data,['datas/revision_20260909/revision_raw.csv'],
        'n=20 paired instances per stratum. Same initial population and same decoder; 14 initial evaluations included.')
    old = pd.read_csv(RAW/'exp414_ablation.csv')
    old['common_objective'] = old[['t_hat','e_hat','r_hat','v_hat','fairness_loss']].to_numpy() @ np.array([.25,.15,.20,.25,.15])
    data = old.groupby('algorithm',as_index=False).agg(n=('objective','size'),objective_mean=('common_objective','mean'),objective_sd=('common_objective','std'),deadline_rate=('violation_rate','mean'),jain_mean=('jain','mean'))
    add(10,'Ablation','Historical ablation: common-weight evaluation',data,['datas/raw_results/exp414_ablation.csv'],
        'S4; n=20; 400 FE. -F/-RF also changed the search objective. Common rescoring does not remove that confound.')
    group = control[(control.initialization=='greedy') & ~control.algorithm.isin(['DE-RK','LSHADE-lite'])]
    data = group.pivot_table(index='algorithm',columns=['budget','scenario'],values='objective',aggfunc='mean')
    data.columns=[f'{s}_{b}FE' for b,s in data.columns]
    add(11,'Controlled_Ablation','Fixed-objective component interventions',data.reset_index(),['datas/revision_20260909/revision_raw.csv'],
        'n=20 per stratum. Uniform allocation changes decoded initial resources, not raw initial encodings.')
    old = pd.read_csv(RAW/'exp415_sensitivity.csv')
    old = old[old.parameter!='objective_reliability_weight']
    data = old.groupby(['parameter','value'],as_index=False).agg(n=('objective','size'),objective_mean=('objective','mean'),objective_sd=('objective','std'))
    add(12,'Sensitivity','Fixed-objective parameter sensitivity',data,['datas/raw_results/exp415_sensitivity.csv'],
        'S4; n=6; 280 FE. The objective-weight sweep changes the metric scale and remains supplementary.')
    data = pd.read_csv(REV/'analysis/frozen_temperature_contrasts.csv')
    data = data[['scenario','reference_mean','comparator_mean','mean_relative_gain_pct','ci_low_pct','ci_high_pct','p_holm','wins','ties','losses']].rename(columns={'reference_mean':'theta_1_6_mean','comparator_mean':'theta_0_8_mean'})
    data = data[['scenario','theta_0_8_mean','theta_1_6_mean','mean_relative_gain_pct','ci_low_pct','ci_high_pct','p_holm','wins','ties','losses']]
    for name,label in [('RFOTO-ABC','deadline_rate_0_8'),('RFOTO-ABC-T16','deadline_rate_1_6')]:
        data[label]=data.scenario.map(test[test.algorithm==name].groupby('scenario').violation_rate.mean())
    add(13,'Temperature','Frozen resource temperature comparison',data,['datas/revision_20260909/analysis/frozen_temperature_contrasts.csv','datas/revision_20260909/revision_raw.csv'],
        'n=20 per scene; 320 FE. Gain denominator is each 0.8 result. Pointwise paired 95% CI; Holm p in 24-test family.')
    old = pd.read_csv(RAW/'exp417_ood.csv')
    data = old.groupby(['ood_case','algorithm'],as_index=False).agg(n=('objective','size'),objective_mean=('objective','mean'),objective_sd=('objective','std'),deadline_rate=('violation_rate','mean'),jain_mean=('jain','mean'))
    data['ood_case']=data.ood_case.replace({'in_distribution':'S2 baseline','bursty_heavy_load':'S3 heavy load','strong_server_heterogeneity':'S5 CPU reduction and bandwidth increase','channel_estimation_shift':'S4 observed link degradation'})
    add(14,'Transfer','Observed-state cross-scenario reoptimization',data,['datas/raw_results/exp417_ood.csv'],
        'n=15; 350 FE searches, 1 FE rule. Optimization and evaluation both observe the changed state.')
    data = test.groupby(['scenario','algorithm','theta'],as_index=False).agg(n=('objective','size'),objective_mean=('objective','mean'),objective_sd=('objective','std'))
    add(15,'Frozen_Test','Six fresh scenario groups: frozen configurations',data,['datas/revision_20260909/revision_raw.csv'],
        'n=20; 320 FE searches, 1 FE rule. Only RFOTO-ABC was evaluated at theta 1.6; not a decoder-controlled cross-temperature ranking.')
    old = pd.read_csv(RAW/'exp413_scalability.csv')
    data = old[old.algorithm=='RFOTO-ABC'].groupby(['n_users','n_servers'],as_index=False).agg(n=('objective','size'),objective_mean=('objective','mean'),objective_sd=('objective','std'),runtime_mean_s=('runtime_s','mean'),runtime_sd_s=('runtime_s','std'))
    add(16,'Scaling','RFOTO-ABC scale and runtime',data,['datas/raw_results/exp413_scalability.csv'],
        'n=10; 320 FE. Scenario also changes with scale, so this is not an isolated complexity-order estimate.')
    supplementary=[]
    for name,path,note in [
        ('Revision_Raw',REV/'revision_raw.csv','All 2040 recorded runs; no resampling or row selection.'),
        ('Controlled_Contrasts',REV/'analysis/controlled_contrasts.csv','84 prespecified paired contrasts; Holm family=84.'),
        ('Frozen_Contrasts',REV/'analysis/frozen_test_contrasts.csv','24 paired contrasts; Holm family=24.'),
        ('Temperature_Contrasts',REV/'analysis/frozen_temperature_contrasts.csv','Six reversed-orientation contrasts from the same 24-test family, not new tests.'),
        ('Objective_Weight_Sweep',RAW/'exp415_sensitivity.csv','Exploratory objective reliability-weight changes; objectives are not on one common scale.')]:
        frame=pd.read_csv(path)
        if name=='Objective_Weight_Sweep': frame=frame[frame.parameter=='objective_reliability_weight']
        supplementary.append({'sheet':name,'title':name.replace('_',' '),'source':'Source: '+path.relative_to(ROOT).as_posix(),
             'note':note,'headers':list(frame.columns),'rows':matrix(frame)})
    (DEST/'table_index.json').write_text(json.dumps([{k:v for k,v in item.items() if k not in ('headers','rows')} for item in tables],indent=2),encoding='utf-8')
    payload=ROOT/'outputs/workbook_payload.json'
    payload.parent.mkdir(parents=True,exist_ok=True)
    payload.write_text(json.dumps({'main':tables,'supplement':supplementary},ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print(f'Exported {len(tables)} manuscript data tables and workbook payload: {payload}')

if __name__=='__main__':
    main()
