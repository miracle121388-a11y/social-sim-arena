"""Localize existing evidence-backed tables and plots without changing English outputs."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workspace import path,digest
import json,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

for folder in ['paper/tables_zh','paper/figures_zh','paper/qa/zh']:
    path(folder).mkdir(parents=True,exist_ok=True)
S=json.loads(path('provenance/closure/supplement.json').read_text(encoding='utf-8'))
A=json.loads(path('provenance/closure/evolution-audit.json').read_text(encoding='utf-8'))
C=json.loads(path('provenance/campaign60/summary.json').read_text(encoding='utf-8'))
assert digest('method.py')==C['method_sha256']
common=r'逐活动 AUC $\times10^3$，括号为 95\% 世界 bootstrap 区间；24 个独立世界，固定训练数据、证据与模板。'
captions={
 'acquisition_original':'原始对照：校准与取证策略同时变化。'+common,
 'acquisition_matched':'同先验取证对照：所有方法采用进化先验。'+common,
 'ablations':'冻结方法消融。星号表示同时改变了先验或单点选择目标。'+common,
 'calibration':'被动校准基线，不获取额外证据。'+common,
 'macro':r'宏平均 AUC $\times10^3$ 及其相对 Full 的描述性均值差。区间是均值的世界 bootstrap 区间，不是预测区间。',
 'paired':r'对照减 Full 的配对活动 AUC 差值 $\times10^6$，附 95\% 世界 bootstrap 区间。正值有利于 Full；微小差值不一定具有实际意义。',
 'stress':r'Full 的事后区间告警率（百分比）与 95\% 世界 bootstrap 区间。“无偏移”衡量误报率；24 个世界中端点比例的区间可能退化。',
 'stress_magnitude':r'相对于无偏移世界的真实轨迹位移，RMSE $\times10^3$。单独报告偏移强度，以区分扰动很弱与检测不敏感。',
 'timing':'10 次同步 GPU 配对计时，执行顺序交替。分别计算每一对的加速比再取中位数，因此不必等于两类时间中位数之比。',
 'uncertainty':r'最终预算下的不确定性均值与 95\% 世界 bootstrap 区间。覆盖率对应逐点 90\% 预测区间。',
 'golden':'原冻结测试缓存的描述性结果。Random 对三次查询重复取平均；这些相互影响的活动不是独立重复样本。',
 'evolution_all':'全部 60 个经审计的候选。开发分数来自自适应选择，不是独立验证。',
}
replacements={
 'Matched-prior Standard OED':'同先验 Standard OED','Matched-prior ParamIG':'同先验 ParamIG',
 'Matched-prior Entropy':'同先验 Entropy','Matched-prior Random':'同先验 Random',
 'Without combination target':'移除组合目标','Without batch conditioning':'移除批量条件化',
 'Without sharing*':'取消参数共享*','Original single point*':'原单点估计*','Matched MAP':'匹配 MAP',
 'Simple statistics':'简单统计模型','Uncalibrated':'未校准模型','Process only':'仅过程校准',
 'Trajectory only':'仅轨迹校准','Passive V1':'被动 V1',
 'Comparator minus Full':'对照减 Full','Difference from Full':'相对 Full 的差值',
 'Macro AUC':'宏平均 AUC','Pooled AUC':'合并 AUC','Activity 1':'活动 1','Activity 2':'活动 2','Activity 3':'活动 3',
 'Coverage (percent)':'覆盖率（百分比）','Interval width (fraction)':'区间宽度（比例）',
 'Epistemic variance x 1e8':r'认识方差 $\times10^8$','Aleatoric variance x 1e4':r'随机方差 $\times10^4$',
 'Max. difference':'最大残差','Median ratio':'配对加速比中位数','Cov. (ms)':'协方差（毫秒）','Enum. (ms)':'枚举（毫秒）',
 'uniform compatible':'均匀相容先验','frozen':'冻结先验','Truth rule':'真值规则',
 'propagation':'传播偏移','waiting':'候补偏移','transport':'交通冲击','both':'两者叠加','none':'无偏移',
 'Parent AUC':'父版本 AUC','Dev AUC':'开发 AUC','Decision':'决定','Commit':'提交',
 'Round':'轮次','KEEP':'保留','REVERT':'回退','Coverage':'覆盖率','Width':'宽度','Quantity':'量','Method':'方法','Prior':'先验',
}
for name,caption in captions.items():
    original=path('paper/tables/'+name+'.tex').read_text(encoding='utf-8')
    lines=original.splitlines()
    for i,line in enumerate(lines):
        if line.startswith(r'\caption{'):
            suffix=line[line.rfind('}')+1:]
            # Longtable puts its label on the same line; retain it verbatim.
            label_pos=line.find(r'\label{')
            if label_pos>=0:suffix=line[label_pos:]
            lines[i]=r'\caption{'+caption+'}'+suffix
        elif not line.startswith((r'\label',r'\begin',r'\end')):
            for en,zh in replacements.items():line=line.replace(en,zh)
            lines[i]=line
    translated='\n'.join(lines)+'\n'
    # Ensure every row's scientific numbers are untouched (exclude labels/header).
    def rows(text):
        return [re.findall(r'(?<![A-Za-z])[+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?',x.split('&',1)[1])
                for x in text.splitlines() if '&' in x and re.search(r'\d',x.split('&',1)[1])
                and not any(t in x for t in ['Activity','活动','Parent AUC','父版本 AUC'])]
    assert rows(original)==rows(translated),name
    path('paper/tables_zh/'+name+'.tex').write_text(translated,encoding='utf-8')

plt.rcParams.update({'font.family':['Microsoft YaHei','DejaVu Sans'],'font.size':8,
 'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,'axes.unicode_minus':False})
colors=['#0072B2','#E69F00','#009E73','#CC79A7','#D55E00']
original=['Random','Entropy','ParamIG','Standard_OED','Covariance']
matched=['SamePrior_Random','SamePrior_Entropy','SamePrior_ParamIG','SamePrior_Standard_OED','Covariance']
def label(n):return 'Full' if n=='Covariance' else n.replace('SamePrior_','').replace('_',' ')
fig,axes=plt.subplots(2,3,figsize=(7,4),layout='constrained')
for row,names in enumerate([original,matched]):
 for e in range(3):
  ax=axes[row,e]
  for j,n in enumerate(names):
   stat=S['summary'][n]['event_rmse_curve'];y=np.asarray(stat['mean'])[:,e]
   ax.plot(S['budgets'],y*1000,color=colors[j],label=label(n),ls=['-','--','-.',':','-'][j],lw=1.3)
   if row==0:ax.fill_between(S['budgets'],np.asarray(stat['ci95_low'])[:,e]*1000,np.asarray(stat['ci95_high'])[:,e]*1000,color=colors[j],alpha=.08)
  ax.set_title(f'活动 {e+1} / '+('同先验' if row else '原始先验'));ax.set_xlabel('证据预算');ax.grid(alpha=.12)
  if e==0:ax.set_ylabel('轨迹 RMSE × 1000')
  if row==1:ax.ticklabel_format(axis='y',style='plain',useOffset=False)
axes[0,0].legend(fontsize=6,frameon=False,ncol=2)
fig.savefig(path('paper/figures_zh/budget_curves.pdf'));plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(7,2.5),layout='constrained')
for decision,color,marker,zh in [('REVERT','#999999','x','回退'),('KEEP','#0072B2','o','保留')]:
 rows_=[r for r in A['rows'] if r['decision']==decision]
 axes[0].scatter([r['round'] for r in rows_],[r['dev_auc'] for r in rows_],s=19,color=color,marker=marker,label=zh)
best=C['baseline_dev_auc'];ys=[best]
for r in A['rows']:
 if r['decision']=='KEEP':best=r['dev_auc']
 ys.append(best)
axes[0].step(range(61),ys,where='post',lw=1,color='#0072B2')
axes[0].set(xlabel='开发试验轮次',ylabel='开发 AUC');axes[0].legend(frameon=False,fontsize=7)
for j,(name,v) in enumerate(S['timing'].items()):
 for k,(key,color,zh) in enumerate([('covariance_ms','#0072B2','协方差'),('enumeration_ms','#D55E00','显式枚举')]):
  y=[r[key] for r in v['raw']];axes[1].scatter(np.full(len(y),j)+(k-.5)*.22,y,color=color,s=13,label=zh if j==0 else None)
axes[1].set(yscale='log',ylabel='同步计时（毫秒）',xticks=[0,1],xticklabels=['冻结先验','均匀相容先验']);axes[1].legend(frameon=False,fontsize=7)
fig.savefig(path('paper/figures_zh/evolution_timing.pdf'));plt.close(fig)

stress=S['stress_summary']['Covariance'];matrix=np.array([v['interval_alarm']['mean'] for v in stress.values()])*100
fig,ax=plt.subplots(figsize=(5.4,2.4),layout='constrained');im=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=100,aspect='auto')
ax.set(xticks=range(3),xticklabels=['活动 1','活动 2','活动 3'],yticks=range(len(stress)),yticklabels=[replacements[n] for n in stress])
for i in range(matrix.shape[0]):
 for j in range(3):ax.text(j,i,f'{matrix[i,j]:.1f}%',ha='center',va='center',color='white' if matrix[i,j]>60 else 'black')
fig.colorbar(im,ax=ax,label='告警率（%）');fig.savefig(path('paper/figures_zh/stress_alarms.pdf'));plt.close(fig)
path('paper/qa/zh/assets.json').write_text(json.dumps({'tables_translated':len(captions),'numeric_rows_identical':True,'figures':3,'method_sha256':digest('method.py'),'source_supplement_sha256':digest('provenance/closure/supplement.json')},indent=2)+'\n',encoding='utf-8')
print('Chinese tables and vector figures generated; numeric rows unchanged.')
