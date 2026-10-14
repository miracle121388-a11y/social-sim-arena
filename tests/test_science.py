import unittest
import torch
import method
from unittest.mock import patch
from prepare_and_cache import SocialSimulator, SocioVerse_Campus, MIT_Benchmark_Adapter, process_cohort


class ScientificContracts(unittest.TestCase):
    def test_covariance_matches_enumeration(self):
        torch.manual_seed(1)
        for _ in range(10):
            w=torch.rand(13);w/=w.sum()
            p=torch.rand(13,19);z=torch.rand(13,4,5);cost=1+torch.rand(19)
            self.assertTrue(torch.allclose(method.covariance_scores(w,p,z,cost),
                method.explicit_scores(w,p,z,cost),atol=5e-8,rtol=1e-4))

    def test_no_information_zero_score(self):
        w=torch.ones(4)/4;p=torch.full((4,3),.5);z=torch.rand(4,5)
        self.assertLess(float(method.covariance_scores(w,p,z,torch.ones(3)).abs().max()),1e-12)

    def test_known_binary_variance_reduction(self):
        w=torch.tensor([.5,.5]);p=torch.tensor([[.1],[.9]]);z=torch.tensor([[0.],[1.]])
        score=method.covariance_scores(w,p,z,torch.ones(1))
        self.assertAlmostEqual(float(score[0]),.16,places=6)

    def test_missing_marginalizes_not_negative(self):
        w=torch.tensor([.3,.7]);p=torch.tensor([[.9],[.1]])
        result=method.posterior_update(w,{'probabilities':p,'labels':torch.tensor([0.]),'observed':torch.tensor([False])})
        self.assertTrue(torch.allclose(w,result))

    def test_known_mnar_missingness(self):
        w=torch.tensor([.5,.5]);p=torch.tensor([[.8],[.2]])
        rho=torch.tensor([[[.1,.9]],[[.1,.9]]])
        result=method.posterior_update(w,{'probabilities':p,'labels':torch.zeros(1),
            'observed':torch.zeros(1,dtype=torch.bool),'observation_probability':rho})
        expected=torch.tensor([.26,.74]);self.assertTrue(torch.allclose(result,expected))

    def test_mixture_total_variance(self):
        torch.manual_seed(3);samples=torch.rand(3,4,2,5,3);w=torch.tensor([.2,.3,.5])
        pred=method.predict(w,{'Trajectories':samples,'P_records':torch.rand(3,7)})
        total=(w[:,None,None,None,None]*(samples-pred['mean']).square()).sum(0).mean(0)
        self.assertTrue(torch.allclose(total,pred['epistemic']+pred['aleatoric'],atol=1e-7))
        self.assertTrue((pred['lower']<=pred['upper']).all())
        self.assertAlmostEqual(float(pred['atom_weights'].sum()),1.,places=6)

    def test_batch_budget_and_uniqueness(self):
        torch.manual_seed(4);w=torch.ones(5)/5
        probe={'P_records':torch.rand(5,10),'Trajectories':torch.rand(5,2,2,3,3)}
        costs=torch.tensor([1.,4.,2.,1.,3.,1.,1.,2.,1.,1.]);mask=torch.ones(10,dtype=torch.bool);mask[0]=False
        q=method.select_evidence_batch(w,probe,mask,costs,batch_size=4,budget_remaining=3)
        self.assertEqual(len(q),len(torch.unique(q)));self.assertTrue(mask[q].all());self.assertLessEqual(float(costs[q].sum()),3)

    def test_batch_second_choice_integrates_both_outcomes(self):
        torch.manual_seed(11);w=torch.rand(7);w/=w.sum()
        p=torch.rand(7,9);samples=torch.rand(7,3,2,4,3);cost=torch.ones(9)
        query={'P_records':p,'Trajectories':samples};mask=torch.ones(9,dtype=torch.bool)
        actual=method.select_evidence_batch(w,query,mask,cost,batch_size=2)
        z=samples.mean(1)
        first=method.explicit_scores(w,p,z,cost).argmax()
        score=torch.zeros(9)
        for likelihood in [p[:,first],1-p[:,first]]:
            mass=w@likelihood;post=w*likelihood/mass
            score+=mass*method.explicit_scores(post,p,z,cost)
        score[first]=-torch.inf
        self.assertEqual(actual.tolist(),[int(first),int(score.argmax())])

    def test_empty_set_is_not_silently_relaxed(self):
        cache={'Trajectories':torch.zeros(2,2,1,3,3),'observed_trajectory':torch.ones(1,3,3),
               'P_history':torch.ones(2,3)*.5,'history_labels':torch.ones(3),
               'history_observed':torch.ones(3,dtype=torch.bool)}
        with self.assertRaises(ValueError):method.construct_compatible_set(cache)

    def test_fixed_baselines_do_not_call_mutable_method(self):
        import evaluate
        torch.manual_seed(22)
        train={'Trajectories':torch.zeros(5,2,1,3,3),'observed_trajectory':torch.zeros(1,3,3),
               'P_history':torch.rand(5,10),'history_labels':torch.zeros(10),
               'history_observed':torch.ones(10,dtype=torch.bool)}
        query={'P_records':torch.rand(5,10),'Trajectories':torch.rand(5,2,1,3,3)}
        with patch.object(method,'construct_compatible_set',side_effect=RuntimeError('must not be called')), \
             patch.object(method,'select_evidence_batch',side_effect=RuntimeError('must not be called')), \
             patch.object(method,'posterior_update',side_effect=RuntimeError('must not be called')):
            w=evaluate.fixed_compatible(train,'joint')['weights']
            q=evaluate.fixed_select(w,query,torch.ones(10,dtype=torch.bool),torch.ones(10),2,'ParamIG',None)
            result=evaluate.fixed_update(w,{'probabilities':query['P_records'][:,q],
                'labels':torch.zeros(2),'observed':torch.ones(2,dtype=torch.bool)})
            self.assertAlmostEqual(float(result.sum()),1.,places=6)

    def test_unseen_view_is_latent(self):
        theta=torch.tensor([[.9,.3,.2],[.3,.9,.2]])
        p,_=process_cohort(theta,SocioVerse_Campus.events('train'),count=30,kind='history')
        self.assertTrue(torch.allclose(p[0],p[1],atol=1e-7))

    def test_simulator_settlement_and_replay(self):
        sim=SocialSimulator(n_agents=24,n_seeds=2)
        events=torch.tensor([[2,1,1,1,1.,1.,5],[2,1,1,1,1.,1.,5]])
        theta=torch.tensor([[.9,.9,.1]])
        a=sim.run(theta,events,seed=1);b=sim.run(theta,events,seed=1)
        self.assertTrue(torch.equal(a['Trajectories'],b['Trajectories']))
        self.assertLessEqual(float(a['Trajectories'][...,0].max()),2/24+1e-6)
        self.assertTrue((a['Intent'][:,:,0,0] > a['Trajectories'][:,:,0,0,0]*24).any())

    def test_adapter_rejects_duplicates_and_preserves_missing(self):
        args=[torch.ones(2,3),torch.ones(1,4),torch.tensor([[0.,0.,0.,0.,float('nan'),0.,0.]]),torch.zeros(1,2,3)]
        kw={'dataset_name':'synthetic-contract','source_uri':'local:test','license_name':'synthetic','split':'train'}
        out=MIT_Benchmark_Adapter.convert(*args,**kw)
        self.assertTrue(torch.isnan(out['Stage_Record'][0,4]))
        args[2]=args[2].repeat(2,1)
        with self.assertRaises(ValueError):MIT_Benchmark_Adapter.convert(*args,**kw)


if __name__=='__main__':unittest.main()
