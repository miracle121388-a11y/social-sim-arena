"""Generate manuscript assets from immutable, explicitly selected result files.

Run from repository root: .venv-research/Scripts/python.exe -B paper/generate_artifacts.py
No simulation, optimization, or selection on test performance is performed here.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workspace import path, digest
import csv
import json
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

INPUTS = ['provenance/closure/supplement.json', 'provenance/closure/golden-test.json',
          'provenance/closure/evolution-audit.json', 'provenance/campaign60/summary.json']
S, G, A, C = [json.loads(path(p).read_text(encoding='utf-8')) for p in INPUTS]
assert digest('method.py') == C['method_sha256'] == S['method_sha256'] == G['method_sha256']
for folder in ['paper/figures', 'paper/tables', 'paper/sections']:
    path(folder).mkdir(parents=True, exist_ok=True)

def write(name, content):
    path('paper/'+name).write_text(content, encoding='utf-8')

def esc(s):
    return str(s).replace('_', r'\_').replace('%', r'\%').replace('&', r'\&')

LABELS = {'Covariance':'Full', 'NoSharing':'Without sharing*',
          'NoCombination':'Without combination target', 'SinglePoint':'Original single point*',
          'MatchedMAP':'Matched MAP', 'NoBatchDedup':'Without batch conditioning',
          'SimpleStats':'Simple statistics', 'Uncalibrated':'Uncalibrated',
          'ProcessOnly':'Process only', 'TrajectoryOnly':'Trajectory only', 'PassiveV1':'Passive V1'}

def label(n):
    return LABELS.get(n,n.replace('SamePrior_', 'Matched-prior ').replace('_',' '))

def ci(stat, e=None, scale=1000, precision=2):
    x=[stat[k] if e is None else stat[k][e] for k in ['mean','ci95_low','ci95_high']]
    return f'{scale*x[0]:.{precision}f} [{scale*x[1]:.{precision}f}, {scale*x[2]:.{precision}f}]'

def table(filename, headers, rows, caption, key, small=True):
    placement='H' if filename in {'golden','calibration','paired','uncertainty','stress_magnitude'} else 'tbp'
    lines=[r'\begin{table}['+placement+']', r'\centering', r'\caption{'+caption+'}',r'\label{tab:'+key+'}',
           r'\scriptsize' if small else r'\small',r'\setlength{\tabcolsep}{3pt}',
           r'\begin{tabular}{l'+'r'*(len(headers)-1)+'}',r'\toprule',
           ' & '.join(headers)+r' \\',r'\midrule']
    lines += [' & '.join(map(esc,row))+r' \\' for row in rows]
    write('tables/'+filename+'.tex','\n'.join(lines+[r'\bottomrule',r'\end{tabular}',r'\end{table}','']))

summary=S['summary']
original=['Random','Entropy','ParamIG','Standard_OED','Covariance']
matched=['SamePrior_Random','SamePrior_Entropy','SamePrior_ParamIG','SamePrior_Standard_OED','Covariance']
ablations=['Covariance','NoSharing','NoCombination','SinglePoint','MatchedMAP','NoBatchDedup']
baseline=['SimpleStats','Uncalibrated','ProcessOnly','TrajectoryOnly','PassiveV1']
for file,names,caption in [
 ('acquisition_original',original,'Original comparison: calibration and acquisition both vary.'),
 ('acquisition_matched',matched,'Controlled acquisition comparison: all methods use the evolved prior.'),
 ('ablations',ablations,'Frozen-method ablations. Asterisks identify changes that also alter the prior or point-selection objective.'),
 ('calibration',baseline,'Passive calibration baselines. These rows acquire no additional evidence.')]:
    table(file,['Method','Activity 1','Activity 2','Activity 3'],
          [[label(n)]+[ci(summary[n]['event_auc'],e) for e in range(3)] for n in names],
          caption+r' Activity AUC $\times10^3$ with 95\% world-bootstrap intervals; 24 worlds, fixed training data, evidence and templates.',file)
table('macro',['Method','Macro AUC','Difference from Full'],
      [[label(n),ci(summary[n]['macro_auc'],precision=4),
        f"{1000*(summary[n]['macro_auc']['mean']-summary['Covariance']['macro_auc']['mean']):+.4f}"] for n in
       ['Covariance','MatchedMAP','SamePrior_Random','NoCombination','NoBatchDedup','NoSharing']],
      r'Macro AUC $\times10^3$ and descriptive mean differences. Intervals are world-bootstrap intervals on the mean, not predictive intervals.','macro')
table('paired',['Comparator minus Full','Activity 1','Activity 2','Activity 3'],
      [[label(n)]+[ci(S['paired_event_auc_minus_full'][n],e,scale=1e6,precision=2) for e in range(3)]
       for n in ['MatchedMAP','SamePrior_Random','NoCombination','NoBatchDedup']],
      r'Paired activity AUC differences $\times10^6$ with 95\% world-bootstrap intervals. Positive favors Full; tiny differences are not necessarily practically meaningful.','paired')
stress=S['stress_summary']['Covariance']
table('stress',['Truth rule','Activity 1','Activity 2','Activity 3'],
      [[n]+[ci(v['interval_alarm'],e,scale=100,precision=1) for e in range(3)] for n,v in stress.items()],
      r'Post-observation interval alarm rates (percent) and 95\% world-bootstrap intervals for Full. The none row measures false alarms. Endpoint bootstrap intervals can degenerate with 24 worlds.','stress')
table('stress_magnitude',['Truth rule','Activity 1','Activity 2','Activity 3'],
      [[n]+[ci(v['truth_shift_rmse'],e) for e in range(3)] for n,v in stress.items()],
      r'True trajectory displacement relative to the no-shift world, RMSE $\times10^3$. Reported separately to distinguish weak perturbations from insensitive detection.','stress_magnitude')
table('timing',['Prior','Cov. (ms)','Enum. (ms)','Median ratio','Max. difference'],
      [[n.replace('_',' '),f"{np.median([r['covariance_ms'] for r in v['raw']]):.3f}",
        f"{np.median([r['enumeration_ms'] for r in v['raw']]):.2f}",f"{v['median_speedup']:.2f}",
        f"{v['max_abs_difference']:.2e}"] for n,v in S['timing'].items()],
      'Ten synchronized, alternating-order GPU timing pairs. Median ratios are computed per pair; they need not equal the ratio of marginal medians.','timing')
table('uncertainty',['Quantity','Activity 1','Activity 2','Activity 3'],
      [[name]+[ci(summary['Covariance'][key],e,scale,precision) for e in range(3)] for key,name,scale,precision in
       [('coverage90','Coverage (percent)',100,1),('width90','Interval width (fraction)',1,4),
        ('epistemic','Epistemic variance x 1e8',1e8,2),('aleatoric','Aleatoric variance x 1e4',1e4,2)]],
      r'Final-budget uncertainty: means and 95\% world-bootstrap intervals. Coverage concerns pointwise 90\% predictive intervals.','uncertainty')
table('golden',['Method','Pooled AUC','Brier','NLL','Coverage','Width'],
      [[label(n),f"{np.mean([r['auc_error'] for r in G['strategies'] if r['strategy']==n]):.6f}"]+
       [f"{np.mean([r['curve'][-1][key] for r in G['strategies'] if r['strategy']==n]):.4f}"
        for key in ['brier','nll','coverage_90','width_90']] for n in original+baseline+['NoSharing','NoCombination','SinglePoint']],
      'Original frozen test cache, descriptive results. Random is averaged over its three query repetitions. These interacting activities do not constitute independent replicates.','golden')

# Entire ledger: preserve failures and tiny improvements, without selection after test.
evol=[r'\begin{longtable}{rrrll}',r'\caption{All 60 audited candidates. Development scores are adaptively selected, not independent validation.}\label{tab:alltrials}\\',
      r'\toprule Round & Dev AUC & Parent AUC & Decision & Commit \\ \midrule\endfirsthead',
      r'\toprule Round & Dev AUC & Parent AUC & Decision & Commit \\ \midrule\endhead']
for r in A['rows']:
    evol.append(f"{r['round']} & {r['dev_auc']:.8f} & {r['parent_auc']:.8f} & {r['decision']} & "+r'\texttt{'+r['commit'][:7]+r'} \\')
write('tables/evolution_all.tex','\n'.join(evol+[r'\bottomrule',r'\end{longtable}','']))

last=G['strategies'][0]['curve'][-1]
numbers={'DevReduction':100*C['relative_dev_reduction'],'InitialDev':C['baseline_dev_auc'],
         'FinalDev':C['best_dev_auc'],'TestAUC':G['auc_error'],'FrozenSpeed':S['timing']['frozen']['median_speedup'],
         'UniformSpeed':S['timing']['uniform_compatible']['median_speedup'],'ESS':C['diagnostics']['training_effective_mechanisms'],
         'MaxWeight':C['diagnostics']['training_largest_weight'],'MacroFull':summary['Covariance']['macro_auc']['mean'],
         'MacroRandom':summary['SamePrior_Random']['macro_auc']['mean'],'MacroMAP':summary['MatchedMAP']['macro_auc']['mean'],
         'DevBrierStart':C['process_warning']['baseline_dev_brier'],'DevBrierEnd':C['process_warning']['best_dev_brier'],
         'TestBrier':last['brier'],'TestCoverage':100*last['coverage_90'],'TestWidth':last['width_90'],
         'TestRuntime':G['runtime_s'],'TestVRAM':G['peak_vram_mb'],
         'HistoryPair':G['score_comparison']['historical_pair_rmse'],'ProbePair':G['score_comparison']['probe_pair_rmse']}
macros=[]
for key,val in numbers.items():
    digits=2 if key in ['DevReduction','FrozenSpeed','UniformSpeed','TestCoverage','TestRuntime','TestVRAM'] else 6
    macros.append('\\newcommand{\\'+key+'}{'+f'{val:.{digits}f}'+'}')
write('tables/numbers.tex','\n'.join(macros)+'\n')
write('numbers.json',json.dumps(numbers,indent=2)+'\n')

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,
                     'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
colors=['#0072B2','#E69F00','#009E73','#CC79A7','#D55E00']
fig,axes=plt.subplots(2,3,figsize=(7.0,4.0),layout='constrained')
for row,names in enumerate([original,matched]):
    for e in range(3):
        ax=axes[row,e]
        for j,n in enumerate(names):
            stat=summary[n]['event_rmse_curve']; y=np.asarray(stat['mean'])[:,e]
            ax.plot(S['budgets'],y*1000,color=colors[j],label=label(n),ls=['-','--','-.',':','-'][j],lw=1.3)
            if row==0:
                ax.fill_between(S['budgets'],np.asarray(stat['ci95_low'])[:,e]*1000,np.asarray(stat['ci95_high'])[:,e]*1000,color=colors[j],alpha=.08)
        ax.set_title(f'Activity {e+1}'+(' / matched prior' if row else ' / original prior'))
        ax.set_xlabel('Evidence budget');ax.grid(alpha=.12)
        if e==0:ax.set_ylabel('RMSE x 1000')
        if row==1: ax.ticklabel_format(axis='y',style='plain',useOffset=False)
axes[0,0].legend(fontsize=6,frameon=False,ncol=2)
fig.savefig(path('paper/figures/budget_curves.pdf'));plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(7.0,2.5),layout='constrained')
for decision,color,marker in [('REVERT','#999999','x'),('KEEP','#0072B2','o')]:
    rows=[r for r in A['rows'] if r['decision']==decision]
    axes[0].scatter([r['round'] for r in rows],[r['dev_auc'] for r in rows],s=19,color=color,marker=marker,label=decision)
best=C['baseline_dev_auc'];ys=[best]
for r in A['rows']:
    if r['decision']=='KEEP':best=r['dev_auc']
    ys.append(best)
axes[0].step(range(61),ys,where='post',lw=1,color='#0072B2')
axes[0].set(xlabel='Development trial',ylabel='Development AUC');axes[0].legend(frameon=False,fontsize=7)
for j,(name,v) in enumerate(S['timing'].items()):
    for k,(key,color) in enumerate([('covariance_ms','#0072B2'),('enumeration_ms','#D55E00')]):
        y=[r[key] for r in v['raw']]
        axes[1].scatter(np.full(len(y),j)+(k-.5)*.22,y,color=color,s=13,label=key.replace('_ms','') if j==0 else None)
axes[1].set(yscale='log',ylabel='Synchronized time (ms)',xticks=[0,1],xticklabels=['Frozen prior','Uniform compatible'])
axes[1].legend(frameon=False,fontsize=7)
fig.savefig(path('paper/figures/evolution_timing.pdf'));plt.close(fig)

fig,ax=plt.subplots(figsize=(5.4,2.4),layout='constrained')
matrix=np.array([v['interval_alarm']['mean'] for v in stress.values()])*100
im=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=100,aspect='auto')
ax.set(xticks=range(3),xticklabels=['Activity 1','Activity 2','Activity 3'],yticks=range(len(stress)),yticklabels=list(stress))
for i in range(matrix.shape[0]):
    for j in range(3):ax.text(j,i,f'{matrix[i,j]:.1f}%',ha='center',va='center',color='white' if matrix[i,j]>60 else 'black')
fig.colorbar(im,ax=ax,label='Alarm rate (%)')
fig.savefig(path('paper/figures/stress_alarms.pdf'));plt.close(fig)

# Inventory every root result; historical runs are documented, never silently pooled.
inventory=[]
campaign_ids={r['run_id'] for r in A['rows']}
for p in sorted(path('results').glob('*.json')):
    rel=p.relative_to(path('')).as_posix()
    try:
        obj=json.loads(p.read_text(encoding='utf-8'));rid=obj.get('run_id',p.stem)
        category=('canonical_supplement' if rid==S['run_id'] else 'canonical_frozen_test' if rid==G['run_id']
                  else 'development_trial' if rid in campaign_ids else 'historical_or_reproduction_not_pooled')
        inventory.append({'file':rel,'sha256':digest(rel),'run_id':rid,'category':category,'status':obj.get('status'),'split':obj.get('split'),'mode':obj.get('mode')})
    except (ValueError,UnicodeError) as error:
        inventory.append({'file':rel,'sha256':digest(rel),'category':'unreadable_preserved','error':str(error)})
write('data_inventory.json',json.dumps(inventory,indent=2)+'\n')
manifest={'inputs':{p:digest(p) for p in INPUTS},'method_sha256':digest('method.py'),
          'ledger_sha256':digest('experiments.tsv'),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=path(''),text=True).strip(),
          'canonical_selection':'Previously sealed provenance copies; no selection on test score.',
          'all_result_files':len(inventory),'worlds':S['worlds'],'official_benchmarks':'NOT_EVALUATED',
          'outputs':{p.relative_to(path('')).as_posix():digest(p.relative_to(path(''))) for folder in ['paper/figures','paper/tables'] for p in path(folder).iterdir() if p.is_file()}}
write('artifact_manifest.json',json.dumps(manifest,indent=2)+'\n')
print(f"Generated paper assets; inventoried {len(inventory)} result files; frozen method verified.")
