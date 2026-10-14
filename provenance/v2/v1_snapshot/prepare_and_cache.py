"""Fixed synthetic benchmark, simulator, tensor adapter and compact rollout cache.

Freeze this file before search. No download, model API or external data by default.
"""
import argparse
import itertools
import json
import time
from workspace import path, digest, save_json
import torch

SCHEMA = 1
N_AGENTS, N_SEEDS, N_STEPS = 128, 8, 8
BUDGETS = [0, 2, 4, 8, 12, 16]
CHANNELS = ['registered', 'waitlisted', 'attended']


def device_name(request='auto'):
    return 'cuda' if request == 'auto' and torch.cuda.is_available() else ('cpu' if request == 'auto' else request)


class MIT_Benchmark_Adapter:
    """Explicit generic schema, NOT a certified MIT dataset/leaderboard adapter.

    Caller maps a named, licensed dataset to agent/event tensors and records
    [agent_id,event_id,time,stage,value,observed,group_id]. Missing values may
    be NaN only when observed=0. No real data is loaded by this project.
    """
    @staticmethod
    def convert(agents, events, stage_records, group_trajectory, *, dataset_name,
                source_uri, license_name, split, units='count'):
        if split not in {'train', 'dev', 'test'}:
            raise ValueError('Invalid split')
        if not dataset_name or not source_uri or not license_name:
            raise ValueError('Dataset provenance and license are required')
        a, e, s, g = [torch.as_tensor(x).clone() for x in (agents, events, stage_records, group_trajectory)]
        if a.ndim != 2 or e.ndim != 2 or s.ndim != 2 or s.shape[1] != 7 or g.ndim != 3:
            raise ValueError('Expected Agent[A,F], Event[E,F], Stage_Record[R,7], Group_Trajectory[E,T,C]')
        if g.shape[0] != e.shape[0] or not torch.isfinite(g).all():
            raise ValueError('Invalid trajectory/event alignment')
        if not torch.isfinite(a).all() or not torch.isfinite(e).all():
            raise ValueError('Nonfinite features')
        if s.numel():
            if not torch.isfinite(s[:, [0,1,2,3,5,6]]).all():
                raise ValueError('Nonfinite record metadata')
            if not torch.all((s[:,5] == 0) | (s[:,5] == 1)):
                raise ValueError('observed must be binary')
            if not torch.all(s[:,[0,1,2,3,6]] == s[:,[0,1,2,3,6]].floor()):
                raise ValueError('IDs/time/stage must be integers')
            if (s[:,0] < 0).any() or (s[:,0] >= len(a)).any() or (s[:,1] < 0).any() or (s[:,1] >= len(e)).any():
                raise ValueError('Unknown agent/event')
            if (s[:,2] < 0).any() or (s[:,2] >= g.shape[1]).any():
                raise ValueError('Invalid time')
            observed = s[:,5].bool()
            if not torch.all((s[observed,4] == 0) | (s[observed,4] == 1)):
                raise ValueError('Observed process outcomes must be binary')
            if len(torch.unique(s[:,[0,1,2,3]], dim=0)) != len(s):
                raise ValueError('Duplicate process records: deduplicate at source')
        return {'Agent': a, 'Event': e, 'Stage_Record': s, 'Group_Trajectory': g,
                'metadata': {'dataset': dataset_name, 'source': source_uri,
                             'license': license_name, 'split': split, 'units': units,
                             'status': 'mapped_not_benchmark_validated'}}


class SocioVerse_Campus:
    """Small constructed ambiguity benchmark; not official contest data."""
    @staticmethod
    def events(split):
        # [capacity, waitlist, forwarding, conflict, notification reach, price, start]
        # Historical mechanisms appear separately; held-out events combine them.
        rows = {
            'train': [[128,0,0,0,1.,1.,5], [128,0,0,0,.85,1.,6],
                      [22,1,0,0,1.,1.,7], [128,0,1,0,.7,1.,7]],
            'probe': [[22,1,1,0,.8,1.,5], [20,1,0,1,.9,1.,5],
                      [128,0,1,1,.75,1.,6], [18,1,1,1,.85,1.,6]],
            'dev': [[20,1,1,0,.82,1.,5], [24,1,0,1,.88,1.,5], [19,1,1,1,.72,1.,6]],
            'test': [[17,1,1,1,.78,1.,5], [26,1,1,1,.91,1.,5], [21,1,1,1,.68,1.,6]],
        }
        return torch.tensor(rows[split], dtype=torch.float32)

    @staticmethod
    def population(n, seed, device):
        g = torch.Generator(device=device).manual_seed(seed)
        # Pre-event interest, time availability, spendable budget, past experience.
        return torch.stack([.55+.45*torch.rand(n, generator=g, device=device),
                            (torch.rand(n, generator=g, device=device) > .10).float(),
                            1+2*torch.rand(n, generator=g, device=device),
                            torch.zeros(n, device=device)], dim=1)


class SocialSimulator:
    """Tensorized over mechanisms, random seeds and people; loops only time/events.

    State: informed/attempted/booked/waiting, budget, availability, experience.
    Intent is logged before capacity/conflict/budget settlement; forwarding uses
    a ring neighbor's previous state, never global private information.
    """
    def __init__(self, n_agents=N_AGENTS, n_seeds=N_SEEDS, steps=N_STEPS, device='cpu'):
        self.n, self.s, self.t, self.device = n_agents, n_seeds, steps, device

    @torch.no_grad()
    def run(self, theta, events, seed=0, misspecified=False):
        theta, events = theta.to(self.device), events.to(self.device)
        m, e = theta.shape[0], len(events)
        if theta.ndim == 2:
            theta = theta[:,None,:].expand(-1,e,-1)
        if theta.shape != (m,e,3):
            raise ValueError('Parameters must be [M,3] shared or [M,E,3] unshared')
        pop = SocioVerse_Campus.population(self.n, seed+71, self.device)
        gen = torch.Generator(device=self.device).manual_seed(seed)
        shape = (m,self.s,e,self.n)
        informed = torch.zeros(shape, dtype=torch.bool, device=self.device)
        attempted = informed.clone(); booked = informed.clone(); waiting = informed.clone()
        attended = informed.clone()
        queued = torch.full(shape, 999., device=self.device)
        budget = pop[:,2].expand(m,self.s,self.n).clone()
        experience = pop[:,3].expand(m,self.s,self.n).clone()
        priority = torch.rand((1,self.s,e,self.n), generator=gen, device=self.device)
        attention = theta[:,:,0][:,None,:,None] * events[:,4][None,None,:,None]
        part = theta[:,:,1][:,None,:,None] * pop[:,0][None,None,None,:]
        dropout = theta[:,:,2][:,None,:,None]
        traces, intents, views = [], [], []
        def random():
            # Common random numbers align mechanisms; independent truth seeds.
            return torch.rand((1,self.s,e,self.n), generator=gen, device=self.device)
        for t in range(self.t):
            window = (t < events[:,6]-1)[None,None,:,None]
            notified = (random() < attention) if t == 0 else torch.zeros_like(informed)
            if t > 0:
                peer = torch.roll(informed | booked, 1, -1)
                notified |= peer & (events[:,2][None,None,:,None] > 0) & (random() < attention*.35)
            newly_seen = notified & ~informed & window
            informed |= newly_seen
            intent = informed & ~attempted & window & (random() < part*(1+.04*experience[:,:,None,:]).clamp_max(1.2))
            # One participation decision after first notice: preserves a*p ambiguity.
            intent &= newly_seen
            attempted |= newly_seen
            cancel = booked & (random() < .035*dropout) & window
            leave = waiting & (random() < dropout) & (t > 0)
            if misspecified and t == 4:
                # Withheld common transport disruption, absent from every candidate.
                cancel |= booked & (random() < .85)
                leave |= waiting
            booked &= ~cancel; waiting &= ~leave
            budget += (cancel.float()*events[:,5][None,None,:,None]).sum(2)
            for j in range(e):
                start = int(events[j,6])
                conflict = torch.zeros_like(budget, dtype=torch.bool)
                if events[j,3] > 0:
                    same_time = (events[:,6] == events[j,6]) & (torch.arange(e,device=self.device) != j)
                    conflict = booked[:,:,same_time,:].any(2)
                eligible = (pop[:,1] > 0) & (budget >= events[j,5]) & ~conflict
                applicants = intent[:,:,j,:] & eligible
                wait_enabled = events[j,1] > 0
                queued[:,:,j,:] = torch.where(applicants, t+priority[:,:,j,:], queued[:,:,j,:])
                pool = (waiting[:,:,j,:] | applicants) & eligible & (t < start-1)
                scores = queued[:,:,j,:].masked_fill(~pool, 1e6)
                order = scores.argsort(dim=-1, stable=True)
                ranks = torch.empty_like(order).scatter_(-1, order, torch.arange(self.n,device=self.device).expand_as(order))
                slots = (events[j,0] - booked[:,:,j,:].sum(-1)).clamp_min(0)
                admit = pool & (ranks < slots[:,:,None])
                booked[:,:,j,:] |= admit
                budget -= admit * events[j,5]
                waiting[:,:,j,:] = (pool & ~admit) & wait_enabled
                if t == start:
                    arrived = booked[:,:,j,:] & (pop[:,1] > 0)
                    attended[:,:,j,:] |= arrived
                    experience += arrived
            assert not (booked & waiting).any()
            assert (booked.sum(-1) <= events[:,0][None,None,:]).all()
            assert (budget >= -1e-5).all()
            traces.append(torch.stack([booked.sum(-1),waiting.sum(-1),attended.sum(-1)],-1))
            intents.append(intent.sum(-1)); views.append(newly_seen.sum(-1))
        return {'Trajectories': torch.stack(traces,3).float()/self.n,
                'Intent': torch.stack(intents,3), 'Views': torch.stack(views,3),
                'Agent': pop, 'Event': events}


def process_cohort(theta, events, count=160, seed=12, kind='pool'):
    """Independent audit people, one Bernoulli record each (no reused counts).

    View unknown for intent rows: P(intent)=P(view)*P(intent|view), not zero.
    Conditional dropout row is sampled in a standardized observed waitlist risk
    state. Pool likelihoods therefore do not claim arbitrary-history validity.
    """
    device = theta.device
    g = torch.Generator(device=device).manual_seed(seed)
    event = torch.arange(count,device=device) % len(events)
    stage = torch.arange(count,device=device) % 3 if kind == 'pool' else torch.ones(count,device=device,dtype=torch.long)
    interest = .55+.45*torch.rand(count,generator=g,device=device)
    pars = theta[:,None,:].expand(-1,count,-1) if theta.ndim==2 else theta[:,event,:]
    a = pars[:,:,0]*events[event,4]
    b = pars[:,:,1]*interest
    p = torch.where(stage[None,:]==0,a,torch.where(stage[None,:]==1,a*b,pars[:,:,2]))
    return p.clamp(1e-5,1-1e-5), {'event':event,'stage':stage,'interest':interest}


@torch.no_grad()
def build(device):
    grid = torch.tensor(list(itertools.product(torch.linspace(.15,.95,10).tolist(),
                                               torch.linspace(.15,.95,10).tolist(),[.12,.42])),device=device)
    truth = torch.tensor([[.90,.30,.27]],device=device)
    sim = SocialSimulator(device=device)
    cache = {'schema':SCHEMA,'parameters':grid.cpu(),'budgets':BUDGETS,'channels':CHANNELS,
             'n_agents':N_AGENTS,'n_seeds':N_SEEDS,'banks':{}}
    seeds = {'train':113,'probe':211,'dev':317,'test':419}
    for bank_name in ('shared','unshared'):
        bank = {}
        for split in seeds:
            events = SocioVerse_Campus.events(split).to(device)
            if bank_name=='shared':
                theta=grid
            else:
                g=torch.Generator(device=device).manual_seed(seeds[split]+992)
                theta=torch.stack([grid[torch.randperm(len(grid),generator=g,device=device)] for _ in events],1)
            rollout=sim.run(theta,events,seeds[split])
            p,meta=process_cohort(theta,events,seed=seeds[split]+2000)
            bank[split]={'Trajectories':rollout['Trajectories'].cpu().half(),
                         'P_records':p.cpu(), 'events':events.cpu()}
            if split=='train':
                ph,_=process_cohort(theta,events,count=96,seed=914,kind='history')
                bank[split]['P_history']=ph.cpu()
        cache['banks'][bank_name]=bank
    truth_data={}
    for split in ('train','dev','test'):
        events=SocioVerse_Campus.events(split).to(device)
        actual=sim.run(truth,events,seeds[split]+10000)
        p,meta=process_cohort(truth,events,seed=seeds[split]+2000)
        g=torch.Generator(device=device).manual_seed(seeds[split]+23000)
        labels=(torch.rand(p.shape[1],device=device,generator=g)<p[0]).float()
        observed=torch.rand(p.shape[1],device=device,generator=g)>.15
        truth_data[split]={'trajectory':actual['Trajectories'][0].cpu(),
                           'labels':labels.cpu(),'observed':observed.cpu()}
        if split=='train':
            ph,_=process_cohort(truth,events,count=96,seed=914,kind='history')
            history_y=(torch.rand(96,device=device,generator=g)<ph[0]).float()
            history_observed=torch.rand(96,device=device,generator=g)>.2
            for bank in cache['banks'].values():
                bank['train'].update({'observed_trajectory':actual['Trajectories'][0].mean(0).cpu(),
                                     'history_labels':history_y.cpu(),'history_observed':history_observed.cpu()})
        else:
            shifted=sim.run(truth,events,seeds[split]+10000,misspecified=True)
            truth_data[split]['shifted_trajectory']=shifted['Trajectories'][0].cpu()
    cache['costs']=torch.ones(160)
    # Active acquisition labels are trainer-owned, never included in method APIs.
    truth_data['acquisition']=truth_data.pop('train')
    cache['truth']=truth_data
    cache['metadata']={'status':'tested_synthetic_only','population':'constructed campus example',
        'probe_source':'fixed training-rule compositions; no target labels used',
        'missingness':'MCAR; missing intent views marginalized analytically',
        'cohorts':'trajectory, passive process, active audit are disjoint independent cohorts',
        'unshared':'independent per-event parameter permutations; larger hypothesis space, prior changes',
        'security':'local integrity checks only; cache is NOT a secure held-out boundary',
        'MIT':'generic schema only, no named benchmark loaded',
        'seeds':seeds}
    return cache


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--device',default='auto',choices=['auto','cpu','cuda'])
    args=parser.parse_args()
    if path('data/rollout_cache.pt').exists():
        raise FileExistsError('Cache already exists. Preserve it; use a new benchmark workspace/version to regenerate.')
    started=time.perf_counter()
    torch.set_num_threads(4)
    device=device_name(args.device)
    cache=build(device)
    torch.save(cache,path('data/rollout_cache.pt'))
    manifest={'schema':SCHEMA,'sha256':digest('data/rollout_cache.pt'),
              'prepare_sha256':digest('prepare_and_cache.py'),'device':device,
              'size_mb':path('data/rollout_cache.pt').stat().st_size/1e6,
              'runtime_s':time.perf_counter()-started,'metadata':cache['metadata']}
    save_json('data/cache_manifest.json',manifest)
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':
    main()
