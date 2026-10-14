"""The ONLY evolvable file. Baseline v0; tensor-only mechanism inference.

For binary Y and cached trajectory mean Z, total variance gives
E[Var(Z)-Var(Z|Y)] = ||Cov(Z,p(Y=1|theta))||² / (q*(1-q)).
This is model-internal expected reduction, not guaranteed real-error reduction.
"""
import torch

TRAIN_VARIANCE_FLOOR = 1e-05

FIT_OBJECTIVE = 'worst_event'

TRAJECTORY_SCALE = 0.0007



def _training_distance(trajectories, truth, original_error, train_cache):
    variance = train_cache["Trajectories"].float().var(1, unbiased=False).mean(0)
    relative_variance = (variance + TRAIN_VARIANCE_FLOOR) / (variance.mean() + TRAIN_VARIANCE_FLOOR)
    residual = (trajectories - truth) / relative_variance.sqrt()
    if FIT_OBJECTIVE == 'worst_event':
        return residual.square().mean((2, 3)).amax(1)
    if FIT_OBJECTIVE == 'worst_channel':
        return residual.square().mean((1, 2)).amax(1)
    if FIT_OBJECTIVE == 'absolute':
        return residual.abs().mean((1, 2, 3)).square()
    if FIT_OBJECTIVE == 'huber':
        return 2 * torch.nn.functional.huber_loss(trajectories, truth.expand_as(trajectories), delta=.01, reduction='none').mean((1, 2, 3))
    if FIT_OBJECTIVE == 'trimmed':
        errors = residual.square().flatten(1).sort(1).values
        return errors[:, :int(.9 * errors.shape[1])].mean(1)
    if FIT_OBJECTIVE == 'late':
        return residual[:, :, residual.shape[2]//2:, :].square().mean((1, 2, 3))
    return original_error.square()

def construct_compatible_set(train_cache, process_slack=0.045,
                             trajectory_limit=0.10, mode='joint'):
    trajectories = train_cache['Trajectories'].float().mean(1)
    truth = train_cache['observed_trajectory'].float()
    trajectory_error = (trajectories - truth).square().mean((1, 2, 3)).sqrt()
    p = train_cache['P_history'].float()
    y = train_cache['history_labels'].float()
    mask = train_cache['history_observed'].bool()
    # Missingness is MCAR in this benchmark: integrate missing labels to one.
    # Process cohort is disjoint from both aggregate and acquisition cohorts.
    if mask.any():
        process_error = (p[:, mask] - y[mask]).square().mean(1)
    else:
        process_error = torch.zeros_like(trajectory_error)
    process_ok = process_error <= process_error.min() + process_slack
    trajectory_ok = trajectory_error <= trajectory_limit
    if mode == 'process':
        keep = process_ok
    elif mode == 'trajectory':
        keep = trajectory_ok
    elif mode == 'uncalibrated':
        keep = torch.ones_like(process_ok)
    else:
        keep = process_ok & trajectory_ok
    if not keep.any():
        raise ValueError('Empty compatible set: model inadequacy; do not silently relax thresholds')
    energy = _training_distance(trajectories, truth, trajectory_error, train_cache) / (2 * TRAJECTORY_SCALE**2)
    weights = torch.softmax((-energy).masked_fill(~keep, -torch.inf), dim=0)
    return {'weights': weights, 'mask': keep, 'process_error': process_error,
            'trajectory_error': trajectory_error}


def covariance_scores(weights, probabilities, trajectories, costs):
    """[M], [M,R], [M,...], [R] -> normalized value per cost [R]."""
    p = probabilities.float()
    z = trajectories.float().flatten(1)
    q = weights @ p
    centered = z - weights @ z
    cov = p.T @ (weights[:, None] * centered)
    return cov.square().mean(1) / (q * (1-q)).clamp_min(1e-12) / costs


def explicit_scores(weights, probabilities, trajectories, costs):
    """Independent enumeration reference for numerical/compute comparison."""
    z = trajectories.float().flatten(1)
    mu = weights @ z
    prior_var = (weights[:, None] * (z-mu).square()).sum(0).mean()
    values = []
    for p, cost in zip(probabilities.float().T, costs):
        q = weights @ p
        posterior_var = torch.zeros_like(q)
        for likelihood, mass in ((p, q), (1-p, 1-q)):
            w = weights * likelihood / mass.clamp_min(1e-12)
            posterior_var += mass * (w[:, None] * (z - w @ z).square()).sum(0).mean()
        values.append((prior_var - posterior_var) / cost)
    return torch.stack(values)


def select_evidence_batch(candidate_weights, probe_cache, pool_mask, costs,
                          batch_size=2, budget_remaining=None, strategy='Covariance',
                          generator=None):
    """Exact fantasy-branch expectation for <=4 queries, without reading answers.

    Each record is a different event-agent pair. Conditional independence given
    a mechanism is an explicit synthetic acquisition-cohort assumption.
    """
    if not 1 <= batch_size <= 4:
        raise ValueError('Exact batch enumeration supports 1..4 queries')
    p = probe_cache['P_records'].float()
    z = probe_cache['Trajectories'].float().mean(1)
    mask = pool_mask.clone()
    if torch.any(costs <= 0):
        raise ValueError('Costs must be positive')
    remaining = float('inf') if budget_remaining is None else float(budget_remaining)
    branches = [(1.0, candidate_weights)]
    selected = []
    for _ in range(batch_size):
        eligible = mask & (costs <= remaining)
        if not eligible.any():
            break
        if strategy == 'Random':
            scores = torch.rand(p.shape[1], device=p.device, generator=generator)
        else:
            scores = torch.zeros(p.shape[1], device=p.device)
            for mass, w in branches:
                q = (w @ p).clamp(1e-7, 1-1e-7)
                h = -q*q.log() - (1-q)*(1-q).log()
                if strategy == 'Entropy':
                    s = h / costs
                elif strategy == 'ParamIG':
                    pc = p.clamp(1e-7, 1-1e-7)
                    hp = -pc*pc.log() - (1-pc)*(1-pc).log()
                    s = (h - w @ hp) / costs
                else:
                    s = covariance_scores(w, p, z, costs)
                scores += mass * s
        index = int(scores.masked_fill(~eligible, -torch.inf).argmax())
        selected.append(index)
        mask[index] = False
        remaining -= float(costs[index])
        # Integrate over BOTH hypothetical answers, no arbitrary pseudo-label.
        expanded = []
        for mass, w in branches:
            for likelihood in (p[:, index], 1-p[:, index]):
                prob = w @ likelihood
                if prob > 1e-12:
                    expanded.append((mass*prob, w*likelihood/prob))
        branches = expanded
    return torch.tensor(selected, dtype=torch.long, device=p.device)


def posterior_update(weights, revealed_records, temperature=1.0):
    if temperature <= 0:
        raise ValueError('temperature must be positive')
    p = revealed_records['probabilities'].float().clamp(1e-7, 1-1e-7)
    y = revealed_records['labels'].float()
    observed = revealed_records.get('observed', torch.ones_like(y, dtype=torch.bool))
    log_likelihood = torch.where(y[None, :] > .5, p.log(), (1-p).log())
    # Optional known MNAR observation probabilities [M,R,2]. When absent,
    # missingness is ignorable and the marginal likelihood is exactly one.
    if 'observation_probability' in revealed_records:
        rho = revealed_records['observation_probability'].float().clamp(1e-7, 1-1e-7)
        observed_rho = torch.where(y[None, :] > .5, rho[..., 1], rho[..., 0])
        log_likelihood += observed_rho.log()
        missing = ((1-p)*(1-rho[..., 0]) + p*(1-rho[..., 1])).log()
    else:
        missing = torch.zeros_like(p)
    log_likelihood = torch.where(observed[None, :], log_likelihood, missing)
    logw = torch.where(weights > 0, weights.log(), -torch.inf)
    return torch.softmax(logw + log_likelihood.sum(1)/temperature, dim=0)


def predict(weights, target_cache):
    samples = target_cache['Trajectories'].float()
    conditional_mean = samples.mean(1)
    mean = torch.einsum('m,metc->etc', weights, conditional_mean)
    epistemic = torch.einsum('m,metc->etc', weights, (conditional_mean-mean).square())
    aleatoric = torch.einsum('m,metc->etc', weights, samples.var(1, unbiased=False))
    flat = samples.flatten(0, 1)
    atom_weights = weights.repeat_interleave(samples.shape[1]) / samples.shape[1]
    sorted_values, order = flat.sort(dim=0)
    cdf = atom_weights[order].cumsum(0)
    def quantile(q):
        indices = (cdf < q).sum(0).clamp_max(flat.shape[0]-1)
        return sorted_values.gather(0, indices.unsqueeze(0)).squeeze(0)
    return {'mean': mean, 'epistemic': epistemic, 'aleatoric': aleatoric,
            'lower': quantile(.05), 'upper': quantile(.95),
            # Whole paths are mixture atoms. Marginal intervals are NOT bands.
            'trajectory_atoms': samples, 'atom_weights': atom_weights,
            'record_probabilities': weights @ target_cache['P_records'].float()}


def update_and_predict(candidate_weights, revealed_records, target_cache,
                       temperature=1.0):
    weights = posterior_update(candidate_weights, revealed_records, temperature)
    return {'weights': weights, **predict(weights, target_cache)}

V2_CONFIG = {'sigma': 0.008, 'ess_floor': 12.0, 'process_weight': 8.0, 'objective': 'mean', 'late_weight': 1.0, 'batch_fantasy': True, 'update_temperature': 1.0}

# Round 2: vectorized world batches and entropy-constrained calibration.
SUPPORTS_WORLD_BATCH = True
_v1_construct = construct_compatible_set
_v1_select = select_evidence_batch
_v1_update = posterior_update


def construct_compatible_set(train_cache, process_slack=.045,
                             trajectory_limit=.10, mode='joint'):
    z=train_cache['Trajectories'].float()
    mu=z.mean(1); truth=train_cache['observed_trajectory'].float()
    err=(mu-truth).square().mean((1,2,3)).sqrt()
    mask=train_cache['history_observed'].bool()
    p=train_cache['P_history'].float()[:,mask].clamp(1e-6,1-1e-6)
    y=train_cache['history_labels'].float()[mask]
    pe=(p-y).square().mean(1) if mask.any() else torch.zeros_like(err)
    ll=-(y*p.log()+(1-y)*(1-p).log()).mean(1) if mask.any() else torch.zeros_like(err)
    keep=(err<=trajectory_limit)&(pe<=pe.min()+process_slack)
    if mode=='uncalibrated':keep=torch.ones_like(keep)
    if int(keep.sum())<V2_CONFIG['ess_floor']:
        raise ValueError('Compatible support smaller than the prespecified ESS floor')
    var=z.var(1,unbiased=False).mean(0)
    relative=(var+1e-5)/(var.mean()+1e-5)
    residual=(mu-truth).square()/relative
    distance=(residual.mean((2,3)).amax(1) if V2_CONFIG['objective']=='worst_event'
              else residual.mean((1,2,3)))
    energy=distance/(2*V2_CONFIG['sigma']**2)+V2_CONFIG['process_weight']*ll
    def gibbs(temp):return torch.softmax((-energy/temp).masked_fill(~keep,-torch.inf),0)
    # Smallest temperature >=1 with sufficient ESS. Equivalent to controlling
    # Gibbs entropy regularization; ESS itself is Renyi-2, not Shannon entropy.
    lo,hi=1.,1.
    while float(gibbs(hi).square().sum().reciprocal())<V2_CONFIG['ess_floor']+1e-4:
        hi*=2
        if hi>1e10:raise ValueError('ESS constraint infeasible')
    for _ in range(28):
        mid=(lo+hi)/2
        if float(gibbs(mid).square().sum().reciprocal())<V2_CONFIG['ess_floor']+1e-4:lo=mid
        else:hi=mid
    w=gibbs(hi)
    return {'weights':w,'mask':keep,'trajectory_error':err,'process_error':pe,
            'calibration_temperature':hi}


def posterior_update(weights,revealed_records,temperature=None):
    tau=V2_CONFIG['update_temperature'] if temperature is None else temperature
    if weights.ndim==1:return _v1_update(weights,revealed_records,tau)
    p=revealed_records['probabilities'].clamp(1e-7,1-1e-7) # W,M,B
    y=revealed_records['labels'][:,None,:]
    observed=revealed_records['observed'][:,None,:]
    ll=torch.where(y>.5,p.log(),(1-p).log())
    ll=torch.where(observed,ll,torch.zeros_like(ll)).sum(-1)
    logw=torch.where(weights>0,weights.log(),-torch.inf)
    return torch.softmax(logw+ll/tau,-1)


def _world_covariance(w,p,z,costs):
    q=w@p
    cov=torch.einsum('mr,wm,md->wrd',p,w,z)-(q[:,:,None]*(w@z)[:,None,:])
    return cov.square().mean(-1)/(q*(1-q)).clamp_min(1e-10)/costs


def select_evidence_batch(candidate_weights,probe_cache,pool_mask,costs,
                          batch_size=2,budget_remaining=None,strategy='Covariance',generator=None):
    single=candidate_weights.ndim==1
    w=candidate_weights[None,:] if single else candidate_weights
    mask=pool_mask[None,:].clone() if single else pool_mask.clone()
    p=probe_cache['P_records'].float()
    z=probe_cache['Trajectories'].float().mean(1)
    time_weight=torch.linspace(1.,V2_CONFIG['late_weight'],z.shape[2],device=z.device)
    z=(z*time_weight[None,None,:,None].sqrt()).flatten(1)
    branches=[(torch.ones(len(w),device=w.device),w)];selected=[]
    remaining=float('inf') if budget_remaining is None else float(budget_remaining)
    for j in range(batch_size):
        if strategy=='Random':scores=torch.rand(mask.shape,device=w.device,generator=generator)
        else:
            scores=torch.zeros_like(mask,dtype=torch.float32)
            for mass,bw in branches:
                q=(bw@p).clamp(1e-7,1-1e-7)
                if strategy=='Entropy':s=(-q*q.log()-(1-q)*(1-q).log())/costs
                else:s=_world_covariance(bw,p,z,costs)
                scores+=mass[:,None]*s
        ix=scores.masked_fill(~(mask&(costs<=remaining)),-torch.inf).argmax(1)
        selected.append(ix);mask.scatter_(1,ix[:,None],False)
        remaining-=float(costs[ix].max())
        if V2_CONFIG['batch_fantasy'] and j+1<batch_size:
            expanded=[]
            for mass,bw in branches:
                pi=p[:,ix].T
                for likelihood in (pi,1-pi):
                    prob=(bw*likelihood).sum(1)
                    powered=likelihood.pow(1/V2_CONFIG['update_temperature'])
                    nw=bw*powered;nw=nw/nw.sum(1,keepdim=True)
                    expanded.append((mass*prob,nw))
            branches=expanded
    result=torch.stack(selected,1)
    return result[0] if single else result


def update_and_predict(candidate_weights,revealed_records,target_cache,temperature=None):
    w=posterior_update(candidate_weights,revealed_records,temperature)
    return {'weights':w,**predict(w,target_cache)}
