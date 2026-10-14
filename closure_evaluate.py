"""Post-freeze supplements; never changes the golden evaluator or method.

See CLOSURE_PROTOCOL.md for predeclared units, seeds and limitations.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import time
import uuid

import numpy as np
import torch

import evaluate as golden
import method
from prepare_and_cache import SocialSimulator, device_name
from supplemental_rules import SupplementalStressSimulator
from workspace import digest, path, save_json


def no_batch_select(w, query, mask, costs, size, budget):
    """Same covariance, same unique queries; omit within-batch fantasy updates."""
    scores = method.covariance_scores(
        w, query['P_records'], query['Trajectories'].float().mean(1), costs)
    available = mask.clone()
    chosen = []
    for _ in range(size):
        eligible = available & (costs <= budget)
        if not eligible.any():
            break
        index = int(scores.masked_fill(~eligible, -torch.inf).argmax())
        chosen.append(index)
        available[index] = False
        budget -= float(costs[index])
    return torch.tensor(chosen, device=w.device, dtype=torch.long)


def initial_weights(cache, name):
    bank = cache['banks']['unshared' if name == 'NoSharing' else 'shared']
    fixed = name in {'Random', 'Entropy', 'ParamIG', 'Standard_OED', 'SimpleStats',
                    'Uncalibrated', 'ProcessOnly', 'TrajectoryOnly', 'PassiveV1'}
    mode = {'Uncalibrated': 'uncalibrated', 'ProcessOnly': 'process',
            'TrajectoryOnly': 'trajectory'}.get(name, 'joint')
    initial = (golden.fixed_compatible(bank['train'], mode) if fixed
               else method.construct_compatible_set(bank['train'], mode=mode))
    w = initial['weights']
    if name in {'SinglePoint', 'MatchedMAP'}:
        idx = (initial['process_error'] + initial['trajectory_error']).masked_fill(
            w == 0, torch.inf).argmin() if name == 'SinglePoint' else w.argmax()
        w = torch.nn.functional.one_hot(idx, len(w)).float()
    return bank, w, fixed


def weight_path(cache, name, repeat=0, recorded_queries=None):
    bank, w, fixed = initial_weights(cache, name)
    acquisition = cache['truth']['acquisition']
    mask = acquisition['observed'].bool().clone()
    strategy = name.removeprefix('SamePrior_')
    query = {'P_records': bank['train']['P_records'], 'Trajectories':
             bank['train' if strategy in {'Standard_OED', 'NoCombination'} else 'probe']['Trajectories']}
    passive = name in {'SimpleStats', 'Uncalibrated', 'ProcessOnly', 'TrajectoryOnly', 'PassiveV1'}
    generator = torch.Generator(device=w.device).manual_seed(600 + repeat)
    queries, weights, spent, position = [], [], 0, 0
    for budget in cache['budgets']:
        while spent < budget and not passive:
            size = min(2, budget - spent)
            if recorded_queries is not None:
                batch = torch.tensor(recorded_queries[position]['indices'], device=w.device)
                position += 1
            elif name == 'NoBatchDedup':
                batch = no_batch_select(w, query, mask, cache['costs'], size, budget-spent)
            elif name.startswith('SamePrior_'):
                batch = golden.fixed_select(w, query, mask, cache['costs'], size, strategy, generator)
            else:
                batch = method.select_evidence_batch(w, query, mask, cache['costs'], size,
                                                      budget_remaining=budget-spent)
            if not len(batch) or len(batch.unique()) != len(batch) or not mask[batch].all():
                raise ValueError('Invalid supplemental query batch')
            cost = int(cache['costs'][batch].sum())
            if cost > budget-spent:
                raise ValueError('Supplemental budget exceeded')
            reveal = {'probabilities': bank['train']['P_records'][:, batch],
                      'labels': acquisition['labels'][batch], 'observed': acquisition['observed'][batch]}
            w = golden.fixed_update(w, reveal) if fixed else method.posterior_update(w, reveal)
            golden.validated_weights(w, len(bank['train']['Trajectories']))
            mask[batch] = False
            spent += cost
            queries.append({'budget': spent, 'indices': batch.tolist(), 'cost': cost})
        weights.append(w.clone())
    return {'name': name, 'repeat': repeat, 'weights': torch.stack(weights), 'queries': queries}


def summarize(values, indices):
    """First axis is independent worlds; all trailing axes stay paired."""
    x = np.asarray(values, dtype=float)
    draws = x[indices].mean(axis=1)
    return {'mean': x.mean(axis=0).tolist(),
            'ci95_low': np.quantile(draws, .025, axis=0).tolist(),
            'ci95_high': np.quantile(draws, .975, axis=0).tolist(),
            'n_independent_worlds': len(x)}


def target_for(cache, name, samples):
    bank = cache['banks']['unshared' if name == 'NoSharing' else 'shared']
    if name == 'SimpleStats':
        samples = bank['train']['observed_trajectory'].float()[None, :, None].expand(
            1, -1, len(bank['test']['events']), -1, -1)
        p = bank['train']['history_labels'][bank['train']['history_observed']].mean().expand(1, 160)
    else:
        p = bank['test']['P_records']
    return {'Trajectories': samples, 'P_records': p}


def path_metrics(cache, item, samples, truth):
    target = target_for(cache, item['name'], samples)
    weights = item['weights'] if item['name'] != 'SimpleStats' else torch.ones(
        len(cache['budgets']), 1, device=samples.device)
    means = torch.einsum('bm,metc->betc', weights, target['Trajectories'].float().mean(1))
    error = means - truth.mean(0)
    event_rmse = error.square().mean((2, 3)).sqrt()
    x = torch.tensor(cache['budgets'], dtype=torch.float64, device=samples.device)
    auc = torch.trapezoid(event_rmse.double(), x, dim=0) / (x[-1]-x[0])
    pooled = torch.trapezoid(error.square().mean((1, 2, 3)).sqrt().double(), x) / (x[-1]-x[0])
    pred = golden.fixed_prediction(weights[-1], target)
    covered = (truth >= pred['lower']) & (truth <= pred['upper'])
    out = {'event_auc': auc.tolist(), 'macro_auc': float(auc.mean()), 'pooled_auc': float(pooled),
           'event_rmse_curve': event_rmse.tolist(),
           'event_mae_curve': error.abs().mean((2, 3)).tolist(),
           'coverage90': covered.float().mean((0, 2, 3)).tolist(),
           'width90': (pred['upper']-pred['lower']).mean((1, 2)).tolist(),
           'epistemic': pred['epistemic'].mean((1, 2)).tolist(),
           'aleatoric': pred['aleatoric'].mean((1, 2)).tolist(),
           'time_channel_abs_error': error[-1].abs().tolist()}
    return out, pred


def timing_study(cache):
    bank = cache['banks']['shared']
    init = method.construct_compatible_set(bank['train'])
    p, z, costs = bank['train']['P_records'], bank['probe']['Trajectories'].float().mean(1), cache['costs']
    results = {}
    for name, w in [('frozen', init['weights']), ('uniform_compatible', init['mask'].float()/init['mask'].sum())]:
        sync = torch.cuda.synchronize if w.is_cuda else lambda: None
        method.covariance_scores(w, p, z, costs)
        method.explicit_scores(w, p, z, costs)
        rows = []
        for i in range(10):
            row, answers = {}, {}
            order = ['covariance', 'enumeration'] if i % 2 == 0 else ['enumeration', 'covariance']
            for label in order:
                fn = method.covariance_scores if label == 'covariance' else method.explicit_scores
                sync()
                start = time.perf_counter()
                answers[label] = fn(w, p, z, costs)
                sync()
                row[label+'_ms'] = 1000*(time.perf_counter()-start)
            row['speedup'] = row['enumeration_ms']/row['covariance_ms']
            row['max_abs_difference'] = float((answers['covariance']-answers['enumeration']).abs().max())
            if not torch.allclose(answers['covariance'], answers['enumeration'], atol=1e-7, rtol=1e-3):
                raise AssertionError('Covariance/enumeration mismatch')
            rows.append(row)
        results[name] = {'raw': rows, 'median_speedup': float(np.median([r['speedup'] for r in rows])),
                         'max_abs_difference': max(r['max_abs_difference'] for r in rows)}
    return results


@torch.inference_mode()
def run(args, run_id):
    start = time.perf_counter()
    golden.verify_integrity()
    frozen = json.loads(path('frozen_method.json').read_text(encoding='utf-8'))
    if digest('method.py') != frozen['method_sha256']:
        raise RuntimeError('Frozen method mismatch')
    source = json.loads(path(args.result).read_text(encoding='utf-8'))
    if source['split'] != 'test' or source['mode'] != 'full_paper_ablation' or source['method_sha256'] != frozen['method_sha256']:
        raise ValueError('A full, frozen test result is required')
    torch.set_num_threads(4)
    device = device_name(args.device)
    cache = golden.move(torch.load(path('data/rollout_cache.pt'), weights_only=True), device)
    paths = [weight_path(cache, r['strategy'], r['repeat'], r['queries']) for r in source['strategies']]
    paths += [weight_path(cache, n, r) for n in ['NoBatchDedup', 'MatchedMAP', 'SamePrior_Random',
              'SamePrior_Entropy', 'SamePrior_ParamIG', 'SamePrior_Standard_OED']
              for r in range(3 if n == 'SamePrior_Random' else 1)]
    cached = []
    for item in paths:
        bank = cache['banks']['unshared' if item['name'] == 'NoSharing' else 'shared']
        row, _ = path_metrics(cache, item, bank['test']['Trajectories'], cache['truth']['test']['trajectory'])
        if len(cached) < len(source['strategies']):
            expected = source['strategies'][len(cached)]['auc_error']
            if abs(row['pooled_auc']-expected) > 2e-7:
                raise AssertionError('Reconstructed golden AUC mismatch')
        cached.append({'name': item['name'], 'repeat': item['repeat'], 'queries': item['queries'], **row})
    simulator, stress_sim = SocialSimulator(device=device), SupplementalStressSimulator(device=device)
    grid = cache['parameters']
    theta_true = torch.tensor([[.90, .30, .27]], device=device)
    events = cache['banks']['shared']['test']['events']
    gen = torch.Generator(device=device).manual_seed(419+992)
    unshared = torch.stack([grid[torch.randperm(len(grid), generator=gen, device=device)] for _ in events], 1)
    worlds = []
    for k in range(args.worlds):
        seed = 51000 + 101*k
        targets = {name: simulator.run(theta, events, seed)['Trajectories'].half()
                   for name, theta in [('shared', grid), ('unshared', unshared)]}
        truths = {'none': simulator.run(theta_true, events, seed+100000)['Trajectories'][0]}
        for shift in ['waiting', 'propagation', 'both', 'transport']:
            truths[shift] = stress_sim.run(theta_true, events, seed+100000,
                stress='none' if shift == 'transport' else shift,
                misspecified=shift == 'transport')['Trajectories'][0]
        world = {'world': k, 'candidate_seed': seed, 'truth_seed': seed+100000, 'strategies': [], 'stress': []}
        for item in paths:
            samples = targets['unshared' if item['name'] == 'NoSharing' else 'shared']
            row, pred = path_metrics(cache, item, samples, truths['none'])
            world['strategies'].append({'name': item['name'], 'repeat': item['repeat'], **row})
            if item['name'] in {'Covariance', 'SinglePoint', 'MatchedMAP', 'PassiveV1'}:
                for shift, observed in truths.items():
                    error = (pred['mean']-observed.mean(0)).square().mean((1, 2)).sqrt()
                    # First realized trajectory, not an average over simulation seeds.
                    outside = ((observed[0] < pred['lower']) | (observed[0] > pred['upper'])).float().mean((1, 2))
                    epi = pred['epistemic'].mean((1, 2))
                    world['stress'].append({'name': item['name'], 'shift': shift,
                        'rmse': error.tolist(), 'outside_fraction': outside.tolist(),
                        'interval_alarm': (outside > .20).float().tolist(),
                        'original_diagnostic': ((epi < .0025) & (error > .08)).float().tolist(),
                        'truth_shift_rmse': (observed-truths['none']).square().mean((0, 2, 3)).sqrt().tolist()})
        worlds.append(world)
        print(f'WORLD | {k+1}/{args.worlds}', flush=True)
    indices = np.random.default_rng(782).integers(args.worlds, size=(2000, args.worlds))
    grouped = defaultdict(list)
    for world in worlds:
        per_world = defaultdict(list)
        for row in world['strategies']:
            per_world[row['name']].append(row)
        for name, rows in per_world.items():
            grouped[name].append({key: np.mean([r[key] for r in rows], axis=0).tolist()
                                 for key in rows[0] if key not in {'name', 'repeat'}})
    summaries = {name: {key: summarize([r[key] for r in rows], indices) for key in rows[0]}
                 for name, rows in grouped.items()}
    paired = {name: summarize(np.asarray([r['event_auc'] for r in rows]) -
                             np.asarray([r['event_auc'] for r in grouped['Covariance']]), indices)
              for name, rows in grouped.items() if name != 'Covariance'}
    stress_summary = {}
    for name in ['Covariance', 'SinglePoint', 'MatchedMAP', 'PassiveV1']:
        stress_summary[name] = {}
        for shift in truths:
            rows = [next(r for r in w['stress'] if r['name'] == name and r['shift'] == shift) for w in worlds]
            stress_summary[name][shift] = {key: summarize([r[key] for r in rows], indices)
                for key in rows[0] if key not in {'name', 'shift'}}
    golden.verify_integrity()
    assert digest('method.py') == frozen['method_sha256']
    return {'run_id': run_id, 'status': 'tested_synthetic', 'golden_result': args.result,
            'method_sha256': frozen['method_sha256'], 'protocol_sha256': digest('CLOSURE_PROTOCOL.md'),
            'supplement_code_sha256': {f: digest(f) for f in ['closure_evaluate.py', 'supplemental_rules.py']},
            'device': device, 'worlds': args.worlds, 'budgets': cache['budgets'],
            'uncertainty_unit': 'independent worlds; per-template activities paired within worlds',
            'conditioning': 'fixed training/evidence and three event templates; population/MC variation only',
            'official_SocioVerse': 'NOT_EVALUATED', 'official_MIT': 'NOT_EVALUATED',
            'cached_results': cached, 'summary': summaries, 'paired_event_auc_minus_full': paired,
            'stress_summary': stress_summary, 'raw_worlds': worlds,
            'timing': timing_study(cache), 'runtime_s_before_timing': time.perf_counter()-start}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--result', required=True)
    parser.add_argument('--device', default='auto', choices=['auto', 'cpu', 'cuda'])
    parser.add_argument('--worlds', type=int, default=24)
    args = parser.parse_args()
    if args.worlds < 2:
        parser.error('At least two independent worlds are required')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-closure-'+uuid.uuid4().hex[:8]
    start = time.perf_counter()
    try:
        result = run(args, run_id)
        result['runtime_s'] = time.perf_counter()-start
        save_json('results/'+run_id+'.json', result)
    except Exception:
        import traceback
        save_json('results/'+run_id+'.json', {'run_id': run_id, 'status': 'crash', 'error': traceback.format_exc()})
        raise
    print('SUPPLEMENT | results/'+run_id+'.json', flush=True)


if __name__ == '__main__':
    main()
