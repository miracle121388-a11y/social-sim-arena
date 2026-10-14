"""Fixed evaluator. Development selection only; test requires a frozen method."""
import time
START = time.perf_counter()
import argparse
import csv
from datetime import datetime, timezone
import json
import subprocess
import traceback
import uuid
from workspace import path, digest, save_json, ROOT
import torch
import method
from prepare_and_cache import device_name

FIXED_FILES = ['prepare_and_cache.py','evaluate.py','workspace.py','autoresearch.py',
               'paper_artifacts.py','program.md','requirements.txt','requirements.lock.txt',
               'tests/test_science.py','tests/test_git_machine.py']


def verify_integrity():
    manifest=json.loads(path('data/cache_manifest.json').read_text(encoding='utf-8'))
    if digest('data/rollout_cache.pt') != manifest['sha256']:
        raise RuntimeError('Cache integrity check failed')
    if digest('prepare_and_cache.py') != manifest['prepare_sha256']:
        raise RuntimeError('Benchmark generator changed after preparation')
    if path('infrastructure.lock.json').exists():
        for name, expected in json.loads(path('infrastructure.lock.json').read_text()).items():
            if digest(name) != expected:
                raise RuntimeError(f'Fixed infrastructure changed: {name}')
    return manifest


def move(value, device):
    if isinstance(value,torch.Tensor):
        return value.to(device)
    if isinstance(value,dict):
        return {k:move(v,device) for k,v in value.items()}
    return value


def validated_weights(w, m):
    if w.shape != (m,) or not torch.isfinite(w).all() or (w < 0).any() or abs(float(w.sum())-1)>1e-5:
        raise ValueError('Method returned invalid posterior')
    return w


def fixed_compatible(train,mode):
    """Frozen comparator calibration, unaffected by edits to method.py."""
    trajectory=(train['Trajectories'].float().mean(1)-train['observed_trajectory']).square().mean((1,2,3)).sqrt()
    mask=train['history_observed'].bool()
    process=(train['P_history'][:,mask]-train['history_labels'][mask]).square().mean(1)
    pok=process<=process.min()+.045;tok=trajectory<=.10
    keep={'uncalibrated':torch.ones_like(pok),'process':pok,'trajectory':tok,'joint':pok&tok}[mode]
    if not keep.any():raise ValueError('Empty fixed comparator compatible set')
    return {'weights':keep.float()/keep.sum(),'process_error':process,'trajectory_error':trajectory}


def fixed_select(w,query,mask,costs,batch_size,strategy,generator):
    """Frozen baseline acquisition, with the same exact fantasy-branch budget."""
    p=query['P_records'].float();z=query['Trajectories'].float().mean(1).flatten(1)
    branches=[(1.,w)];mask=mask.clone();selected=[]
    for _ in range(batch_size):
        scores=torch.zeros(p.shape[1],device=w.device)
        if strategy=='Random':scores=torch.rand(len(scores),device=w.device,generator=generator)
        else:
            for mass,weights in branches:
                q=(weights@p).clamp(1e-7,1-1e-7)
                entropy=-q*q.log()-(1-q)*(1-q).log()
                if strategy=='Entropy':value=entropy
                elif strategy=='ParamIG':
                    pc=p.clamp(1e-7,1-1e-7)
                    value=entropy-weights@(-pc*pc.log()-(1-pc)*(1-pc).log())
                else:
                    covariance=p.T@(weights[:,None]*(z-weights@z))
                    value=covariance.square().mean(1)/(q*(1-q))
                scores+=mass*value/costs
        index=int(scores.masked_fill(~mask,-torch.inf).argmax());selected.append(index);mask[index]=False
        updated=[]
        for mass,weights in branches:
            for likelihood in (p[:,index],1-p[:,index]):
                q=weights@likelihood
                if q>1e-12:updated.append((mass*q,weights*likelihood/q))
        branches=updated
    return torch.tensor(selected,device=w.device,dtype=torch.long)


def fixed_update(w,reveal):
    p=reveal['probabilities'].clamp(1e-7,1-1e-7)
    loglike=torch.where(reveal['labels'][None,:]>.5,p.log(),(1-p).log())
    loglike=torch.where(reveal['observed'][None,:],loglike,0.)
    logw=torch.where(w>0,w.log(),-torch.inf)
    return torch.softmax(logw+loglike.sum(1),dim=0)


def fixed_prediction(w, target):
    """Evaluator-owned mixture moments/intervals, never trust method's metrics."""
    samples=target['Trajectories'].float()
    means=samples.mean(1)
    mean=(w[:,None,None,None]*means).sum(0)
    epi=(w[:,None,None,None]*(means-mean).square()).sum(0)
    alea=(w[:,None,None,None]*samples.var(1,unbiased=False)).sum(0)
    values,indices=samples.flatten(0,1).sort(0)
    atoms=w.repeat_interleave(samples.shape[1])/samples.shape[1]
    cumulative=atoms[indices].cumsum(0)
    def quantile(q):
        i=(cumulative<q).sum(0).clamp_max(len(values)-1)
        return values.gather(0,i[None]).squeeze(0)
    return {'mean':mean,'epistemic':epi,'aleatoric':alea,'lower':quantile(.05),
            'upper':quantile(.95),'p':w@target['P_records'].float()}


def metrics(w,target,truth):
    pred=fixed_prediction(w,target)
    observed=truth['trajectory'].float()
    err=pred['mean']-observed.mean(0)
    mask=truth['observed'].bool()
    y=truth['labels'][mask]
    p=pred['p'][mask].clamp(1e-7,1-1e-7)
    interval=(observed>=pred['lower']) & (observed<=pred['upper'])
    shifted=truth['shifted_trajectory'].float().mean(0)
    shifted_rmse=(pred['mean']-shifted).square().mean().sqrt()
    epi=pred['epistemic'].mean()
    return {'rmse':float(err.square().mean().sqrt()),'mae':float(err.abs().mean()),
            'rmse_per_event':err.square().mean((1,2)).sqrt().tolist(),
            'rmse_per_time_channel':err.square().mean(0).sqrt().tolist(),
            'nll':float(-(y*p.log()+(1-y)*(1-p).log()).mean()),
            'brier':float((p-y).square().mean()),'coverage_90':float(interval.float().mean()),
            'width_90':float((pred['upper']-pred['lower']).mean()),
            'epistemic_variance':float(epi),'aleatoric_variance':float(pred['aleatoric'].mean()),
            'shifted_rmse':float(shifted_rmse),
            # Diagnostic after observations, not an omniscient pre-event detector.
            'low_disagreement_wrong_flag':bool((epi<.0025)&(shifted_rmse>.08))}


def run_strategy(cache,split,name,repeat=0):
    bank=cache['banks']['unshared' if name=='NoSharing' else 'shared']
    train=bank['train']; target=bank[split]
    cal_mode={'Uncalibrated':'uncalibrated','ProcessOnly':'process','TrajectoryOnly':'trajectory'}.get(name,'joint')
    fixed=name in ('Random','Entropy','ParamIG','Standard_OED','SimpleStats','Uncalibrated',
                   'ProcessOnly','TrajectoryOnly','PassiveV1')
    initial=fixed_compatible(train,cal_mode) if fixed else method.construct_compatible_set(train,mode=cal_mode)
    w=validated_weights(initial['weights'],len(train['Trajectories']))
    compatible=int((w>0).sum())
    if name=='SinglePoint':
        objective=initial['process_error']+initial['trajectory_error']
        idx=objective.masked_fill(w==0,torch.inf).argmin()
        w=torch.nn.functional.one_hot(idx,len(w)).float()
    if name=='SimpleStats':
        # Empirical historical-event paths as bootstrap atoms. No candidate fit.
        samples=train['observed_trajectory'].float()[None,:,None,:,:].expand(1,-1,len(target['events']),-1,-1)
        labels=train['history_labels'][train['history_observed']]
        target={'Trajectories':samples,'P_records':torch.full((1,160),float(labels.mean()),device=w.device)}
        w=torch.ones(1,device=w.device)
    # Availability is public acquisition metadata, not a label. Restrict queries
    # to retrievable records so binary-outcome fantasy updates match the oracle.
    # Missing historical/held-out records remain missing, never negative labels.
    mask=cache['truth']['acquisition']['observed'].bool().clone()
    query={'P_records':train['P_records'],
           'Trajectories':bank['train' if name in ('Standard_OED','NoCombination') else 'probe']['Trajectories']}
    curves=[]; queries=[]; spent=0
    passive=name in ('SimpleStats','Uncalibrated','ProcessOnly','TrajectoryOnly','PassiveV1')
    generator=torch.Generator(device=w.device).manual_seed(600+repeat)
    for budget in cache['budgets']:
        while spent < budget and not passive:
            if fixed:
                batch=fixed_select(w,query,mask,cache['costs'],min(2,budget-spent),name,generator)
            else:
                batch=method.select_evidence_batch(w,query,mask,cache['costs'],
                     batch_size=min(2,budget-spent),budget_remaining=budget-spent,
                     strategy=name if name in ('Random','Entropy','ParamIG') else 'Covariance',generator=generator)
            if batch.numel()==0:
                raise RuntimeError('Acquisition cannot spend declared budget')
            if len(torch.unique(batch)) != len(batch) or not mask[batch].all():
                raise ValueError('Duplicate/reused evidence')
            cost=int(cache['costs'][batch].sum())
            if cost > budget-spent:
                raise ValueError('Evidence budget exceeded')
            reveal={'probabilities':train['P_records'][:,batch],
                    'labels':cache['truth']['acquisition']['labels'][batch],
                    'observed':cache['truth']['acquisition']['observed'][batch]}
            # Only selected labels cross the algorithm boundary. Test labels never do.
            new_w=fixed_update(w,reveal) if fixed else method.update_and_predict(w,reveal,target)['weights']
            w=validated_weights(new_w,len(train['Trajectories']))
            mask[batch]=False; spent+=cost
            queries.append({'budget':spent,'indices':batch.tolist(),'cost':cost,
                            'observed':reveal['observed'].tolist()})
        curves.append({'budget':budget,'spent':spent,**metrics(w,target,cache['truth'][split])})
    x=torch.tensor(cache['budgets'],dtype=torch.float64)
    y=torch.tensor([v['rmse'] for v in curves],dtype=torch.float64)
    auc=float(torch.trapezoid(y,x)/(x[-1]-x[0]))
    return {'strategy':name,'repeat':repeat,'auc_error':auc,'compatible_count':compatible,
            'curve':curves,'queries':queries,'final':curves[-1]}


def score_comparison(cache):
    bank=cache['banks']['shared']; w=method.construct_compatible_set(bank['train'])['weights']
    p=bank['train']['P_records']; z=bank['probe']['Trajectories'].float().mean(1)
    costs=cache['costs']
    def sync():
        if w.is_cuda: torch.cuda.synchronize()
    method.covariance_scores(w,p,z,costs); method.explicit_scores(w,p[:,:2],z,costs[:2]); sync()
    out={}
    for name,fn in [('covariance',method.covariance_scores),('enumeration',method.explicit_scores)]:
        sync(); started=time.perf_counter()
        for _ in range(3): scores=fn(w,p,z,costs)
        sync(); out[name+'_ms']=(time.perf_counter()-started)*1000/3
        out[name+'_scores']=scores
    out['max_abs_difference']=float((out.pop('covariance_scores')-out.pop('enumeration_scores')).abs().max())
    # Select ambiguity pair using historical/probe predictions ONLY.
    keep=w>0
    history=bank['train']['Trajectories'].float().mean(1)[keep].flatten(1)
    probes=z[keep].flatten(1)
    historical=torch.cdist(history,history)/history.shape[1]**.5
    divergence=torch.cdist(probes,probes)/probes.shape[1]**.5
    permitted=(historical<.05)&~torch.eye(len(history),device=w.device,dtype=torch.bool)
    chosen=divergence.masked_fill(~permitted,-1).flatten().argmax()
    i,j=int(chosen)//len(history),int(chosen)%len(history)
    out['ambiguity_pair_found']=bool(permitted.any())
    out['historical_pair_rmse']=float(historical[i,j])
    out['probe_pair_rmse']=float(divergence[i,j])
    out['pair_parameters']=cache['parameters'][keep][[i,j]].tolist()
    return out


def record_tsv(result,status='baseline'):
    p=path('experiments.tsv'); exists=p.exists()
    columns=['run_id','commit','method_sha256','split','mode','auc_error','runtime_s','status','result']
    row={k:result.get(k,'') for k in columns}
    row['status']=status; row['result']='results/'+result['run_id']+'.json'
    with p.open('a',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns,delimiter='\t')
        if not exists:writer.writeheader()
        writer.writerow(row)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--split',choices=['dev','test'],default='dev')
    parser.add_argument('--mode',choices=['fast_dev','full_paper_ablation'],default='fast_dev')
    parser.add_argument('--device',choices=['auto','cpu','cuda'],default='auto')
    args=parser.parse_args()
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    result={'run_id':run_id,'split':args.split,'mode':args.mode,'method_sha256':digest('method.py')}
    try:
        result['commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        manifest=verify_integrity()
        if args.split=='test':
            frozen=json.loads(path('frozen_method.json').read_text())
            if frozen['method_sha256']!=digest('method.py'):
                raise RuntimeError('Test method differs from frozen development winner')
        torch.set_num_threads(4)
        device=device_name(args.device)
        if device=='cuda':torch.cuda.reset_peak_memory_stats()
        start=time.perf_counter()
        cache=move(torch.load(path('data/rollout_cache.pt'),map_location='cpu',weights_only=True),device)
        if device=='cuda':torch.cuda.synchronize()
        result['cache_load_s']=time.perf_counter()-start
        names=['Covariance']
        if args.mode=='full_paper_ablation':
            names+=['Random','Entropy','ParamIG','Standard_OED','SimpleStats','Uncalibrated',
                    'ProcessOnly','TrajectoryOnly','PassiveV1','NoSharing','NoCombination','SinglePoint']
        results=[]
        with torch.inference_mode():
            for name in names:
                for repeat in range(3 if name=='Random' else 1):
                    results.append(run_strategy(cache,args.split,name,repeat))
            if args.mode=='full_paper_ablation':result['score_comparison']=score_comparison(cache)
        if device=='cuda':torch.cuda.synchronize()
        verify_integrity()
        if result['method_sha256']!=digest('method.py'):
            raise RuntimeError('Algorithm changed while evaluation was running')
        result.update({'strategies':results,'auc_error':results[0]['auc_error'],
                       'runtime_s':time.perf_counter()-START,'device':device,
                       'peak_vram_mb':torch.cuda.max_memory_allocated()/1024**2 if device=='cuda' else 0,
                       'cache_sha256':manifest['sha256'],'status':'tested_synthetic',
                       'units':'population fraction; normalized trapezoidal budget AUC',
                       'coverage':'pointwise mixture quantiles over mechanisms and seeds, not simultaneous bands',
                       'nll':'independent audit cohort next decision at standardized known risk states'})
        save_json('results/'+run_id+'.json',result);record_tsv(result)
        print(f"RESULT | results/{run_id}.json | device: {device} | peak_vram_mb: {result['peak_vram_mb']:.1f}")
        final=results[0]['final']
        print(f"METRIC | {args.split}_auc_error: {result['auc_error']:.4f} | brier: {final['brier']:.4f} | coverage_90: {final['coverage_90']:.4f} | width_90: {final['width_90']:.4f} | runtime_s: {result['runtime_s']:.2f}")
    except Exception:
        result.update({'status':'crash','error':traceback.format_exc(),'runtime_s':time.perf_counter()-START})
        save_json('results/'+run_id+'.json',result);record_tsv(result,'crash')
        raise


if __name__=='__main__':main()
