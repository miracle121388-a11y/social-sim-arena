"""Fixed V3 simulator, correlated process audits, and immutable split caches."""
import argparse
import itertools
import json
import time
import torch
from workspace import path, digest, save_json

def config():
    return json.loads(path('configs/standard_v3.json').read_text())

def device_name(request='auto'):
    return 'cuda' if request!='cpu' and torch.cuda.is_available() else 'cpu'

class SocialSimulator:
    """Intent -> capacity/conflict settlement -> budget/information feedback.
    theta = attention, conditional participation, cascade, audit nuisance.
    Shared [M,4] and independent [M,E,4] parameters use the SAME kernel.
    """
    def __init__(self,cfg=None,device='cpu'):
        self.cfg=cfg or config();self.device=device

    def events(self,split):
        # capacity fraction, waitlist, forwarding, exclusive conflict, reach, start
        rows={
            'train':[[.8,1,0,0,1.,6],[.8,0,1,0,.9,7],[.8,1,0,0,.8,8]],
            'probe':[[.40,1,1,1,.9,6],[.45,1,1,1,.85,6],[.80,1,1,1,.8,7]],
            'dev':[[.38,1,1,1,.95,5],[.42,1,1,1,.8,5],[.75,1,1,1,.9,8]],
            'test':[[.35,1,1,1,.85,6],[.48,1,1,1,.95,6],[.70,1,1,1,.75,8]]
        }[split]
        return torch.tensor(rows,device=self.device)

    @torch.no_grad()
    def run(self,theta,split,seed):
        n=self.cfg['agents'];s=self.cfg['seeds'];events=self.events(split);e=len(events)
        m=len(theta);pars=theta[:,None,:].expand(-1,e,-1) if theta.ndim==2 else theta
        a,b,c=[pars[:,:,i][:,None,:,None] for i in range(3)]
        g=torch.Generator(device=self.device).manual_seed(seed)
        def rand():return torch.rand((1,s,e,n),generator=g,device=self.device)
        interest=.85+.15*rand();available=rand()>.05;u=rand()
        reach=events[None,None,:,4,None]
        seen=(u<a*reach).clone();intent=(u<a*b*reach*interest).clone()
        # Conditional on seeing, U/(a*reach) is uniform. Equal a*b gives equal intents.
        booked=torch.zeros((m,s,e,n),dtype=torch.bool,device=self.device)
        waiting=booked.clone();attended=booked.clone()
        budget=torch.full((m,s,n),3.,device=self.device)
        trajectory=[];intent_path=[]
        for t in range(self.cfg['steps']):
            if t:
                peers=torch.zeros_like(seen,dtype=torch.float32)
                for offset in [1,2,4,8,16,32,64,128]:peers+=seen.roll(offset,-1)
                enabled=(events[:,1]*events[:,2])[None,None,:,None]
                arrival=(~seen)&(rand()<1-(1-.55*c*enabled)**peers)
                intent=arrival&(rand()<b*interest);seen|=arrival
            intent &= t<events[None,None,:,5,None]-1
            cancel=booked&(rand()<.0015)&(t<events[None,None,:,5,None])
            booked &= ~cancel;budget+=cancel.sum(2)
            waiting &= rand()>.018
            for k in range(e):
                overlaps=events[:,5]==events[k,5];overlaps[k]=False
                blocked=booked[:,:,overlaps,:].any(2)&(events[k,3]>0)
                eligible=available[:,:,k,:]&(budget>=1)&~blocked
                demand=(waiting[:,:,k,:]|intent[:,:,k,:])&~booked[:,:,k,:]&eligible&(t<events[k,5])
                slots=(int(float(events[k,0])*n)-booked[:,:,k,:].sum(-1)).clamp_min(0)
                accepted=demand&(demand.long().cumsum(-1)<=slots[:,:,None])
                booked[:,:,k,:]|=accepted;budget-=accepted.float()
                waiting[:,:,k,:]=(demand&~accepted)&(events[k,1]>0)
                if t==int(events[k,5]):attended[:,:,k,:]=booked[:,:,k,:]&available[:,:,k,:]
            trajectory.append(torch.stack([booked.sum(-1),waiting.sum(-1),attended.sum(-1)],-1)/n)
            intent_path.append(intent.sum(-1)/n)
        return {'Trajectories':torch.stack(trajectory,3),'Intent':torch.stack(intent_path,3),'Event':events}

def pool_definition(cfg):
    names=[name for name,count in cfg['group_counts'].items() for _ in range(count)]
    groups=torch.arange(len(names)).repeat_interleave(cfg['records_per_group'])
    stages=torch.tensor([['view','cascade','nuisance','ordinary','noise'].index(n) for n in names])
    group_cost=torch.tensor([(.5 if i%2==0 else 1.) if n in ['view','cascade'] else
                            (2. if n=='ordinary' else .5) for i,n in enumerate(names)])
    g=torch.Generator().manual_seed(cfg['pool_permutation_seed'])
    order=torch.randperm(len(groups),generator=g)
    return {'group':groups[order],'stage':stages[groups[order]],'group_stage':stages,
            'costs':group_cost[groups[order]],'event':torch.zeros(len(groups),dtype=torch.long),
            'reliability':torch.full((len(groups),),cfg['sensor_reliability']),
            'observed_probability':torch.full((len(groups),),cfg['observation_probability'])}

def group_probabilities(theta,pool):
    pars=theta if theta.ndim==2 else theta[:,0,:]
    a,b,c,h=pars.T;stage=pool['group_stage'].to(theta.device)
    return torch.stack([a,c,h,a*b*.925,torch.full_like(a,.5)],1)[:,stage].clamp(1e-6,1-1e-6)

def record_probabilities(pg,pool):
    r=pool['reliability'].to(pg.device);groups=pool['group'].to(pg.device)
    return (1-r)+(2*r-1)*pg[:,groups]

def sample_audit(pg,pool,g,replicates=1):
    latent=torch.rand((replicates,pg.numel()),generator=g,device=pg.device)<pg
    groups=pool['group'].to(pg.device);r=pool['reliability'].to(pg.device)
    prob=torch.where(latent[:,groups],r,1-r)
    return (torch.rand(prob.shape,generator=g,device=pg.device)<prob).float()

def unshared_indices(cfg):
    """Balanced conditional marginals in EVERY product-stratum combination.

    Each of the eight combinations contains four Latin-hypercube replicates of
    all 100 nuisance-inclusive mechanisms per activity. This avoids losing
    support merely because history rejects one product stratum.
    """
    g=torch.Generator().manual_seed(cfg['unshared_seed'])
    repetitions=cfg['unshared_particles']//800
    return torch.cat([torch.stack([100*s+torch.randperm(100,generator=g) for s in strata],1)
                      for strata in itertools.product(range(2),repeat=3)
                      for _ in range(repetitions)],0)

@torch.no_grad()
def build(device):
    cfg=config();sim=SocialSimulator(cfg,device);pool=pool_definition(cfg)
    grid=torch.tensor([[a,p/a,c,h] for p,a,c,h in itertools.product(cfg['products'],cfg['attention'],cfg['cascade'],cfg['nuisance'])],device=device)
    assert len(grid)==200
    truth=torch.tensor([cfg['truth']],device=device)
    cache={'schema':cfg['schema'],'parameters':grid.cpu(),'pool':pool,'budgets':cfg['budgets'],'shared':{},'unshared':{}}
    for split in ['train','probe','dev','test']:
        cache['shared'][split]={'Trajectories':sim.run(grid,split,cfg['cache_seed'])['Trajectories'].half().cpu()}
    pg=group_probabilities(grid,pool).cpu()
    cache['shared']['P_groups']=pg;cache['shared']['P_records']=record_probabilities(pg,pool)
    interest=torch.linspace(.85,1.,256,device=device)
    ph=grid[:,0,None]*grid[:,1,None]*interest
    g=torch.Generator(device=device).manual_seed(cfg['history_seed'])
    truep=truth[0,0]*truth[0,1]*interest
    cache['train']={**cache['shared']['train'],'P_history':ph.cpu(),
        'history_labels':(torch.rand(256,device=device,generator=g)<truep).float().cpu(),
        'history_observed':(torch.rand(256,device=device,generator=g)>.2).cpu(),
        'observed_trajectory':sim.run(truth,'train',cfg['history_seed'])['Trajectories'][0].mean(0).cpu()}
    alias=torch.where((grid[:,0]*grid[:,1]-.22).abs()<1e-5)[0].cpu()
    geometry={'alias_count':len(alias),'distinct_predictive_mechanisms':25,
              'definition':'pairwise RMSE diameter; not a lower bound on every pair'}
    for split in ['train','probe','dev','test']:
        z=cache['shared'][split]['Trajectories'].float().mean(1)[alias].flatten(1)
        dist=torch.pdist(z)/z.shape[1]**.5
        geometry[split]={'diameter':float(dist.max()),'median':float(dist.median()),
                         'fraction_above_018':float((dist>.18).float().mean())}
    save_json('provenance/v3/geometry.json',geometry)
    if not(geometry['train']['diameter']<.012 and geometry['probe']['diameter']>.18 and geometry['test']['diameter']>.18):
        raise ValueError('Pre-evaluation geometry check failed; preserve evidence before protocol changes')
    indices=unshared_indices(cfg)
    cache['unshared']['indices']=indices;joint=grid[indices.to(device)]
    for split in ['probe','dev','test']:
        parts=[sim.run(chunk,split,cfg['cache_seed'])['Trajectories'].half().cpu() for chunk in joint.split(100)]
        cache['unshared'][split]={'Trajectories':torch.cat(parts)}
    cache['unshared']['P_groups']=group_probabilities(joint,pool).cpu()
    cache['unshared']['P_records']=record_probabilities(cache['unshared']['P_groups'],pool)
    for split in ['dev','test']:
        worlds=[]
        for seed in cfg[split+'_seeds']:
            g=torch.Generator(device=device).manual_seed(seed+30000);pt=group_probabilities(truth,pool)[0]
            worlds.append({'trajectory':sim.run(truth,split,seed)['Trajectories'][0].mean(0).cpu(),
                'labels':sample_audit(pt,pool,g)[0].cpu(),
                'observed':(torch.rand(len(pool['group']),generator=g,device=device)<cfg['observation_probability']).cpu(),
                'audit_labels':sample_audit(pt,pool,g,64).cpu()})
        torch.save(worlds,path('data/v3/'+split+'_truth.pt'))
    cache['geometry']=geometry
    cache['metadata']={'status':'tested_synthetic_only','missingness':'MCAR',
        'joint_observations':'shared Bernoulli episode; conditionally independent noisy sensor records',
        'test_status':'sealed; candidate predictions but no target answers inside main cache',
        'no_sharing':'independent activity joint particles; prior dependence changes'}
    return cache

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--device',default='auto',choices=['auto','cpu','cuda'])
    args=parser.parse_args();torch.set_num_threads(4);started=time.perf_counter()
    if path('data/v3/manifest.json').exists():raise FileExistsError('V3 cache already generated; preserve frozen data')
    prior=json.loads(path('provenance/v3/previous/manifest.json').read_text())
    if digest('data/rollout_cache.pt')!=prior['files']['data/rollout_cache.pt']:
        raise RuntimeError('Existing root cache is not the archived V1 cache')
    path('data/v3').mkdir(exist_ok=True)
    cache=build(device_name(args.device));torch.save(cache,path('data/rollout_cache.pt'))
    files=['data/rollout_cache.pt','data/v3/dev_truth.pt','data/v3/test_truth.pt','configs/standard_v3.json']
    manifest={'schema':cache['schema'],'files':{f:digest(f) for f in files},
              'runtime_s':time.perf_counter()-started,'cache_mb':path('data/rollout_cache.pt').stat().st_size/1e6,
              'geometry':cache['geometry']}
    save_json('data/v3/manifest.json',manifest)
    path('data/cache_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
