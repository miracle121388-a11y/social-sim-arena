"""The ONLY evolvable file. Baseline v0; tensor-only mechanism inference.

For binary Y and cached trajectory mean Z, total variance gives
E[Var(Z)-Var(Z|Y)] = ||Cov(Z,p(Y=1|theta))||² / (q*(1-q)).
This is model-internal expected reduction, not guaranteed real-error reduction.
"""
import torch

UPDATE_TEMPERATURE = 0.5

TRAJECTORY_SCALE = 0.001


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
    energy = trajectory_error.square() / (2 * TRAJECTORY_SCALE**2)
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
    weights = posterior_update(candidate_weights, revealed_records, temperature * UPDATE_TEMPERATURE)
    return {'weights': weights, **predict(weights, target_cache)}
