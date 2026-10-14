"""Frozen Round-2 evaluator: matched priors, updates, pools and world seeds."""
import importlib.util
import json
import subprocess
import time
import uuid
import numpy as np
import torch
from workspace import path,digest,save_json,ROOT
from v2_benchmark import config


def load_v1():
    spec=importlib.util.spec_from_file_location('frozen_v1',path('provenance/v2/v1_snapshot/method.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def verify():
    for manifest in ['data/v2/manifest.json','infrastructure.v2.lock.json']:
        obj=json.loads(path(manifest).read_text())
        for name,expected in obj['files'].items():
            if digest(name)!=expected:raise RuntimeError('Frozen V2 file changed: '+name)


def move(obj,device):
    if isinstance(obj,torch.Tensor):return obj.to(device)
    if isinstance(obj,dict):return {k:move(v,device) for k,v in obj.items()}
    if isinstance(obj,list):return [move(v,device) for v in obj]
    return obj


def ci(values):
    a=np.asarray(values,dtype=float);cfg=config()
    rng=np.random.default_rng(cfg['bootstrap_seed'])
    samples=a[rng.integers(0,len(a),(cfg['bootstrap_repeats'],len(a)))].mean(1)
    return [float(x) for x in np.quantile(samples,[.025,.975])]


def fixed_select(w,p,mask,costs,strategy,generator,tau,z):
    """Independent implementations; all selectors receive identical w0 and tau."""
    branches=[(torch.ones(len(w),device=w.device),w)];selected=[];mask=mask.clone()
    for j in range(2):
        scores=torch.zeros_like(mask,dtype=torch.float32)
        if strategy=='Random':scores=torch.rand(mask.shape,generator=generator,device=w.device)
        else:
            for mass,bw in branches:
                q=(bw@p).clamp(1e-7,1-1e-7)
                h=-q*q.log()-(1-q)*(1-q).log()
                if strategy=='Entropy':s=h
                elif strategy=='ParamIG':
                    s=h-bw@(-p*p.log()-(1-p)*(1-p).log())
                else:
                    c=torch.einsum('mr,wm,md->wrd',p,bw,z)-q[:,:,None]*(bw@z)[:,None,:]
                    s=c.square().mean(-1)/(q*(1-q)).clamp_min(1e-10)
                scores+=mass[:,None]*s/costs
        ix=scores.masked_fill(~mask,-torch.inf).argmax(1);selected.append(ix)
        mask.scatter_(1,ix[:,None],False)
        if j==0:
            expanded=[]
            for mass,bw in branches:
                for likelihood in (p[:,ix].T,1-p[:,ix].T):
                    prob=(bw*likelihood).sum(1);nw=bw*likelihood.pow(1/tau)
                    expanded.append((mass*prob,nw/nw.sum(1,keepdim=True)))
            branches=expanded
    return torch.stack(selected,1)


def update(module,w,p,y,observed):
    if getattr(module,'SUPPORTS_WORLD_BATCH',False):
        return module.posterior_update(w,{'probabilities':p,'labels':y,'observed':observed})
    return torch.stack([module.posterior_update(wi,{'probabilities':pi,'labels':yi,'observed':oi})
                        for wi,pi,yi,oi in zip(w,p,y,observed)])


def run_policy(module,cache,worlds,split,strategy,w0):
    bank=cache['bank'];p=bank['probe']['P_records'];costs=cache['costs'];n=len(worlds)
    w=w0.expand(n,-1).clone();pool=torch.ones(n,p.shape[1],dtype=torch.bool,device=p.device)
    truth=torch.stack([v['trajectory'] for v in worlds]);labels=torch.stack([v['labels'] for v in worlds])
    observed=torch.stack([v['observed'] for v in worlds]);audit=torch.stack([v['audit_labels'] for v in worlds])
    z=bank[split]['Trajectories'].float().mean(1);flat=z.flatten(1)
    tau=getattr(module,'V2_CONFIG',{}).get('update_temperature',1.)
    g=torch.Generator(device=p.device).manual_seed(92831)
    curve=[];briers=[];weights=[];budgets=cache['budgets'];chosen=[]
    for b in range(0,17,2):
        if b in budgets:
            pred=(w@flat).reshape(n,*z.shape[1:])
            curve.append((pred-truth).square().mean((2,3)).sqrt()) # W,E; activitywise
            q=w@bank[split]['P_records']
            briers.append((q[:,None,:]-audit).square().mean((1,2)))
            weights.append(w.clone())
        if b==16:break
        if strategy=='Full':
            if getattr(module,'SUPPORTS_WORLD_BATCH',False):
                ix=module.select_evidence_batch(w,bank['probe'],pool,costs,2,16-b)
            else:
                ix=torch.stack([module.select_evidence_batch(wi,bank['probe'],mi,costs,2,16-b) for wi,mi in zip(w,pool)])
        else:
            zgoal=bank['train']['Trajectories'].float().mean(1).flatten(1)
            ix=fixed_select(w,p,pool,costs,strategy,g,tau,zgoal)
        if ix.shape!=(n,2) or torch.any(ix[:,0]==ix[:,1]) or not pool.gather(1,ix).all():
            raise ValueError('Selector returned duplicate, invalid or previously observed records')
        pool.scatter_(1,ix,False);chosen.append(ix)
        w=update(module,w,p[:,ix].permute(1,0,2),labels.gather(1,ix),observed.gather(1,ix))
        if not torch.isfinite(w).all() or (w<0).any() or not torch.allclose(w.sum(1),torch.ones(n,device=w.device),atol=1e-5):
            raise ValueError('Invalid posterior')
    errors=torch.stack(curve,1);bs=torch.tensor(budgets,device=p.device)
    auc=torch.trapezoid(errors,bs,dim=1)/16
    macro=auc.mean(1);delta=errors[:,0].mean(1)-errors[:,-1].mean(1)
    def vals(x):return x.detach().cpu().tolist()
    activities=[]
    for k in range(z.shape[1]):
        activities.append({'activity':k,'auc':float(auc[:,k].mean()),'auc_ci95':ci(vals(auc[:,k])),
                           'b0_error':float(errors[:,0,k].mean()),'b16_error':float(errors[:,-1,k].mean()),
                           'b0_b16_difference_ci95':ci(vals(errors[:,0,k]-errors[:,-1,k]))})
    return {'auc':float(macro.mean()),'auc_ci95':ci(vals(macro)),
            'world_auc':vals(macro),'event_world_auc':vals(auc),'event_world_curves':vals(errors),
            'b0_error':float(errors[:,0].mean()),'b16_error':float(errors[:,-1].mean()),
            'b0_b16_difference_ci95':ci(vals(delta)),
            'initial_brier':float(briers[0].mean()),'final_brier':float(briers[-1].mean()),
            'activity_results':activities,'selected_indices':vals(torch.stack(chosen,1)),
            'final_weights':vals(weights[-1])}


def guards(result):
    g=config()['guards'];s=result['strategies'];full=s['Full']
    return {'ess':result['initial_ess']>=g['initial_ess_min'],
            'initial_brier':full['initial_brier']<=g['initial_brier_max'],
            'final_brier':full['final_brier']<=g['final_brier_max'],
            'b16_significant':full['b0_b16_difference_ci95'][0]>0,
            'random_gain':full['auc']<.95*s['Random']['auc'],
            'entropy_gain':full['auc']<.95*s['Entropy']['auc'],
            'runtime':result['runtime_s']<=g['runtime_s_max']}


def main(args,start):
    import method
    verify();torch.set_num_threads(4)
    device='cuda' if args.device!='cpu' and torch.cuda.is_available() else 'cpu'
    module=load_v1() if args.method_version=='v1' else method
    method_path='provenance/v2/v1_snapshot/method.py' if args.method_version=='v1' else 'method.py'
    mh=digest(method_path)
    if args.split=='test':
        frozen=json.loads(path('provenance/v2/frozen.json').read_text())
        if args.method_version!='v1' and mh!=frozen['method_sha256']:raise RuntimeError('Test requires the frozen winner')
    cache=move(torch.load(path('data/v2/rollout_cache.pt'),weights_only=True),device)
    worlds=move(torch.load(path('data/v2/'+args.split+'_truth.pt'),weights_only=True),device)
    strategies=['Full','Random','Entropy']
    if args.mode=='full_paper_ablation':strategies+=['ParamIG','Standard_OED']
    with torch.inference_mode():
        state=module.construct_compatible_set(cache['bank']['train']);w0=state['weights']
        if not torch.isfinite(w0).all() or (w0<0).any() or abs(float(w0.sum())-1)>1e-5:raise ValueError('Invalid initial weights')
        results={name:run_policy(module,cache,worlds,args.split,name,w0) for name in strategies}
    if device=='cuda':torch.cuda.synchronize()
    verify()
    if mh!=digest(method_path):raise RuntimeError('Method changed during evaluation')
    result={'schema':'v2-evaluation','split':args.split,'mode':args.mode,'method_version':args.method_version,
            'method_sha256':mh,'config':getattr(module,'V2_CONFIG',None),
            'initial_ess':float(w0.square().sum().reciprocal()),'max_initial_weight':float(w0.max()),
            'initial_weights':w0.cpu().tolist(),'strategies':results,
            'auc_error':results['Full']['auc'],'runtime_s':time.perf_counter()-start,
            'n_worlds':len(worlds),'device':device,'status':'tested_synthetic_only',
            'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
    result['guards']=guards(result);result['eligible']=all(result['guards'].values())
    result['gains']={k:1-results['Full']['auc']/results[k]['auc'] for k in ['Random','Entropy']}
    output='results/v2/'+args.split+'-'+args.method_version+'-'+uuid.uuid4().hex[:12]+'.json'
    path('results/v2').mkdir(exist_ok=True);save_json(output,result)
    print('RESULT | '+output)
    print('GUARDS | '+json.dumps(result['guards'])+' | ess: '+str(result['initial_ess'])+' | gains: '+json.dumps(result['gains']))
    print(f"METRIC | {args.split}_auc_error: {result['auc_error']:.8f} | brier: {results['Full']['final_brier']:.6f} | runtime_s: {result['runtime_s']:.2f}")
    return result
