import math
import random
from dataclasses import replace
import unittest
from njusim.research.acquisition import composition_score, enumeration_score, disagreement, update_weights, candidate_information_gain
from njusim.research.hypotheses import Hypothesis, HypothesisSet, compatible
from njusim.research.evidence import Query, QueryPool
from njusim.research.evaluator import SyntheticOracle
from njusim.research.probes import ProbeKey, ProbeCache, validate_partitions, normalized_budget_auc

class ResearchTests(unittest.TestCase):
    def test_covariance_matches_explicit_outcomes(self):
        r=random.Random(611)
        for _ in range(300):
            k=r.randint(2,10);d=r.randint(1,8)
            w=[r.random() for _ in range(k)];p=[r.random() for _ in range(k)]
            z=[[r.uniform(-2,2) for _ in range(d)] for _ in range(k)]
            self.assertAlmostEqual(composition_score(w,p,z),enumeration_score(w,p,z),places=11)

    def test_uninformative_high_entropy_has_zero_value(self):
        self.assertEqual(composition_score([1,1],[.5,.5],[[0],[1]]),0)
        self.assertEqual(candidate_information_gain([1,1],[.5,.5]),0)

    def test_candidate_disagreement_without_target_difference_is_zero(self):
        self.assertEqual(composition_score([1,1],[0,1],[[3,2],[3,2]]),0)

    def test_cost_and_target_scaling(self):
        args=([.4,.6],[.2,.8],[[0,1],[1,0]])
        s=composition_score(*args)
        self.assertAlmostEqual(composition_score(*args,cost=2),s/2)
        self.assertAlmostEqual(composition_score(args[0],args[1],[[0,2],[2,0]]),4*s)

    def test_boundaries_and_zero_weight_candidates(self):
        for p in ([0,0],[1,1],[1e-300,2e-300],[1-1e-15,1-2e-15]):
            s=composition_score([1,1],p,[[0],[1]])
            self.assertTrue(math.isfinite(s));self.assertGreaterEqual(s,0)
        self.assertEqual(composition_score([1,0],[0,1],[[0],[99]]),0)

    def test_bad_numeric_inputs_fail_closed(self):
        for w,p,z,c in [
            ([0,0],[0,1],[[0],[1]],1),([1,-1],[0,1],[[0],[1]],1),
            ([1,1],[math.nan,1],[[0],[1]],1),([1,1],[0,1],[[0],[1,2]],1),
            ([1,1],[0,1],[[math.inf],[1]],1),([1,1],[0,1],[[0],[1]],0)]:
            with self.assertRaises(ValueError):composition_score(w,p,z,c)

    def test_impossible_evidence_is_mismatch_not_uniform_reset(self):
        with self.assertRaises(ValueError):update_weights([1,1],[0,0],1)
        self.assertEqual(update_weights([1,1],[0,1],1),(0,1))

    def test_expected_reduction_bounded_by_prior_disagreement(self):
        w=[1,2,3];p=[.2,.7,.9];z=[[0,2],[1,-1],[2,0]]
        self.assertLessEqual(composition_score(w,p,z),disagreement(w,z)+1e-12)

    def candidate(self, id="a", parameter=0):
        return Hypothesis(id,"generic_stage",(("response_bias",parameter),),.2,.3,("train",),"grid-v1")

    def test_candidates_same_training_set_and_thresholds(self):
        a=self.candidate();b=self.candidate("b",2);bad=replace(b,process_loss=.8)
        self.assertEqual(len(compatible([a,b,bad],train_event_ids=["train"],epsilon_process=.5,epsilon_rollout=.5).candidates),2)
        with self.assertRaises(ValueError):compatible([replace(a,fit_event_ids=("test",))],train_event_ids=["train"],epsilon_process=1,epsilon_rollout=1)
        with self.assertRaises(ValueError):compatible([a],train_event_ids=["train"],epsilon_process=0,epsilon_rollout=0)

    def test_duplicate_parameters_not_false_diversity(self):
        a=self.candidate()
        with self.assertRaises(ValueError):HypothesisSet((a,replace(a,id="alias")),(1,1))
        h=HypothesisSet((a,self.candidate("b",2)),(1,1))
        self.assertEqual(h.effective_size,2)

    def query(self, id="q", **kw):
        return Query(id,"train","generic_decision",1,"synthetic-fixture",id,**kw)

    def pool(self, queries=None,budget=2):
        return QueryPool(queries or [self.query()],train_event_ids=["train"],budget=budget)

    def test_sealed_test_and_field_access_and_real_data_rejected(self):
        for q in [replace(self.query(),split="test"),replace(self.query(),event_id="test"),
                  self.query(permitted=False),self.query(provenance="real_observed"),self.query(provenance="model_generated")]:
            pool=self.pool([q]);calls=[]
            with self.assertRaises(PermissionError):pool.reveal(q.id,history_token=pool.history_token,read_label=lambda _:calls.append(1))
            self.assertEqual(calls,[]);self.assertEqual(pool.spent,0)

    def test_budget_duplicate_and_stale_history_rejected(self):
        pool=self.pool([self.query("a"),self.query("b")],budget=1)
        oracle=SyntheticOracle({"a":1,"b":0});token=pool.history_token
        pool.reveal("a",history_token=token,read_label=oracle.read_label)
        self.assertEqual(pool.spent,1)
        for q,t in [("b",token),("a",pool.history_token),("b",pool.history_token)]:
            with self.assertRaises(ValueError):pool.reveal(q,history_token=t,read_label=oracle.read_label)
        self.assertEqual(pool.spent,1)

    def test_incomplete_or_inapplicable_queries_rejected(self):
        for kwargs in [dict(history_complete=False),dict(at_risk=False),dict(censored=True),dict(directly_changes_target=True)]:
            pool=self.pool([self.query(**kwargs)])
            with self.assertRaises(ValueError):pool.check("q",pool.history_token)

    def test_missing_label_not_billed_or_converted_to_zero(self):
        pool=self.pool()
        with self.assertRaises(ValueError):pool.reveal("q",history_token=pool.history_token,read_label=lambda _:None)
        self.assertEqual(pool.spent,0);self.assertEqual(pool.revealed,())

    def test_duplicate_opportunity_alias_rejected(self):
        q=self.query()
        with self.assertRaises(ValueError):self.pool([q,replace(q,id="alias")])

    def key(self):
        return ProbeKey("candidate","backend","simulator","population","configuration",("occupancy","queue"),(10,10),(1,2,3),"paired-v1")

    def test_cache_separates_parameters_rules_backend_population_and_seeds(self):
        cache=ProbeCache();key=self.key()
        mean,var,n=cache.put(key,[[0,10],[10,20],[20,30]])
        self.assertEqual(mean,(1,2));self.assertEqual(var,(1,1));self.assertEqual(n,3)
        with self.assertRaises(ValueError):cache.put(key,[[0,0]]*3)
        for field,value in [("candidate_fingerprint","other"),("configuration_fingerprint","other"),
                            ("backend_fingerprint","other"),("simulator_fingerprint","other"),
                            ("population_fingerprint","other"),("seeds",(4,5,6)),("scales",(1,1))]:
            with self.assertRaises(KeyError):cache.get(replace(key,**{field:value}))

    def test_probe_test_configuration_leakage_rejected(self):
        validate_partitions({"tr":"a"},{"dev":"b"},{"probe":"c"},{"test":"d"})
        with self.assertRaises(ValueError):validate_partitions({"tr":"a"},{"dev":"b"},{"probe":"d"},{"test":"d"})
        with self.assertRaises(ValueError):validate_partitions({"tr":"a"},{"tr":"b"},{"probe":"c"},{"test":"d"})

    def test_auc_equal_event_weight_and_common_budget_support(self):
        self.assertAlmostEqual(normalized_budget_auc([0,1,2],[[1,.5,0],[.2,.2,.2]]),.35)
        with self.assertRaises(ValueError):normalized_budget_auc([0,2,1],[[1,.5,0]])
        with self.assertRaises(ValueError):normalized_budget_auc([0,1,2],[[1,.5]])
