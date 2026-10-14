"""One-time documented correctness repair; no target truth or algorithm edits."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import torch
from workspace import path,digest,save_json
from prepare_and_cache import config,device_name,SocialSimulator,unshared_indices,group_probabilities,record_probabilities

before=json.loads(path('provenance/v3/pre_balance/manifest.json').read_text())
assert digest('data/rollout_cache.pt')==before['files']['data/rollout_cache.pt']
mh=digest('method.py')
truth_hash={n:digest(n) for n in ['data/v3/dev_truth.pt','data/v3/test_truth.pt']}
torch.set_num_threads(4);device=device_name();cfg=config();sim=SocialSimulator(cfg,device)
cache=torch.load(path('data/rollout_cache.pt'),weights_only=True)
indices=unshared_indices(cfg);joint=cache['parameters'].to(device)[indices.to(device)]
bank={'indices':indices}
for split in ['probe','dev','test']:
    bank[split]={'Trajectories':torch.cat([sim.run(chunk,split,cfg['cache_seed'])['Trajectories'].half().cpu()
                                        for chunk in joint.split(100)])}
bank['P_groups']=group_probabilities(joint,cache['pool']).cpu()
bank['P_records']=record_probabilities(bank['P_groups'],cache['pool'])
cache['unshared']=bank;torch.save(cache,path('data/rollout_cache.pt'))
manifest=json.loads(path('data/v3/manifest.json').read_text())
manifest['files']={n:digest(n) for n in manifest['files']}
manifest['cache_mb']=path('data/rollout_cache.pt').stat().st_size/1e6
manifest['correctness_revision']='balanced NoSharing strata; shared cache and truth unchanged'
for name in ['data/v3/manifest.json','data/cache_manifest.json']:
    path(name).write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
old=torch.load(path('provenance/v3/pre_balance/data/rollout_cache.pt'),weights_only=True)
def equal(a,b):
    if isinstance(a,torch.Tensor):return torch.equal(a,b)
    if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    return a==b
for key in ['shared','train','pool','parameters','geometry']:assert equal(old[key],cache[key]),key
assert digest('method.py')==mh
assert all(digest(n)==h for n,h in truth_hash.items())
report={'reason':'NoSharing marginal prior imbalance is an implementation confound, not a desired performance change',
        'shared_cache_equal':True,'train_pool_parameters_equal':True,'truth_files_unchanged':truth_hash,
        'method_unchanged':mh,'joint_particles':len(indices),'root_cache_sha256':digest('data/rollout_cache.pt')}
save_json('provenance/v3/balance-repair.json',report);print(json.dumps(report,indent=2))
