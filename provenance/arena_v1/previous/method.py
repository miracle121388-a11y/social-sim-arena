"""Standard V0: ESS-constrained calibration and correlated-evidence acquisition.
No simulator calls, disk reads, target labels, or hidden evaluation access.
"""
import torch

CALIBRATION_SIGMA=.015
PROCESS_WEIGHT=1.
MIN_ESS=15.
LATE_WEIGHT=2.

def construct_compatible_set(train_cache):
    samples=train_cache['Trajectories'].float();z=samples.mean(1)
    residual=(z-train_cache['observed_trajectory']).square()
    error=residual.mean((1,2,3)).sqrt()
    mask=train_cache['history_observed'].bool();p=train_cache['P_history'][:,mask].clamp(1e-6,1-1e-6)
    y=train_cache['history_labels'][mask]
    pe=(p-y).square().mean(1) if mask.any() else torch.zeros_like(error)
    nll=-(y*p.log()+(1-y)*(1-p).log()).mean(1) if mask.any() else torch.zeros_like(error)
    keep=(error<=error.min()+.012)&(pe<=pe.min()+.01)
    if int(keep.sum())<MIN_ESS:raise ValueError('Insufficient compatible support for ESS>=15')
    variance=samples.var(1,unbiased=False).mean(0)
    relative=(variance+1e-5)/(variance.mean()+1e-5)
    energy=(residual/relative).mean((1,2,3))/(2*CALIBRATION_SIGMA**2)+PROCESS_WEIGHT*nll
    def weights(temp):return torch.softmax((-energy/temp).masked_fill(~keep,-torch.inf),0)
    lo,hi=1.,1.
    while float(1/weights(hi).square().sum())<MIN_ESS-1e-5:
        hi*=2
        if hi>1e9:raise ValueError('Unable to meet ESS floor')
    if hi>1:
        for _ in range(25):
            mid=(lo+hi)/2
            if float(1/weights(mid).square().sum())<MIN_ESS:lo=mid
            else:hi=mid
    return {'weights':weights(hi),'mask':keep,'temperature':hi,
            'trajectory_error':error,'process_error':pe}

def initial_episode_state(worlds,groups,device):
    return {'log_l0':torch.zeros(worlds,groups,device=device),
            'log_l1':torch.zeros(worlds,groups,device=device)}

def conditional_probabilities(group_probabilities,pool,state):
    pg=group_probabilities.clamp(1e-6,1-1e-6)
    latent=torch.sigmoid(torch.logit(pg)[None,:,:]+(state['log_l1']-state['log_l0'])[:,None,:])
    r=pool['reliability']
    return (1-r)[None,None,:]+(2*r-1)[None,None,:]*latent[:,:,pool['group']]

def update_one(weights,state,group_probabilities,pool,index,answer,observed):
    """Exact marginalization of shared episodes; repeated sensors are NOT iid."""
    valid=(index>=0)&observed;ix=index.clamp_min(0);world=torch.arange(len(weights),device=weights.device)
    p=conditional_probabilities(group_probabilities,pool,state)[world,:,ix].clamp(1e-7,1-1e-7)
    likelihood=torch.where(answer[:,None]>.5,p,1-p)
    ll=torch.where(valid[:,None],likelihood.log(),torch.zeros_like(likelihood))
    logw=torch.where(weights>0,weights.log(),-torch.inf)
    posterior=torch.softmax(logw+ll,1)
    group=pool['group'][ix];r=pool['reliability'][ix]
    l1=torch.where(answer>.5,r,1-r).log()*valid;l0=torch.where(answer>.5,1-r,r).log()*valid
    new={'log_l0':state['log_l0'].clone(),'log_l1':state['log_l1'].clone()}
    new['log_l0'].scatter_add_(1,group[:,None],l0[:,None])
    new['log_l1'].scatter_add_(1,group[:,None],l1[:,None])
    return posterior,new

def covariance_scores(weights,probabilities,trajectories,costs):
    z=trajectories.flatten(1);q=torch.einsum('wm,wmr->wr',weights,probabilities)
    cov=torch.bmm(probabilities.transpose(1,2),weights[:,:,None]*z[None,:,:])-q[:,:,None]*(weights@z)[:,None,:]
    return cov.square().mean(-1)/(q*(1-q)).clamp_min(1e-10)/costs

def select_evidence_batch(candidate_weights,probe_cache,pool_mask,costs,batch_size=2,
                          budget_remaining=None,state=None,pool=None,condition=True,
                          score_function=None,generator=None):
    """Outcome branches include MCAR missing responses; no submodularity claim.
    condition=False freezes acquisition beliefs only, not actual posterior updates.
    The fixed evaluator supplies independent baseline score functions.
    """
    w=candidate_weights;pg=probe_cache['P_groups'];z=probe_cache['Trajectories'].float().mean(1)
    time=torch.linspace(1.,LATE_WEIGHT,z.shape[2],device=w.device)
    z=z*time[None,None,:,None].sqrt()
    mask=pool_mask.clone();remaining=budget_remaining.clone()
    branches=[(torch.ones(len(w),device=w.device),w,state)];selected=[]
    for j in range(batch_size):
        scores=torch.zeros_like(mask,dtype=torch.float32)
        for mass,bw,bs in branches:
            p=conditional_probabilities(pg,pool,bs)
            value=(covariance_scores(bw,p,z,costs) if score_function is None else score_function(bw,p,z,costs))
            scores+=mass[:,None]*value*pool['observed_probability']
        eligible=mask&(costs<=remaining[:,None]+1e-6)
        no_signal=scores.abs().amax(1)<1e-12
        tie=torch.rand(scores.shape,generator=generator,device=w.device)*1e-13
        scores=torch.where(no_signal[:,None],tie,scores)
        ix=scores.masked_fill(~eligible,-torch.inf).argmax(1)
        ix=torch.where(eligible.any(1),ix,torch.full_like(ix,-1));selected.append(ix)
        valid=ix>=0;safe=ix.clamp_min(0);world=torch.arange(len(w),device=w.device)
        mask[world[valid],safe[valid]]=False;remaining-=costs[safe]*valid
        if condition and j+1<batch_size:
            expanded=[]
            for mass,bw,bs in branches:
                p=conditional_probabilities(pg,pool,bs)[world,:,safe]
                q=(bw*p).sum(1);rho=pool['observed_probability'][safe]*valid
                for y,prob in [(0.,1-q),(1.,q)]:
                    nw,ns=update_one(bw,bs,pg,pool,ix,torch.full_like(q,y),valid)
                    expanded.append((mass*rho*prob,nw,ns))
                expanded.append((mass*(1-rho),bw,bs))
            branches=expanded
    return torch.stack(selected,1)

def update_and_predict(candidate_weights,revealed_records,target_cache):
    w=candidate_weights;state=revealed_records['state'];pool=revealed_records['pool']
    for j in range(revealed_records['indices'].shape[1]):
        w,state=update_one(w,state,target_cache['P_groups'],pool,
            revealed_records['indices'][:,j],revealed_records['labels'][:,j],revealed_records['observed'][:,j])
    samples=target_cache['Trajectories'].float();z=samples.mean(1)
    mu=(w@z.flatten(1)).reshape(len(w),*z.shape[1:])
    epistemic=(torch.einsum('wm,metc->wetc',w,z.square())-mu.square()).clamp_min(0)
    aleatoric=torch.einsum('wm,metc->wetc',w,samples.var(1,unbiased=False))
    return {'weights':w,'state':state,'mean':mu,'epistemic':epistemic,'aleatoric':aleatoric}
