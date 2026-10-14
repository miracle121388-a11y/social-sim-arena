"""Independent synthetic stress configuration. Never overwrites the V1 cache.

Queue-enabled notices permit a cascade; a forwarding flag alone does not.
This deliberate interaction stress test is not a measured real-world mechanism.
"""
import itertools
import json
import time
import torch
from workspace import path, digest, save_json


def config():
    return json.loads(path('configs/high_disagreement_mode.json').read_text())


class HighDisagreementSimulator:
    def __init__(self, cfg, device='cpu'):
        self.cfg, self.device = cfg, device

    def events(self, split):
        # capacity fraction, queue, peer forwarding, conflict, start
        rows = ([[.8,1,0,0,6],[.8,0,1,0,7],[.8,1,0,0,8]] if split=='train' else
                [[.40,1,1,.9,6],[.45,1,1,.9,6],[.80,1,1,.9,7]])
        return torch.tensor(rows,device=self.device)

    @torch.no_grad()
    def run(self, theta, split, seed, shifted=False):
        cfg=self.cfg; n=cfg['n_agents']; s=cfg['n_seeds']; tmax=cfg['steps']
        events=self.events(split); m=len(theta); e=len(events)
        g=torch.Generator(device=self.device).manual_seed(seed)
        shape=(m,s,e,n)
        def rand():return torch.rand((1,s,e,n),generator=g,device=self.device)
        # Common random numbers couple mechanisms, not independent worlds.
        interest=.85+.15*rand(); available=rand()>.05
        a,b,d=[theta[:,j,None,None,None] for j in range(3)]
        u=rand(); seen=(u<a).expand(shape).clone()
        intent=(u<a*b*interest).expand(shape).clone()
        # U/a is uniform conditional on U<a: exactly the required conditional
        # participation probability; equal a*b gives identical initial intents.
        booked=torch.zeros(shape,dtype=torch.bool,device=self.device)
        waiting=booked.clone(); attended=booked.clone()
        budget=torch.full((m,s,n),3.,device=self.device)
        trajectories=[]; intents=[]
        for t in range(tmax):
            if t>0:
                peers=torch.zeros(shape,device=self.device)
                for offset in (1,2,4,8,16,32,64,128):
                    peers+=seen.roll(offset,-1).float()
                # Public queue notices are forwarded by informed peers. Single
                # historical interventions do not activate this interaction.
                cascade=events[:,1]*events[:,2]
                arrival=(~seen)&(rand()<1-(1-.65*cascade[None,None,:,None])**peers)
                intent=arrival&(rand()<b*interest)
                seen|=arrival
            intent &= t<events[None,None,:,4,None]-1
            cancel=booked&(rand()<.012*d)&(t<events[None,None,:,4,None])
            if shifted and t==4:
                cancel|=booked&(rand()<.75)
            booked &= ~cancel; budget+=cancel.sum(2)
            waiting &= ~(rand()<d*.15)
            for k in range(e):
                overlap=(events[:,4]==events[k,4]);overlap[k]=False
                occupied=booked[:,:,overlap,:].any(2)
                blocked=occupied&(rand()[:,:,k,:]<events[k,3])
                eligible=available[:,:,k,:]&(budget>=1)&~blocked
                demand=(waiting[:,:,k,:]|intent[:,:,k,:])&~booked[:,:,k,:]&eligible&(t<events[k,4])
                slots=(int(float(events[k,0])*n)-booked[:,:,k,:].sum(-1)).clamp_min(0)
                accepted=demand&(demand.long().cumsum(-1)<=slots[:,:,None])
                booked[:,:,k,:]|=accepted;budget-=accepted.float()
                waiting[:,:,k,:]=(demand&~accepted)&(events[k,1]>0)
                if t==int(events[k,4]):
                    attended[:,:,k,:]=booked[:,:,k,:]&available[:,:,k,:]&~blocked
            trajectories.append(torch.stack([booked.sum(-1),waiting.sum(-1),attended.sum(-1)],-1)/n)
            intents.append(intent.sum(-1)/n)
        return {'Trajectories':torch.stack(trajectories,3),
                'Intent':torch.stack(intents,3),'Event':events}


def probabilities(theta, history=False):
    """Independent audit cohorts. Availability is a genuine nuisance record.

    Its high irreducible entropy is intentional and explicitly reported. Pool
    stage proportions are fixed before evaluation, not selected by performance.
    """
    if history:
        interest=torch.linspace(.85,1.,256,device=theta.device)
        return theta[:,0,None]*theta[:,1,None]*interest
    p=torch.cat([theta[:,0,None].expand(-1,24),
                 torch.full((len(theta),40),.5,device=theta.device),
                 theta[:,0,None]*theta[:,1,None]*torch.linspace(.85,1.,96,device=theta.device)],1)
    return p.clamp(1e-6,1-1e-6)


def draw_world(sim, theta, split, seed):
    g=torch.Generator(device=theta.device).manual_seed(seed+100000)
    p=probabilities(theta)[0]
    labels=(torch.rand(160,device=theta.device,generator=g)<p).float()
    audit=(torch.rand((64,160),device=theta.device,generator=g)<p).float()
    observed=torch.rand(160,device=theta.device,generator=g)>.1
    return {'trajectory':sim.run(theta,split,seed)['Trajectories'][0].mean(0).cpu(),
            'labels':labels.cpu(),'observed':observed.cpu(),'audit_labels':audit.cpu()}


@torch.no_grad()
def build_high_disagreement(device):
    cfg=config(); sim=HighDisagreementSimulator(cfg,device)
    grid=torch.tensor(list(itertools.product(cfg['grid'],cfg['grid'],cfg['dropout'])),device=device)
    truth=torch.tensor([cfg['truth']],device=device)
    pair=torch.tensor(cfg['ambiguity_pair'],device=device)
    geometry={}
    for split in ('train','probe','test'):
        z=sim.run(pair,split,1103)['Trajectories'].mean(1)
        geometry[split+'_pair_rmse']=float((z[0]-z[1]).square().mean().sqrt())
    # A failed design check is kept as evidence, not silently resampled.
    save_json('provenance/v2/geometry.json',geometry)
    if not(geometry['train_pair_rmse']<.01 and geometry['probe_pair_rmse']>.15 and geometry['test_pair_rmse']>.15):
        raise ValueError(f'Pre-search geometry specification not met: {geometry}')
    bank={}
    for split,seed in [('train',1103),('probe',1907),('dev',1907),('test',1907)]:
        bank[split]={'Trajectories':sim.run(grid,split,seed)['Trajectories'].half().cpu(),
                     'P_records':probabilities(grid).cpu()}
    g=torch.Generator(device=device).manual_seed(cfg['history_seed'])
    ph=probabilities(truth,True)[0]
    bank['train'].update(P_history=probabilities(grid,True).cpu(),
        history_labels=(torch.rand(256,generator=g,device=device)<ph).float().cpu(),
        history_observed=(torch.rand(256,generator=g,device=device)>.2).cpu(),
        observed_trajectory=sim.run(truth,'train',cfg['history_seed'])['Trajectories'][0].mean(0).cpu())
    cache={'schema':cfg['schema'],'parameters':grid.cpu(),'bank':bank,'costs':torch.ones(160),
           'budgets':cfg['budgets'],'geometry':geometry,'metadata':{'status':'tested_synthetic',
           'scope':'deliberately constructed interaction and nuisance-entropy stress test',
           'uncertainty_unit':'independent simulated world; activities inside a world are dependent',
           'same_distribution_test':'fresh worlds, same fixed event design; not cross-domain validation'}}
    # Test labels live in a separate, hash-locked file, never loaded in dev.
    for split in ('dev','test'):
        worlds=[draw_world(sim,truth,split,seed) for seed in cfg[split+'_world_seeds']]
        torch.save(worlds,path(f'data/v2/{split}_truth.pt'))
    return cache


def main(device):
    started=time.perf_counter();torch.set_num_threads(4)
    path('data/v2').mkdir(exist_ok=True)
    for name in ('rollout_cache.pt','dev_truth.pt','test_truth.pt','manifest.json'):
        if path('data/v2/'+name).exists():raise FileExistsError('Preserve the existing V2 cache')
    cache=build_high_disagreement(device)
    torch.save(cache,path('data/v2/rollout_cache.pt'))
    manifest={'files':{f:digest(f) for f in ['data/v2/rollout_cache.pt','data/v2/dev_truth.pt','data/v2/test_truth.pt','configs/high_disagreement_mode.json']},
              'geometry':cache['geometry'],'runtime_s':time.perf_counter()-started,
              'size_mb':path('data/v2/rollout_cache.pt').stat().st_size/1e6}
    save_json('data/v2/manifest.json',manifest);print(json.dumps(manifest,indent=2))
