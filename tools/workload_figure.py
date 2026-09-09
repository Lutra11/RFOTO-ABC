"""Reconstruct the historical workload-mapping plot inputs, without new sampling rules."""
from pathlib import Path
import sys
import numpy as np
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from algorithm.rfoto_core import build_scenario

def ecdf(a):
    x=np.sort(np.asarray(a,float))
    return x,np.arange(1,len(x)+1)/len(x)

def draw(destination):
    with np.load(ROOT/'datasets/processed/alibaba_workload_profiles.npz',allow_pickle=False) as d:
        compute=d['compute_cycles'].astype(float)/1e9
        util=d['machine_cpu_util_percent'].astype(float)
        instances=d['instance_num'].astype(float)
    generated=[]
    for si,scene in enumerate(['S1','S2','S3','S4','S5','S6']):
        for run in range(30):
            s=build_scenario(scene,run,731000+si*1000+run)
            generated.append((s['C']/1e9,s['queue_delay']*1e3,np.full(s['n'],s['n'],float)))
    task=np.concatenate([x[0] for x in generated]); queue=np.concatenate([x[1] for x in generated]); count=np.concatenate([x[2] for x in generated])
    plt.rcParams.update({'font.family':['Arial','DejaVu Sans'],'font.size':8.5,'axes.titlesize':9,
        'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False,'legend.fontsize':7,
        'pdf.fonttype':42,'savefig.facecolor':'white'})
    fig,axes=plt.subplots(1,3,figsize=(7.1,2.4))
    gray='#767676'; blue='#0F4D92'; red='#B64342'
    axes[0].plot(*ecdf(np.clip(compute,0,5)),color=gray,label='Alibaba-derived pool')
    axes[0].plot(*ecdf(np.clip(task,0,5)),color=blue,label='Generated tasks')
    axes[0].set(xlabel='Compute demand (Gcycles)',ylabel='Empirical CDF',title='(a) Task compute demand')
    axes[0].legend(loc='lower right')
    axes[1].plot(*ecdf(util),color=gray,label='Alibaba CPU util.')
    twin=axes[1].twiny(); twin.plot(*ecdf(queue),color='#E69F00',label='Generated queue delay')
    axes[1].set(xlabel='Source CPU utilization (%)',ylabel='Empirical CDF',title='(b) Server load mapping')
    twin.set_xlabel('Queue delay (ms)')
    lines=axes[1].lines+twin.lines
    axes[1].legend(lines,[x.get_label() for x in lines],loc='lower right')
    axes[2].boxplot([np.clip(instances,0,np.quantile(instances,.98)),count],
        tick_labels=['Alibaba\ninstances','Scenario\nusers'],patch_artist=True,widths=.55,
        boxprops={'facecolor':'#CFCECE','edgecolor':'#222222','linewidth':.65},
        medianprops={'color':red,'linewidth':1},whiskerprops={'color':'#222222','linewidth':.65},
        capprops={'color':'#222222','linewidth':.65},
        flierprops={'marker':'.','markersize':1.3,'markerfacecolor':gray,'markeredgecolor':gray,'alpha':.25})
    axes[2].set(ylabel='Count',title='(c) Scale boundary check')
    for ax in axes: ax.grid(axis='y',alpha=.25,linewidth=.6)
    fig.tight_layout(pad=1.0)
    for ext in ['png','pdf']:
        (destination/ext).mkdir(parents=True,exist_ok=True)
        fig.savefig(destination/ext/f'Fig01_Workload_Mapping.{ext}',dpi=600,bbox_inches='tight',pad_inches=.12)
    plt.close(fig)
