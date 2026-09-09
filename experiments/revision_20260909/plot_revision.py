"""English-only publication figures, true 600-dpi PNG plus vector PDF."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
sys.path.append('C:/RFOTO-ABC/pydeps_clean')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'datas/revision_20260909'
ANALYSIS = DATA/'analysis'
FIG = ROOT/'images/revision_20260909'
for ext in ('png', 'pdf'):
    (FIG/ext).mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family': ['Arial', 'DejaVu Sans'], 'font.size': 9.5,
    'axes.labelsize': 9.5, 'axes.titlesize': 10.5, 'axes.titleweight': 'bold',
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': 1.1,
    'legend.frameon': False, 'legend.fontsize': 9, 'pdf.fonttype': 42, 'ps.fonttype': 42,
    'svg.fonttype': 'none', 'savefig.facecolor': 'white'})
COLORS = {'RFOTO-ABC': '#8B1A1A', 'RFOTO-ABC-T16': '#B64342', 'Plain-ABC': '#767676',
          'LSHADE-lite': '#0F4D92', 'DE-RK': '#42949E', 'Offload-then-Allocate': '#42949E'}
MARKERS = {'RFOTO-ABC': 'o', 'RFOTO-ABC-T16': 's', 'Plain-ABC': '^', 'LSHADE-lite': 'D', 'DE-RK': 'v', 'Offload-then-Allocate': '^'}

def save(fig, name):
    fig.savefig(FIG/'png'/f'{name}.png', dpi=600, bbox_inches='tight', pad_inches=0.12)
    fig.savefig(FIG/'pdf'/f'{name}.pdf', dpi=600, bbox_inches='tight', pad_inches=0.12)
    plt.close(fig)

def controlled_convergence():
    methods = ['RFOTO-ABC', 'Plain-ABC', 'DE-RK', 'LSHADE-lite']
    fig, axes = plt.subplots(2, 3, figsize=(7.25, 5.0), sharex=True)
    grid = np.r_[14, np.arange(50, 1001, 50)]
    for row, init in enumerate(['greedy', 'random']):
        for col, scene in enumerate(['S2', 'S4', 'S6']):
            ax = axes[row, col]
            for method in methods:
                ys = []
                for run in range(20):
                    path = DATA/'run_records'/f'controlled_{scene}_{run:02d}_1000_{init}_{method}.json'
                    d = json.loads(path.read_text())
                    fe, obj = np.array(d['trace_fe']), np.array(d['trace_objective'])
                    positions = np.clip(np.searchsorted(fe, grid, side='right')-1, 0, len(fe)-1)
                    ys.append(obj[positions]/obj[0])
                ys = np.array(ys)
                ax.plot(grid, ys.mean(axis=0), color=COLORS[method], linewidth=1.6, label=method,
                        marker=MARKERS[method], markersize=3, markevery=5)
            ax.set_title(f'({chr(97+row*3+col)}) {scene}: {init.capitalize()} init.', loc='left')
            ax.grid(axis='y', color='#e3e3e3', linewidth=.6)
            ax.set_xlim(0, 1000)
            ax.set_xticks([0, 500, 1000])
            if col == 0:
                ax.set_ylabel('Best / initial objective')
            if row == 1:
                ax.set_xlabel('Function evaluations')
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=4, bbox_to_anchor=(.5, 1.005))
    fig.tight_layout(rect=[0, 0, 1, .94], pad=.9)
    save(fig, 'Rev_Fig04_Matched_Initialization')

def component_effects():
    c = pd.read_csv(ANALYSIS/'controlled_contrasts.csv')
    c = c[(c.contrast=='matched_search') & (c.initialization=='greedy') & (c.budget==1000)]
    methods = ['No-risk-sampling', 'No-fair-selection', 'Random-scout', 'Uniform-allocation', 'Plain-ABC']
    labels = ['No risk sampling', 'No fair selection', 'Random scout', 'Uniform allocation', 'Plain-ABC']
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.45), sharey=True)
    for col, scene in enumerate(['S2', 'S4', 'S6']):
        ax = axes[col]
        g = c[c.scenario==scene].set_index('comparator').loc[methods]
        y = np.arange(len(methods))
        mean = g.mean_relative_gain_pct.to_numpy()
        lo, hi = g.ci_low_pct.to_numpy(), g.ci_high_pct.to_numpy()
        ax.errorbar(mean, y, xerr=np.array([mean-lo, hi-mean]), fmt='o', color='#8B1A1A',
                    markersize=4.5, capsize=3, linewidth=1.2)
        ax.axvline(0, color='#555555', linewidth=.8, linestyle='--')
        ax.set_yticks(y, labels)
        ax.set_ylim(len(methods)-.45, -.75)
        ax.set_title(f'({chr(97+col)}) {scene}', loc='left')
        ax.set_xlabel('RFOTO relative gain (%)')
        ax.grid(axis='x', color='#e3e3e3', linewidth=.6)
        extent = max(abs(lo).max(), abs(hi).max(), .5)
        ax.set_xlim(min(lo.min(),0)-extent*.15, max(hi.max(),0)+extent*.45)
        for yi, val, high in zip(y, mean, hi):
            ax.annotate(f'{val:+.2f}', (high, yi), xytext=(4, 4), textcoords='offset points', fontsize=8)
    fig.tight_layout(pad=1)
    save(fig, 'Rev_Fig06_Controlled_Ablation')

def frozen_temperature(df):
    test = df[df.suite=='frozen_test']
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.25))
    scenes = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']
    x = np.arange(6)
    for method, label in [('RFOTO-ABC', 'Temperature 0.8'), ('RFOTO-ABC-T16', 'Temperature 1.6')]:
        g = test[test.algorithm==method].groupby('scenario')
        for ax, metric, factor in [(axes[0], 'objective', 1), (axes[1], 'violation_rate', 100)]:
            mean = g[metric].mean().reindex(scenes)*factor
            se = g[metric].std().reindex(scenes)/np.sqrt(20)*factor
            ax.errorbar(x, mean, yerr=se, color=COLORS[method], marker=MARKERS[method],
                        linewidth=1.5, markersize=4, capsize=2, label=label)
    for ax in axes:
        ax.set_xticks(x, scenes)
        ax.set_xlabel('Fresh test scenario')
        ax.grid(axis='y', color='#e3e3e3', linewidth=.6)
    axes[0].set_ylabel('Mean objective')
    axes[1].set_ylabel('Deadline violation (%)')
    axes[0].set_title('(a) Objective', loc='left')
    axes[1].set_title('(b) Deadline violations', loc='left')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, ncol=2, loc='upper center', bbox_to_anchor=(.5, 1.02))
    fig.tight_layout(rect=[0,0,1,.91], pad=.9)
    save(fig, 'Rev_Fig08_Frozen_Temperature')

def frozen_comparison(df):
    test = df[df.suite=='frozen_test']
    p = test.groupby(['algorithm', 'scenario']).objective.mean().unstack()
    c = pd.read_csv(ANALYSIS/'frozen_test_contrasts.csv')
    scenes = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']
    fig, axes = plt.subplots(1, 2, figsize=(7.3, 3.7), gridspec_kw={'width_ratios':[1.15,1]})
    x = np.arange(6)
    methods = ['RFOTO-ABC','RFOTO-ABC-T16','LSHADE-lite','Offload-then-Allocate']
    labels = {'RFOTO-ABC':'RFOTO (0.8)', 'RFOTO-ABC-T16':'RFOTO (1.6)',
              'LSHADE-lite':'LSHADE-lite', 'Offload-then-Allocate':'Two-stage rule'}
    for method in methods:
        axes[0].plot(x, (p.loc[method]/p.min(axis=0)).reindex(scenes), color=COLORS[method],
                     marker=MARKERS[method], markersize=4, linewidth=1.5, label=labels[method])
    for offset, method in [(-.12,'LSHADE-lite'),(.12,'Offload-then-Allocate')]:
        g = c[c.comparator==method].set_index('scenario').loc[scenes]
        mean = g.mean_relative_gain_pct.to_numpy()
        lo, hi = g.ci_low_pct.to_numpy(), g.ci_high_pct.to_numpy()
        axes[1].errorbar(x+offset, mean, yerr=np.array([mean-lo, hi-mean]), fmt=MARKERS[method],
                         color=COLORS[method], capsize=2, markersize=4, label=labels[method])
    axes[1].axhline(0, color='#555555', linewidth=.8, linestyle='--')
    axes[0].set_title('(a) Frozen configurations', loc='left')
    axes[1].set_title('(b) RFOTO at temperature 0.8', loc='left')
    axes[0].set_ylabel('Mean / best method mean')
    axes[1].set_ylabel('Paired relative gain (%)')
    for ax in axes:
        ax.set_xticks(x, scenes)
        ax.set_xlabel('Fresh test scenario')
        ax.grid(axis='y', color='#e3e3e3', linewidth=.6)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='upper center', ncol=2, bbox_to_anchor=(.5, 1.025))
    fig.tight_layout(rect=[0,0,1,.86], pad=.8)
    save(fig, 'Rev_Fig10_Frozen_Test')

if __name__ == '__main__':
    df = pd.read_csv(DATA/'revision_raw.csv')
    controlled_convergence()
    component_effects()
    frozen_temperature(df)
    frozen_comparison(df)
    from PIL import Image
    report = {p.name: {'size':Image.open(p).size, 'dpi':Image.open(p).info.get('dpi')} for p in (FIG/'png').glob('*.png')}
    (FIG/'figure_audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
