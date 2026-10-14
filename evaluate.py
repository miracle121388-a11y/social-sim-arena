"""Fixed V3 evaluator: identical primary priors, monetary budgets, honest ablations."""
import time
START=time.perf_counter()
import argparse
import hashlib
import json
import subprocess
import uuid
import numpy as np
import torch
import method
from prepare_and_cache import config,device_name
from workspace import path,digest,save_json,ROOT

PRIMARY=['Full','Random','Entropy','ParamIG','Standard_OED']
ABLATIONS=['NoBatch','NoProbes','SinglePointMAP','NoSharing']

class PriorCollapseError(ValueError):
    pass

def guard_prior(w):
    if w.ndim!=1 or not torch.isfinite(w).all() or (w<0).any() or abs(float(w.sum())-1)>1e-5:
        raise PriorCollapseError('Invalid initial calibration distribution')
    ess=float(w.square().sum().reciprocal())
    if ess<15.0:raise PriorCollapseError(f'Premature prior collapse: ESS={ess:.8f} < 15')
    return ess

def verify():
    for filename in ['data/v3/manifest.json','infrastructure.v3.lock.json']:
        for name,h in json.loads(path(filename).read_text())['files'].items():
            if digest(name)!=h:raise RuntimeError('Frozen V3 dependency changed: '+name)

def move(obj,device):
    if isinstance(obj,torch.Tensor):return obj.to(device)
    if isinstance(obj,dict):return {k:move(v,device) for k,v in obj.items()}
    if isinstance(obj,list):return [move(v,device) for v in obj]
    return obj

def ci(x):
    x=np.asarray(x,dtype=float);cfg=config()
    rng=np.random.default_rng(cfg['bootstrap_seed'])
    indices=rng.integers(0,len(x),(cfg['bootstrap_repeats'],len(x)))
    return np.quantile(x[indices].mean(1),[.025,.975]).tolist()

def prior_hash(w):
    return hashlib.sha256(w.detach().cpu().contiguous().numpy().tobytes()).hexdigest()

def scorer(name,history,generator):
    def score(w,p,z,costs):
        q=torch.einsum('wm,wmr->wr',w,p).clamp(1e-7,1-1e-7)
        if name=='Random':return torch.rand(q.shape,device=w.device,generator=generator)
        entropy=-q*q.log()-(1-q)*(1-q).log()
        if name=='Entropy':return entropy/costs
        if name=='ParamIG':
            pc=p.clamp(1e-7,1-1e-7)
            conditional=-pc*pc.log()-(1-pc)*(1-pc).log()
            return (entropy-torch.einsum('wm,wmr->wr',w,conditional)).clamp_min(0)/costs
        # Independent outcome enumeration of historical predictive mean shifts.
        hz=history.flatten(1);mu=w@hz
        numerator=torch.bmm((w[:,:,None]*p).transpose(1,2),hz[None,:,:].expand(len(w),-1,-1))
        mu1=numerator/q[:,:,None]
        mu0=(mu[:,None,:]-numerator)/(1-q)[:,:,None]
        value=q*((mu1-mu[:,None,:]).square().mean(-1))+(1-q)*((mu0-mu[:,None,:]).square().mean(-1))
        return value/costs
    return score

def run_policy(name,w0,cache,worlds,split):
    pool=cache['pool'];costs=pool['costs'];n=len(worlds);bank=cache['shared']
    prior=w0.clone();shared_hash=prior_hash(w0);extra={}
    if name=='NoSharing':
        bank=cache['unshared'];indices=bank['indices']
        # Factorized activity priors on a finite stratified joint particle bank.
        prior=w0[indices].prod(1);prior=prior/prior.sum()
        marginals=torch.zeros(3,len(w0),device=w0.device)
        for e in range(3):marginals[e].scatter_add_(0,indices[:,e],prior)
        extra={'prior_dependence':'independent activity parameters; importance-weighted joint particle approximation',
               'initial_marginals':marginals.cpu().tolist(),
               'marginal_total_variation':(.5*(marginals-w0).abs().sum(1)).cpu().tolist()}
        guard_prior(prior)
    elif name=='SinglePointMAP':
        prior=torch.zeros_like(w0);prior[w0.argmax()]=1.
        extra={'diagnostic_only':True,'prior_guard_exception':'evaluator-created MAP after full prior passed'}
    if name in PRIMARY:assert torch.equal(prior,w0)
    w=prior.expand(n,-1).clone();state=method.initial_episode_state(n,bank['P_groups'].shape[1],w.device)
    mask=torch.ones(n,len(costs),dtype=torch.bool,device=w.device);spent=torch.zeros(n,device=w.device)
    truth=torch.stack([x['trajectory'] for x in worlds]);labels=torch.stack([x['labels'] for x in worlds])
    observed=torch.stack([x['observed'] for x in worlds]);audit=torch.stack([x['audit_labels'] for x in worlds])
    target=bank[split]['Trajectories'].float();z=target.mean(1);flat=z.flatten(1)
    probe={**bank['probe'],'P_groups':bank['P_groups']}
    if name=='NoProbes':probe={**cache['shared']['train'],'P_groups':bank['P_groups']}
    rng=torch.Generator(device=w.device).manual_seed(19913)
    score_fn=scorer(name,cache['shared']['train']['Trajectories'].float().mean(1),rng) if name in PRIMARY[1:] else None
    curve=[];briers=[];expenditures=[];traces=[];redundancy=[];epistemic=[];aleatoric=[]
    for budget in cache['budgets']:
        if name!='SinglePointMAP':
            steps=0
            while ((mask&(costs<=budget-spent[:,None]+1e-6)).any()):
                steps+=1
                if steps>64:raise RuntimeError('Acquisition failed to make progress')
                ix=method.select_evidence_batch(w,probe,mask,costs,2,budget-spent,state,pool,
                      condition=name not in ['NoBatch','Random'],score_function=score_fn,generator=rng)
                if ix.shape!=(n,2) or (ix>=len(costs)).any() or (ix<-1).any():raise ValueError('Invalid query indices')
                world=torch.arange(n,device=w.device)
                batch_cost=torch.zeros(n,device=w.device)
                for j in range(2):
                    valid=ix[:,j]>=0;safe=ix[:,j].clamp_min(0)
                    if not mask[world[valid],safe[valid]].all():raise ValueError('Repeated record index')
                    mask[world[valid],safe[valid]]=False;batch_cost+=costs[safe]*valid
                if (spent+batch_cost>budget+1e-6).any():raise ValueError('Evidence budget overspent')
                if not (batch_cost>0).any():raise RuntimeError('No feasible query returned')
                spent+=batch_cost
                groups=pool['group'][ix.clamp_min(0)]
                redundancy.append(((groups[:,0]==groups[:,1])&(ix>=0).all(1)).float())
                traces.append({'checkpoint':budget,'indices':ix.cpu().tolist(),'cost':batch_cost.cpu().tolist()})
                for j in range(2):
                    safe=ix[:,j].clamp_min(0)
                    w,state=method.update_one(w,state,bank['P_groups'],pool,ix[:,j],
                                             labels[world,safe],observed[world,safe]&(ix[:,j]>=0))
                if not torch.isfinite(w).all() or (w<0).any() or not torch.allclose(w.sum(1),torch.ones(n,device=w.device),atol=1e-5):
                    raise ValueError('Invalid posterior')
        mean=(w@flat).reshape(n,*z.shape[1:])
        curve.append((mean-truth).square().mean((2,3)).sqrt())
        q=w@bank['P_records'];briers.append((q[:,None,:]-audit).square().mean((1,2)))
        expenditures.append(spent.clone())
        epistemic.append(((w@flat.square())-(w@flat).square()).clamp_min(0).mean(1))
        aleatoric.append((w@target.var(1,unbiased=False).flatten(1)).mean(1))
    errors=torch.stack(curve,1);budgets=torch.tensor(cache['budgets'],device=w.device)
    auc=torch.trapezoid(errors,budgets,dim=1)/16;macro=auc.mean(1)
    vals=lambda x:x.detach().cpu().tolist()
    events=[]
    for e in range(z.shape[1]):
        events.append({'activity':e,'auc':float(auc[:,e].mean()),'auc_ci95':ci(vals(auc[:,e])),
                       'b0_b16_difference_ci95':ci(vals(errors[:,0,e]-errors[:,-1,e]))})
    return {'auc':float(macro.mean()),'auc_ci95':ci(vals(macro)),'world_auc':vals(macro),
            'event_world_auc':vals(auc),'event_world_errors':vals(errors),
            'macro_curve':vals(errors.mean((0,2))),'brier_curve':vals(torch.stack(briers,1).mean(0)),
            'spent':vals(torch.stack(expenditures,1)),'query_trace':traces,
            'same_episode_batch_fraction':float(torch.stack(redundancy).mean()) if redundancy else 0.,
            'initial_ess':float(prior.square().sum().reciprocal()),'initial_prior_hash':prior_hash(prior),
            'shared_reference_prior_hash':shared_hash,'initial_weights':vals(prior),'final_weights':vals(w),
            'b0_b16_difference_ci95':ci(vals(errors[:,0].mean(1)-errors[:,-1].mean(1))),
            'epistemic_curve':vals(torch.stack(epistemic,1).mean(0)),
            'aleatoric_curve':vals(torch.stack(aleatoric,1).mean(0)),'activities':events,**extra}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--split',choices=['dev','test'],default='dev')
    parser.add_argument('--mode',choices=['fast_dev','full_paper_ablation'],default='fast_dev')
    parser.add_argument('--device',choices=['auto','cpu','cuda'],default='auto')
    args=parser.parse_args();verify();mh=digest('method.py')
    if args.split=='test':
        seal=path('provenance/v3/test_release.json')
        if not seal.exists():raise RuntimeError('V3 test remains sealed; an explicitly authorized final-test release is required')
        if json.loads(seal.read_text())['method_sha256']!=mh:raise RuntimeError('Test method is not the sealed method')
    torch.set_num_threads(4);device=device_name(args.device)
    cache=move(torch.load(path('data/rollout_cache.pt'),weights_only=True),device)
    # Guard before opening any target outcomes.
    with torch.inference_mode():
        try:
            calibration=method.construct_compatible_set(cache['train']);w0=calibration['weights'];ess=guard_prior(w0)
        except (PriorCollapseError,ValueError) as exc:
            result={'status':'invalid_prior','auc_error':999.,'reason':str(exc),'method_sha256':mh,
                    'split':args.split,'runtime_s':time.perf_counter()-START}
            filename='results/v3/invalid-'+uuid.uuid4().hex[:12]+'.json'
            path('results/v3').mkdir(exist_ok=True);save_json(filename,result)
            print('RESULT | '+filename);print(f'METRIC | {args.split}_auc_error: 999.0000 | invalid_prior: {exc}')
            return result
        worlds=move(torch.load(path('data/v3/'+args.split+'_truth.pt'),weights_only=True),device)
        names=PRIMARY+(ABLATIONS if args.mode=='full_paper_ablation' else [])
        policies={name:run_policy(name,w0,cache,worlds,args.split) for name in names}
    assert len({policies[n]['initial_prior_hash'] for n in PRIMARY})==1
    full=policies['Full'];paired={}
    for name,value in policies.items():
        difference=np.asarray(value['world_auc'])-np.asarray(full['world_auc'])
        paired[name]={'mean_auc_difference':float(difference.mean()),'ci95':ci(difference),
                      'relative_full_gain':1-full['auc']/value['auc']}
    if device=='cuda':torch.cuda.synchronize()
    verify()
    if digest('method.py')!=mh:raise RuntimeError('Method changed during evaluation')
    result={'schema':'standard-v3-v0','status':'tested_synthetic','split':args.split,'mode':args.mode,
            'method_sha256':mh,'cache_sha256':digest('data/rollout_cache.pt'),
            'initial_ess':ess,'compatible_support':int(calibration['mask'].sum()),'auc_error':full['auc'],
            'runtime_s':time.perf_counter()-START,'device':device,'strategies':policies,'paired_vs_full':paired,
            'test_status':'sealed' if args.split=='dev' else 'released',
            'uncertainty_unit':'independent whole worlds; activities inside a world are dependent',
            'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
    filename='results/v3/'+args.split+'-'+args.mode+'-'+uuid.uuid4().hex[:12]+'.json'
    path('results/v3').mkdir(exist_ok=True);save_json(filename,result)
    print('RESULT | '+filename)
    print('CURVE | '+json.dumps(full['macro_curve'])+' | ESS: '+str(ess))
    for name,s in policies.items():print(f"{name}: AUC={s['auc']:.6f}, same-episode batch={s['same_episode_batch_fraction']:.3f}")
    print(f"METRIC | {args.split}_auc_error: {full['auc']:.6f} | brier: {full['brier_curve'][-1]:.6f} | initial_ess: {ess:.4f} | runtime_s: {result['runtime_s']:.2f}")
    return result

if __name__=='__main__':main()
