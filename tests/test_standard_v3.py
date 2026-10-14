"""V3 scientific contracts; no development or test answers are opened."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unittest
import torch
import method
from evaluate import guard_prior,PriorCollapseError
from prepare_and_cache import SocialSimulator,config
from workspace import path


class StandardV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(4)
        cls.cache=torch.load(path('data/rollout_cache.pt'),weights_only=True)

    def test_geometry_and_prior(self):
        g=self.cache['geometry']
        self.assertGreaterEqual(g['distinct_predictive_mechanisms'],20)
        self.assertLess(g['train']['diameter'],.012)
        self.assertGreater(g['test']['diameter'],.18)
        out=method.construct_compatible_set(self.cache['train'])
        self.assertGreaterEqual(guard_prior(out['weights']),15)

    def test_guard_rejects_point_and_invalid_weights(self):
        for w in [torch.tensor([1.,0.]),torch.tensor([float('nan'),0.]),torch.ones(20)]:
            with self.assertRaises(PriorCollapseError):guard_prior(w)

    def test_correlated_likelihood_matches_latent_enumeration(self):
        pg=torch.tensor([[.1],[.5],[.9]])
        pool={'group':torch.tensor([0,0]),'reliability':torch.tensor([.97,.97])}
        state=method.initial_episode_state(1,1,'cpu');w=torch.ones(1,3)/3
        for j in range(2):
            w,state=method.update_one(w,state,pg,pool,torch.tensor([j]),torch.ones(1),torch.ones(1,dtype=torch.bool))
        likelihood=pg[:,0]*.97**2+(1-pg[:,0])*.03**2
        expected=likelihood/likelihood.sum()
        self.assertTrue(torch.allclose(w[0],expected,atol=1e-6))
        marginal=.03+.94*pg[:,0];incorrect=marginal.square()/marginal.square().sum()
        self.assertGreater(float((w[0]-incorrect).abs().max()),.03)

    def test_missing_record_is_identity(self):
        pg=self.cache['shared']['P_groups'];pool=self.cache['pool'];w=torch.ones(1,len(pg))/len(pg)
        state=method.initial_episode_state(1,pg.shape[1],'cpu')
        nw,ns=method.update_one(w,state,pg,pool,torch.tensor([0]),torch.ones(1),torch.zeros(1,dtype=torch.bool))
        self.assertTrue(torch.allclose(w,nw,atol=1e-7));self.assertTrue(torch.equal(ns['log_l1'],state['log_l1']))

    def test_batch_conditioning_changes_choices_without_answers(self):
        pg=torch.tensor([[.1,.1],[.1,.9],[.9,.1],[.9,.9]])
        # Two copies of each episode. First target direction is slightly heavier.
        pool={'group':torch.tensor([0,0,1,1]),'reliability':torch.full((4,),.99),
              'observed_probability':torch.ones(4)}
        z=torch.stack([2*pg[:,0],pg[:,1]],1).reshape(4,1,1,1,2)
        probe={'P_groups':pg,'Trajectories':z};w=torch.ones(1,4)/4
        state=method.initial_episode_state(1,2,'cpu');mask=torch.ones(1,4,dtype=torch.bool)
        kwargs=dict(candidate_weights=w,probe_cache=probe,pool_mask=mask,costs=torch.ones(4),
                    budget_remaining=torch.tensor([2.]),state=state,pool=pool)
        full=method.select_evidence_batch(**kwargs,condition=True)
        ablated=method.select_evidence_batch(**kwargs,condition=False)
        self.assertNotEqual(int(pool['group'][full[0,0]]),int(pool['group'][full[0,1]]))
        self.assertEqual(int(pool['group'][ablated[0,0]]),int(pool['group'][ablated[0,1]]))

    def test_variable_costs_and_no_overspend(self):
        pg=self.cache['shared']['P_groups'];pool=self.cache['pool'];w=torch.ones(2,len(pg))/len(pg)
        state=method.initial_episode_state(2,pg.shape[1],'cpu')
        probe={**self.cache['shared']['probe'],'P_groups':pg}
        allowance=torch.tensor([.5,2.]);mask=torch.ones(2,len(pool['costs']),dtype=torch.bool)
        selected=method.select_evidence_batch(w,probe,mask,pool['costs'],budget_remaining=allowance,state=state,pool=pool)
        costs=pool['costs'][selected.clamp_min(0)]*(selected>=0)
        self.assertTrue((costs.sum(1)<=allowance).all())
        self.assertEqual(len(pool['costs'].unique()),3)

    def test_unshared_repeated_parameters_equal_shared_kernel(self):
        cfg={**config(),'agents':32,'seeds':2};sim=SocialSimulator(cfg)
        theta=torch.tensor([[.4,.55,.75,.3]])
        shared=sim.run(theta,'dev',41)['Trajectories']
        independent=sim.run(theta[:,None,:].expand(-1,3,-1),'dev',41)['Trajectories']
        self.assertTrue(torch.equal(shared,independent))
        for e,cap in enumerate(sim.events('dev')[:,0]):
            self.assertLessEqual(float(shared[:,:,e,:,0].max()),int(float(cap)*32)/32+1e-6)

    def test_no_sharing_has_matched_initial_marginals(self):
        w=method.construct_compatible_set(self.cache['train'])['weights']
        indices=self.cache['unshared']['indices']
        prior=w[indices].prod(1);prior/=prior.sum()
        for e in range(3):
            marginal=torch.zeros_like(w).scatter_add_(0,indices[:,e],prior)
            self.assertTrue(torch.allclose(marginal,w,atol=1e-6,rtol=1e-5))
        self.assertTrue((indices[:,0]!=indices[:,1]).any())


if __name__=='__main__':unittest.main()
