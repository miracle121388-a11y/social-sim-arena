"""Scientific invariants, using training data and fabricated evaluation worlds."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import time
import types
import unittest
import torch
from workspace import path,digest
from v2_evaluation import move,run_policy,guards


class V2Invariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(4)
        cls.device='cuda' if torch.cuda.is_available() else 'cpu'
        cls.cache=move(torch.load(path('data/v2/rollout_cache.pt'),weights_only=True),cls.device)
        cls.module=types.ModuleType('test_candidate')
        cfg=json.loads(path('configs/v2_trials.json').read_text())[0]['config']
        source=path('provenance/v2/v1_snapshot/method.py').read_text()+'\nV2_CONFIG='+repr(cfg)+'\n'+path('configs/v2_method_body.txt').read_text()
        exec(compile(source,'method-template','exec'),cls.module.__dict__)

    def test_v1_unchanged(self):
        manifest=json.loads(path('provenance/v2/v1_snapshot/manifest.json').read_text())
        for name in ['method.py','prepare_and_cache.py','evaluate.py','program.md']:
            self.assertEqual(digest('provenance/v2/v1_snapshot/'+name),manifest[name])
        self.assertEqual(digest('data/rollout_cache.pt'),'5cda2802953d611e8ac61cf2c51050e138d7df0616ac7362a578f6da63553289')

    def test_geometry(self):
        geo=self.cache['geometry']
        self.assertLess(geo['train_pair_rmse'],.01)
        self.assertGreater(geo['probe_pair_rmse'],.15)
        self.assertGreater(geo['test_pair_rmse'],.15)

    def test_ess_and_missingness(self):
        w=self.module.construct_compatible_set(self.cache['bank']['train'])['weights']
        self.assertGreaterEqual(float(1/w.square().sum()),8.)
        p=self.cache['bank']['probe']['P_records'][:,:2]
        revealed={'probabilities':p,'labels':torch.zeros(2,device=self.device),'observed':torch.zeros(2,dtype=torch.bool,device=self.device)}
        self.assertTrue(torch.allclose(w,self.module.posterior_update(w,revealed),atol=1e-6))

    def test_vector_covariance_and_batch(self):
        w=self.module.construct_compatible_set(self.cache['bank']['train'])['weights']
        p=self.cache['bank']['probe']['P_records'];z=self.cache['bank']['probe']['Trajectories'].float().mean(1)
        c=self.cache['costs']
        a=self.module.covariance_scores(w,p,z,c)
        b=self.module._world_covariance(w[None,:],p,z.flatten(1),c)[0]
        self.assertTrue(torch.allclose(a,b,atol=2e-7,rtol=2e-3))
        mask=torch.ones(2,p.shape[1],dtype=torch.bool,device=self.device)
        ix=self.module.select_evidence_batch(w.expand(2,-1),self.cache['bank']['probe'],mask,c)
        self.assertTrue((ix[:,0]!=ix[:,1]).all())

    def test_pipeline_with_fabricated_worlds(self):
        bank=self.cache['bank'];w=self.module.construct_compatible_set(bank['train'])['weights']
        fake={'trajectory':bank['dev']['Trajectories'][0].float().mean(0),
              'labels':torch.zeros(160,device=self.device),
              'observed':torch.ones(160,dtype=torch.bool,device=self.device),
              'audit_labels':torch.zeros(64,160,device=self.device)}
        started=time.perf_counter()
        for name in ['Full','Random','Entropy']:
            out=run_policy(self.module,self.cache,[fake]*12,'dev',name,w)
            self.assertEqual(len(out['activity_results']),3)
            self.assertEqual(len(out['world_auc']),12)
        print('Fabricated-world 3-policy smoke runtime:',round(time.perf_counter()-started,3))

    def test_guards_reject_collapse(self):
        s={'auc':.1,'initial_brier':.18,'final_brier':.18,'b0_b16_difference_ci95':[.01,.03]}
        obj={'initial_ess':1.,'runtime_s':1.,'strategies':{'Full':s,'Random':{**s,'auc':.12},'Entropy':{**s,'auc':.12}}}
        self.assertFalse(guards(obj)['ess'])


if __name__=='__main__':unittest.main()
