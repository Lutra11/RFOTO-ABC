"""Figures from original recorded experimental CSVs; never reads effect preview."""
from pathlib import Path
import os,sys,json
OUT=Path(os.environ.get('RFOTO_FIGURE_OUTPUT_ROOT',str(Path(__file__).resolve().parent)))
OUT.mkdir(parents=True,exist_ok=True)
EXPORT_DPI=int(os.environ.get('RFOTO_FIGURE_DPI','600'))
os.environ['MPLCONFIGDIR']=str(OUT/'mplconfig')
import numpy as np
import pandas as pd
try:
    import matplotlib
except ModuleNotFoundError:
    sys.path.append('C:/RFOTO-ABC/pydeps_clean')
    import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

R=Path(__file__).resolve().parents[1]/'datas/raw_results'
F=OUT/'figures'; F.mkdir(exist_ok=True)
RED='#8B1E2D'; BLUE='#0F4D92'; TEAL='#42949E'; GREEN='#238B45'; GRAY='#767676'; PURPLE='#9A4D8E'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':10.5,'axes.titlesize':11,'axes.labelsize':10.5,'axes.linewidth':1.1,'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False,'legend.fontsize':10,'xtick.labelsize':10,'ytick.labelsize':10,'svg.fonttype':'none','pdf.fonttype':42,'savefig.facecolor':'white'})
captions={}
def finish(fig,name,caption):
    fig.savefig(F/(name+'.png'),dpi=EXPORT_DPI,bbox_inches='tight',pad_inches=.08)
    fig.savefig(F/(name+'.pdf'),dpi=EXPORT_DPI,bbox_inches='tight',pad_inches=.08)
    plt.close(fig); captions[name]=caption
def tidy(ax):
    ax.grid(axis='y',alpha=.18,linewidth=.8); ax.set_axisbelow(True)
def meanstd(df,groups,metric):
    return df.groupby(groups)[metric].agg(['mean','std'])
SCENES=['S1','S2','S3','S4','S5','S6']
advanced=pd.read_csv(R/'exp423_advanced_algorithm_comparison.csv')
pv=advanced.pivot(index=['scenario','run'],columns='algorithm',values='objective')
ranks=pv.rank(axis=1).mean().sort_values()
means=advanced.groupby(['algorithm','scenario']).objective.mean().unstack().loc[ranks.index,SCENES]
ratio=means/means.min(axis=0)
fig,ax=plt.subplots(figsize=(7.2,5.1),layout='constrained')
im=ax.imshow(ratio,cmap='Blues',aspect='auto',vmin=1,vmax=ratio.to_numpy().max())
ax.set_xticks(range(6),SCENES); ax.set_yticks(range(len(ranks)),[f'{a}  ({r:.2f})' for a,r in ranks.items()])
for i in range(len(ranks)):
    for j in range(6):
        v=ratio.iloc[i,j]
        ax.text(j,i,f'{v:.2f}',ha='center',va='center',fontsize=10.5,color='white' if v>3.4 else (RED if i==0 else '#202020'),fontweight='bold' if i==0 else 'normal')
ax.add_patch(Rectangle((-.5,-.5),6,1,fill=False,edgecolor=RED,linewidth=2.1))
ax.get_yticklabels()[0].set_color(RED);ax.get_yticklabels()[0].set_fontweight('bold')
ax.set_title('Scenario-normalized objective',loc='left');ax.set_ylabel('Algorithm (mean rank)')
fig.colorbar(im,ax=ax,shrink=.66,pad=.02,label='Mean objective / scenario best')
finish(fig,'Fig2_Advanced_Comparison','先进适配启发式比较。每个场景8个配对实例，11种算法均使用320次目标函数评价，共48个场景–实例块。各算法场景均值除以同场景最小均值，颜色和单元数值表示该比值；行标签括号为实例内11算法秩对48块的均值，并列使用平均秩。深红色标示RFOTO-ABC。改进方法与六个先进适配基线使用贪心种子，经典ABC/GA/PSO/DE的初始化不同；该图评价给定适配器与预算，非原作者完整实现的无条件比较。来源：exp423_advanced_algorithm_comparison.csv。')

# Sparse convergence is forward-filled, never interpolated into fictitious improvement.
tr=pd.read_csv(R/'exp423_advanced_algorithm_trace.csv')
fig,axs=plt.subplots(1,3,figsize=(7.2,3.2),layout='constrained')
names=['RFOTO-ABC','LSHADE-lite','JADE','Gbest-ABC']
colors=[RED,BLUE,TEAL,GRAY]; styles=['-','--',':','-.']
for ax,scene in zip(axs,['S2','S4','S6']):
    for alg,c,ls in zip(names,colors,styles):
        curves=[]; grid=np.arange(24,321)
        for run in range(3):
            d=tr[(tr.scenario==scene)&(tr.algorithm==alg)&(tr.run==run)].sort_values('fe')
            final=advanced[(advanced.scenario==scene)&(advanced.algorithm==alg)&(advanced.run==run)].iloc[0]
            x=np.append(d.fe.to_numpy(),320);y=np.append(d.objective.to_numpy(),final.objective)
            curves.append(y[np.clip(np.searchsorted(x,grid,side='right')-1,0,len(y)-1)]/y[0])
        z=np.asarray(curves); mu=z.mean(axis=0);sd=z.std(axis=0,ddof=1)
        ax.plot(grid,mu,color=c,ls=ls,lw=1.6 if alg=='RFOTO-ABC' else 1.2,label=alg,zorder=5 if alg=='RFOTO-ABC' else 3)
        if alg=='RFOTO-ABC':ax.fill_between(grid,mu-sd,mu+sd,color=c,alpha=.13)
    ax.set_title(scene); ax.set_xlabel('Evaluations');ax.set_xlim(24,320);tidy(ax)
axs[0].set_ylabel('Best / initial objective');fig.legend(*axs[-1].get_legend_handles_labels(),loc='outside upper center',ncol=4,fontsize=10)
finish(fig,'Fig3_Convergence','相同贪心初解条件下的预算内改进。S2、S4、S6各取先进比较已记录轨迹的前3个配对实例，曲线为“当前最优目标值/本次运行初始最优值”的均值，RFOTO-ABC阴影为实例间标准差。稀疏评价检查点采用前向保持，320次评价端点来自对应结果CSV。所选基线的初始最优目标在这9个实例中与RFOTO-ABC相同，多条基线轨迹重合于1。图示初始化之后的局部改进，不能据此推断长期或全局收敛。来源：exp423_advanced_algorithm_trace.csv及exp423_advanced_algorithm_comparison.csv。')

main=pd.read_csv(R/'exp48_main_comparison.csv')
fig,axs=plt.subplots(1,2,figsize=(7.2,3.5),layout='constrained')
names=['RFOTO-ABC','Offload-then-Allocate','Load-Aware']
for ax,metric,title,yl in zip(axs,['objective','violation_rate'],['(a) Composite objective','(b) Deadline violation'],['Objective (lower is better)','Violation rate (%)']):
    for k,(alg,c,m) in enumerate(zip(names,[RED,BLUE,TEAL],['o','s','^'])):
        g=meanstd(main[main.algorithm==alg],['scenario'],metric).reindex(SCENES);scale=100 if metric=='violation_rate' else 1
        ax.errorbar(np.arange(6)+(k-1)*.15,g['mean']*scale,yerr=g['std']*scale,color=c,marker=m,ls='none',ms=4,capsize=2,elinewidth=1,label=alg)
    ax.set_xticks(range(6),SCENES);ax.set_xlabel('Scenario');ax.set_ylabel(yl);ax.set_title(title,loc='left');tidy(ax)
fig.legend(*axs[0].get_legend_handles_labels(),loc='outside upper center',ncol=3,fontsize=10)
finish(fig,'Fig1_Main_Comparison','主实验中RFOTO-ABC与两个整体平均秩最佳的确定性规则比较。点与误差线分别为30个配对场景实例的均值与标准差；左图为复合目标值，右图为截止时间违约率。RFOTO-ABC在S1–S3使用500次、S4–S6使用375次目标评价，规则法执行一次。S2、S4中Offload-then-Allocate的目标均值更低，构成方法适用边界。来源：exp48_main_comparison.csv。')

ab=pd.read_csv(R/'exp414_ablation.csv');cols=['t_hat','e_hat','r_hat','v_hat','fairness_loss']; ab['common']=ab[cols].to_numpy()@np.array([.25,.15,.20,.25,.15])
order=['RFOTO-ABC','RFOTO-ABC-R','RFOTO-ABC-F','RFOTO-ABC-D','RFOTO-ABC-G','RFOTO-ABC-S','RFOTO-ABC-RF','RFOTO-ABC-DG'];labs=['Full','No risk guidance','No fairness terms*','Uniform allocation','No greedy seeding','Random scout','No risk/fairness*','Uniform, no seeding']
g=meanstd(ab,['algorithm'],'common').reindex(order)
fig,(a,b)=plt.subplots(2,1,figsize=(7.2,6.8),gridspec_kw={'height_ratios':[1.35,1]},layout='constrained')
for i,alg in enumerate(order):a.errorbar(g.loc[alg,'mean'],i,xerr=g.loc[alg,'std'],fmt='o',color=RED if i==0 else BLUE,capsize=3,ms=5)
a.set_yticks(range(8),labs);a.invert_yaxis();a.set_xlabel('Common-weight objective');a.set_title('(a) Components and conditional utility',loc='left');a.grid(axis='x',alpha=.18)
sk=pd.read_csv(R/'exp420_ablation_resource_skew_raw.csv'); xx=np.arange(2)
for i,(alg,c,lab) in enumerate([('RFOTO-ABC',RED,'Full'),('RFOTO-ABC-D',BLUE,'Uniform')]):
    d=sk[sk.algorithm==alg];vs=d[['bandwidth_share_cv','cpu_share_cv']]
    b.bar(xx+(i-.5)*.32,vs.mean(),width=.32,yerr=vs.std(),capsize=4,color=c,edgecolor='#333333',linewidth=.6,label=lab,hatch='' if i==0 else '//')
    if i==1:
        for x in xx+.16:b.text(x,.012,'0',ha='center',va='bottom',color=BLUE,fontsize=10)
b.set_xticks(xx,['Bandwidth share','CPU share'],rotation=10);b.set_ylabel('Within-server allocation CV');b.set_title('(b) Allocation imbalance',loc='left');b.legend(loc='upper right');tidy(b)
finish(fig,'Fig4_Ablation','S4条件下的消融与资源分配诊断。每个变体20个配对实例、400次评价。上图用原始五个目标分量统一按(0.25,0.15,0.20,0.25,0.15)重新评价，点与误差线为均值±标准差；*表示原优化同时改变公平性引导和目标公平性权重，统一事后评分并不能使其成为单一因素消融。Uniform allocation以均分替代随机键softmax分配，仍保留容量与可靠性修复。下图来自原20实例重运行诊断，展示服务器内资源份额变异系数的均值±标准差；均分的CV接近浮点零。来源：exp414_ablation.csv、exp420_ablation_resource_skew_raw.csv。')

sen=pd.read_csv(R/'exp415_sensitivity.csv')
fig,axs=plt.subplots(2,2,figsize=(7.2,5.6),layout='constrained')
for ax,par,title,xlabel in zip(axs.flat,['population','greedy_ratio','resource_temperature','fairness_strength'],['(a) Population size','(b) Greedy-seeding ratio','(c) Resource temperature','(d) Fairness-selection strength'],['Population size','Greedy-seeding ratio','Shared bandwidth/CPU temperature','Fairness-selection strength']):
    g=meanstd(sen[sen.parameter==par],['value'],'objective').sort_index()
    ax.errorbar(g.index,g['mean'],yerr=g['std'],fmt='o-',color=RED,capsize=3,lw=1.5,ms=5)
    ax.set_xticks(g.index);ax.set_xlabel(xlabel);ax.set_ylabel('Objective (lower is better)');ax.set_title(title,loc='left');tidy(ax)
finish(fig,'Fig5_Sensitivity','S4单因素参数敏感性。每个取值使用相同6个场景实例与优化随机种子，固定280次函数评价，点与误差线为均值±标准差。各面板分别改变种群规模、贪心初始化比例、带宽与CPU共同温度、公平性选择强度，其他设置维持原默认值。此为局部探索，未独立验证参数最优性。来源：exp415_sensitivity.csv。')

ood=pd.read_csv(R/'exp417_ood.csv');caseorder=['in_distribution','bursty_heavy_load','strong_server_heterogeneity','channel_estimation_shift'];labels=['Reference\nS2','Load+\nS3','Resources\nS5','Channel\nS4']
fig,axs=plt.subplots(2,2,figsize=(7.2,5.8),layout='constrained')
for ax,metric,title,yl in zip(axs.flat,['objective','violation_rate','jain','offload_rate'],['(a) Composite objective','(b) Deadline violation','(c) Service fairness','(d) Offloading behavior'],['Objective','Violation rate (%)','Jain fairness index','Offloading rate (%)']):
    for k,(alg,c,m) in enumerate(zip(['RFOTO-ABC','Standard-ABC','Delay-Greedy'],[RED,BLUE,TEAL],['o','s','^'])):
        g=meanstd(ood[ood.algorithm==alg],['ood_case'],metric).reindex(caseorder);sc=100 if metric in ['violation_rate','offload_rate'] else 1
        ax.errorbar(np.arange(4)+(k-1)*.15,g['mean']*sc,yerr=g['std']*sc,color=c,marker=m,ls='none',capsize=2,ms=4,label=alg)
    ax.set_xticks(range(4),labels);ax.set_ylabel(yl);ax.set_title(title,loc='left');tidy(ax)
fig.legend(*axs[0,0].get_legend_handles_labels(),loc='outside upper center',ncol=3,fontsize=10)
finish(fig,'Fig6_Scenario_Transfer','跨场景参数扰动测试。四条件依次为S2参考条件、S3计算需求放大1.35倍并截断至5 Gcycles、S5服务器CPU容量统一缩减至0.70倍且带宽放大1.20倍、S4成功概率乘0.80且瞬时信道增益损失2 dB。每条件15个配对实例，优化算法350次评价，Delay-Greedy一次评价。点和误差线为实例均值±标准差。四条件来自同一生成器，算法可访问变化后的参数并重新优化，因此该图检验场景迁移适应性，不是未见真实数据或隐藏信道估计偏差上的外部泛化。来源：exp417_ood.csv。')

(OUT/'figure_captions.json').write_text(json.dumps(captions,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'figures':list(captions),'output':str(F)},ensure_ascii=False))
