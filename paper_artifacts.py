"""Fixed synthetic-paper exports. Tables report measured values, never placeholders."""
import argparse
import json
from workspace import path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--result',help='A results/*.json from full_paper_ablation')
    args=parser.parse_args()
    registry=pd.read_csv(path('experiments.tsv'),sep='\t')
    valid=registry[(registry['mode']=='full_paper_ablation') & (registry['status']!='crash')]
    if args.result:
        source=args.result
        if source not in set(registry['result']):raise ValueError('Result not registered')
    elif len(valid):source=valid.iloc[-1]['result']
    else:raise ValueError('Run evaluate.py --mode full_paper_ablation first')
    result=json.loads(path(source).read_text(encoding='utf-8'))
    if result['mode']!='full_paper_ablation':raise ValueError('Full suite required; do not fabricate missing rows')
    out=path('paper/'+result['run_id']);out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for run in result['strategies']:
        rows.append({'Method':run['strategy'],'AUC':run['auc_error'],'RMSE':run['final']['rmse'],
                     'Brier':run['final']['brier'],'NLL':run['final']['nll'],
                     'Coverage':run['final']['coverage_90'],'Width':run['final']['width_90'],
                     'EpiVar':run['final']['epistemic_variance'],'AleaVar':run['final']['aleatoric_variance'],
                     'ShiftRMSE':run['final']['shifted_rmse'],
                     'BoundaryFlag':int(run['final']['low_disagreement_wrong_flag'])})
    frame=pd.DataFrame(rows)
    mean=frame.groupby('Method',sort=False).mean(numeric_only=True).reset_index()
    cmp=result['score_comparison']
    def table(name,df,caption):
        content='% Synthetic example only; no external benchmark validation.\n'
        content+=df.to_latex(index=False,escape=True,float_format='%.4f',caption=caption,
                            label='tab:'+name,position='t',na_rep='--')
        content=content.replace('\\begin{table}', '\\begin{table*}').replace('\\end{table}', '\\end{table*}')
        content=content.replace('\\centering', '\\centering\n\\small\n\\setlength{\\tabcolsep}{3pt}')
        (out/(name+'.tex')).write_text(content,encoding='utf-8')
    table('experiment1',mean[['Method','RMSE','ShiftRMSE','EpiVar','BoundaryFlag']],
          'Mechanism ambiguity and post-observation misspecification diagnostic (synthetic). '
          f"Training-compatible pair: historical RMSE {cmp['historical_pair_rmse']:.4f}, "
          f"probe RMSE {cmp['probe_pair_rmse']:.4f}. Flags use predeclared thresholds; a zero is not proof of adequacy.")
    comparison=mean[['Method','AUC','Brier','NLL','Coverage','Width']].copy()
    comparison['Cov ms']=float('nan');comparison['Enum ms']=float('nan')
    comparison.loc[comparison.Method=='Covariance',['Cov ms','Enum ms']]=[cmp['covariance_ms'],cmp['enumeration_ms']]
    table('experiment2',comparison,'Budget-error comparison; timing measured for covariance and explicit enumeration.')
    table('experiment3',mean[mean.Method.isin(['Covariance','NoSharing','NoCombination','SinglePoint','PassiveV1'])]
          [['Method','AUC','RMSE','Coverage','Width','EpiVar','AleaVar']],
          'Held-out composition prediction and ablations (synthetic; unsharing also changes the prior).')
    plt.rcParams.update({'font.family':'serif','font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                         'pdf.fonttype':42,'ps.fonttype':42})
    fig,ax=plt.subplots(figsize=(3.25,2.35),layout='constrained')
    for name in ['Covariance','Random','Entropy','ParamIG','Standard_OED','PassiveV1']:
        runs=[r for r in result['strategies'] if r['strategy']==name]
        values=pd.DataFrame([[p['rmse'] for p in r['curve']] for r in runs])
        x=[p['budget'] for p in runs[0]['curve']]
        ax.plot(x,values.mean(),marker='o',markersize=2,label=name)
        if len(runs)>1:
            ax.fill_between(x,values.mean()-values.std(),values.mean()+values.std(),alpha=.12)
    ax.set(xlabel='Evidence cost',ylabel='Trajectory RMSE (fraction)')
    ax.legend(fontsize=6,ncol=2,frameon=False)
    fig.savefig(out/'budget_error.pdf');fig.savefig(out/'budget_error.png',dpi=220);plt.close(fig)
    (out/'provenance.json').write_text(json.dumps({'result':source,'run_id':result['run_id'],
         'cache_sha256':result['cache_sha256'],'method_sha256':result['method_sha256'],
         'score_comparison':cmp,'warning':'One constructed world; repeated Random acquisition seeds are not independent datasets.'},indent=2),encoding='utf-8')
    print(out)


if __name__=='__main__':main()
