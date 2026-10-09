from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import json
import math
import sys
import unittest
from njusim.fixtures import population, scenario
from njusim.kernel import Simulator
from njusim.backends import OfflineFixtureBackend, SimpleStatisticalBackend, ResponseCacheBackend, JevBackend, StructuredLLMBackend
from njusim.calibration import SharedCalibrator, usable_rows
from njusim.metrics import metrics, replay_trace
from njusim.experiments import verify_replay, validate_splits
from njusim.io import ROOT, safe_path, write_json

class AllAct:
    name='controlled_fixture';version='1'
    def probabilities(self,obs):
        yes=obs.stage!='cancel'
        return {'yes':float(yes),'no':float(not yes)}

class CancelOne(AllAct):
    def probabilities(self,obs):
        yes=(obs.agent_id=='syn-00') if obs.stage=='cancel' else True
        return {'yes':float(yes),'no':float(not yes)}

def make(name='S2',n=8,backend=None,seed=7,**kwargs):
    spec=scenario(name,n=n,**kwargs)
    return Simulator(spec,population(n),backend or OfflineFixtureBackend(),seed=seed,stream='test-pair')

class KernelTests(unittest.TestCase):
    def test_unreceived_information_absent(self):
        spec=scenario('S1',n=3)
        spec=replace(spec,activities=(replace(spec.activities[0],initial_informed=('syn-00',)),))
        sim=Simulator(spec,population(3),AllAct());sim.run()
        decisions=[r for r in sim.records if r['kind']=='decision']
        self.assertEqual({r['agent'] for r in decisions},{'syn-00'})
        for r in decisions:
            self.assertNotIn('capacity',r['observation']['visible_activity'])
            self.assertNotIn('future_labels',r['observation'])
            for m in r['observation']['sources']:self.assertLessEqual(m['arrived_at'],r['time'])

    def test_sent_delivered_viewed_distinct(self):
        sim=make('S1');sim.step(0)
        self.assertTrue(any(r['kind']=='message_sent' for r in sim.records))
        self.assertFalse(any(r['kind']=='message_delivered' for r in sim.records))
        sim.step(1)
        self.assertTrue(any(r['kind']=='message_delivered' for r in sim.records))

    def test_hidden_full_capacity_does_not_remove_attempt(self):
        sim=make('S2',backend=AllAct(),capacity=0);sim.run()
        m=metrics(sim.records)
        self.assertEqual(m['attempts']['join'],8)
        self.assertEqual(m['counts'].get('join_success',0),0)
        self.assertEqual(m['counts']['reason:capacity_waiting'],8)

    def test_capacity_budget_conservation_each_transition(self):
        sim=make('S3',n=30,backend=AllAct());sim.run()
        for r in sim.records:
            if r['kind']!='transition':continue
            s=r['transition']['new_state']
            self.assertEqual(sum(a['budget'] for a in s['agents'].values())+s['revenue'],600)
            self.assertTrue(all(a['budget']>=0 for a in s['agents'].values()))
            for aid,members in s['occupied'].items():self.assertLessEqual(len(members),sim.activities[aid].capacity)

    def test_cancellation_refund_and_waiting_promotion(self):
        sim=make('S2',n=2,backend=CancelOne(),capacity=1)
        # Force syn-00 to register first, then deliver the second notification.
        a=replace(sim.spec.activities[0],initial_informed=('syn-00',))
        spec=replace(sim.spec,activities=(a,),external_events=({'time':1,'kind':'notification','activity':'A','recipients':['syn-01']},))
        sim=Simulator(spec,population(2),CancelOne());sim.run()
        m=metrics(sim.records)
        self.assertEqual(m['counts']['cancel_success'],1)
        self.assertEqual(m['counts']['promote_success'],1)
        self.assertEqual(sim.states['syn-00'].budget,20)
        self.assertEqual(sim.states['syn-01'].budget,18)

    def test_conflicting_activities_settled_in_environment(self):
        spec=scenario('S3',n=4)
        spec=replace(spec,activities=tuple(replace(a,initial_informed=spec.target_ids,capacity=4) for a in spec.activities))
        sim=Simulator(spec,population(4),AllAct());sim.run()
        m=metrics(sim.records)
        self.assertEqual(m['attempts']['join'],8)
        self.assertEqual(m['counts']['reason:schedule_conflict'],4)

    def test_duplicate_registration_rejected(self):
        sim=make('S1',backend=AllAct());sim.step(0);sim.step(1)
        attempt=sim.attempt('syn-00','A','join',2,'test')
        result=sim.admit(attempt)
        self.assertFalse(result.success);self.assertEqual(result.reason,'duplicate')

    def test_budget_failure(self):
        sim=make('S1',backend=AllAct());sim.states['syn-00'].budget=0;sim.initial_money-=20;sim.run()
        self.assertEqual(metrics(sim.records)['counts']['reason:budget'],1)

    def test_invalid_dates_and_schedules_rejected(self):
        spec=scenario('S1')
        for invalid in (replace(spec,start_at='2026-10-01T09:00:00'),replace(spec,activities=(replace(spec.activities[0],end=0),)),replace(spec,activities=(replace(spec.activities[0],capacity=-1),))):
            with self.assertRaises(ValueError):invalid.validate()

    def test_chunk_size_does_not_change_attempts_or_trajectory(self):
        a=make('S3');b=make('S3');a.run(1);b.run(4)
        self.assertEqual(a.records,b.records)

    def test_agent_iteration_order_invariant(self):
        spec=scenario('S3',n=10)
        a=Simulator(spec,population(10),AllAct());b=Simulator(spec,list(reversed(population(10))),AllAct())
        a.run();b.run();self.assertEqual(a.records,b.records)

    def test_lottery_no_persistent_first_agent_advantage(self):
        wins={p.id:0 for p in population(4)}
        for seed in range(120):
            sim=make('S2',n=4,backend=AllAct(),seed=seed,capacity=1);sim.step(0);sim.step(1)
            wins[sim.occupied['A'][0]]+=1
        self.assertTrue(all(12<=n<=48 for n in wins.values()),wins)

    def test_all_metrics_from_trace(self):
        sim=make('S2');sim.run();m=metrics(sim.records)
        joined=sum(r['kind']=='outcome' and r['outcome']['action']=='join' and r['outcome']['success'] for r in sim.records)
        self.assertEqual(m['counts'].get('join_success',0),joined)
        self.assertLessEqual(m['counts'].get('attend_success',0),joined+m['counts'].get('promote_success',0))
        self.assertLessEqual(m['counts'].get('message_viewed',0),m['counts']['message_delivered'])

    def test_replay_state_and_fixed_response_cache(self):
        sim=make('S3');sim.run();self.assertTrue(verify_replay(sim)['cached_response_reexecution'])

    def test_tampering_detected(self):
        sim=make();sim.run();records=deepcopy(sim.records);records[-1]['time']+=1
        with self.assertRaises(ValueError):replay_trace(records)

    def test_response_cache_miss_is_error(self):
        sim=make('S1',backend=ResponseCacheBackend({},'offline_fixture','1'))
        with self.assertRaises(ValueError):sim.run()

    def test_branch_prefix_has_no_future_information(self):
        spec=scenario('S1',n=4)
        spec=replace(spec,activities=(replace(spec.activities[0],initial_informed=('syn-00',)),))
        branch=replace(spec,external_events=({'time':4,'kind':'notification','activity':'A','recipients':['syn-01']},))
        a=Simulator(spec,population(4),AllAct(),stream='paired');b=Simulator(branch,population(4),AllAct(),stream='paired')
        a.run();b.run()
        def prefix(sim):return [{k:v for k,v in r.items() if k not in ('hash','prev_hash')} for r in sim.records if r['kind']!='init' and r['time']<4]
        self.assertEqual(prefix(a),prefix(b));self.assertNotEqual(a.snapshot(),b.snapshot())

    def test_test_event_or_future_feature_rejected_in_fit(self):
        row=dict(event_id='test',time=1,observed_at=1,label=1)
        with self.assertRaises(ValueError):usable_rows([row],{'train'})
        row.update(event_id='train',observed_at=2)
        with self.assertRaises(ValueError):usable_rows([row],{'train'})

    def test_missing_label_is_not_negative(self):
        row=dict(event_id='train',time=1,label=None)
        self.assertEqual(usable_rows([row],{'train'}),[])

    def test_mutually_exclusive_softmax(self):
        result=SharedCalibrator({'join':2}).apply('join',{'yes':.3,'no':.4,'other':.3})
        self.assertAlmostEqual(sum(result.values()),1)
        self.assertAlmostEqual(result['no']/result['other'],4/3)

    def test_split_guards(self):
        s=scenario('S1','x','train')
        with self.assertRaises(ValueError):validate_splits([s,replace(s,split='test')])
        with self.assertRaises(ValueError):validate_splits([scenario('S3','x','train')])

    def test_external_models_disabled_by_default(self):
        for backend in (JevBackend(),StructuredLLMBackend()):
            with self.assertRaises(RuntimeError):backend.probabilities(None)

    def test_jev_verified_call_shape_with_fake_client(self):
        from types import SimpleNamespace
        class Fake:
            def system_one(self,*,state,questions,model):
                assert set(questions)=={'decision'} and model=='jev-1.13.0'
                return SimpleNamespace(model=model,answers={'decision':SimpleNamespace(probabilities={'yes':.6,'no':.4})})
        b=JevBackend(Fake(),lambda **kwargs:kwargs)
        sim=make('S1',backend=b);sim.run();self.assertTrue(sim.responses)

    def test_output_escape_and_frozen_writes_rejected(self):
        with self.assertRaises(ValueError):safe_path(ROOT.parent/'NJU-xianlinSWM/forbidden.json')
        with self.assertRaises(ValueError):write_json('../forbidden.json',{})
        with self.assertRaises(PermissionError):write_json('legacy_snapshot/forbidden.json',{})

    def test_offline_network_and_subprocess_forbidden(self):
        import socket,subprocess
        with self.assertRaises(PermissionError):socket.socket()
        with self.assertRaises(PermissionError):subprocess.run(['never-run'])

    def test_no_original_modules_imported(self):
        source=ROOT.parent/'NJU-xianlinSWM'
        self.assertFalse(any(getattr(m,'__file__',None) and Path(m.__file__).is_relative_to(source) for m in list(sys.modules.values())))

    def test_frozen_snapshot_hashes(self):
        import hashlib
        for row in json.loads((ROOT/'provenance/reuse_manifest.json').read_text(encoding='utf-8')):
            self.assertEqual(hashlib.sha256((ROOT/row['snapshot_path']).read_bytes()).hexdigest(),row['sha256'])

    def test_duplicate_advance_rejected(self):
        sim=make();sim.step(0)
        with self.assertRaises(ValueError):sim.step(0)

if __name__=='__main__':unittest.main()
