from copy import deepcopy
from dataclasses import asdict
from .fixtures import population, scenario, stage_rows
from .kernel import Simulator
from .calibration import SharedCalibrator, fit_grid
from .backends import OfflineFixtureBackend, SimpleStatisticalBackend, ResponseCacheBackend
from .metrics import metrics, trajectory_mae, probability_scores, replay_trace
from .io import ROOT, write_json, safe_path, sha
import csv
import json
import platform
import statistics
import subprocess

def validate_splits(specs):
    ids=[s.event_id for s in specs]
    if len(ids)!=len(set(ids)):raise ValueError('Events cannot cross splits')
    if any(s.scenario=='S3' and s.split in ('train','dev') for s in specs):raise ValueError('Held-out composition leaked')
    train=[s.start_at for s in specs if s.split=='train'];dev=[s.start_at for s in specs if s.split=='dev'];test=[s.start_at for s in specs if s.split=='test']
    if train and dev and max(train)>=min(dev):raise ValueError('Train/dev chronology overlap')
    if dev and test and max(dev)>=min(test):raise ValueError('Dev/test chronology overlap')

def simulate(spec, backend, calibrator=None, seed=7, people=None):
    people=people or population(prefix='new' if spec.target_ids[0].startswith('new') else 'syn')
    sim=Simulator(spec,people,backend,calibrator,seed=seed,stream=f'{spec.event_id}:rep-{seed}')
    sim.run(); return sim

def verify_replay(sim):
    state=replay_trace(sim.records)
    assert state==sim.snapshot()
    init=sim.records[0]
    cache=ResponseCacheBackend(sim.responses,sim.backend.name,sim.backend.version)
    clone=Simulator(sim.spec,list(sim.people.values()),cache,sim.calibrator,seed=sim.seed,stream=sim.stream,initial_states=init['state']['agents'])
    clone.run()
    assert clone.records==sim.records, 'Cached-response re-execution differs'
    return dict(state_reduction=True,cached_response_reexecution=True,tail_hash=sim.records[-1]['hash'])

def smoke(folder):
    result=[]
    for name in ('S1','S2','S3'):
        spec=scenario(name);sim=simulate(spec,OfflineFixtureBackend())
        sim.save(folder/name)
        replay=verify_replay(sim);write_json(folder/name/'replay.json',replay)
        write_json(f'configs/{name}.json',asdict(spec))
        m=metrics(sim.records)
        result.append(dict(scenario=name,agents=len(sim.people),records=len(sim.records),counts=m['counts'],replay=replay))
    write_json('data/fixtures/personas.json',[asdict(p) for p in population()])
    write_json(folder/'smoke_summary.json',result)
    return result

def research_pilot(folder):
    """Synthetic DGP known only to fixture generator, never training features.

    Train: independent S1/S2 events. Dev: later S2. Test: later S1/S2 and
    unseen S3, including entirely new identities. Seeds are repeats, not events.
    """
    specs=[scenario('S1','train-01','train',date='2026-09-01'),scenario('S2','train-02','train',date='2026-09-02'),
           scenario('S2','dev-03','dev',date='2026-09-03',capacity=7),
           scenario('S1','test-04','test',date='2026-09-04'),scenario('S2','test-05','test',date='2026-09-05',capacity=6),
           scenario('S3','test-comp-06','test',date='2026-09-06'),scenario('S3','test-new-07','test',prefix='new',date='2026-09-07')]
    validate_splits(specs)
    write_json(folder/'split_manifest.json',[asdict(s) for s in specs])
    # Synthetic ground truth, not human behavior: a deliberately selected DGP.
    truth_cal=SharedCalibrator({'join':-.8,'cancel':.7})
    truth={}; rows={}; targets={}
    for s in specs:
        sim=simulate(s,OfflineFixtureBackend(),truth_cal,seed=101)
        truth[s.event_id]=sim;rows[s.event_id]=stage_rows(sim);targets[s.event_id]=metrics(sim.records)['trajectory']
        sim.save(folder/'synthetic_truth'/s.event_id)
    write_json(folder/'synthetic_labels.json',[row for group in rows.values() for row in group])
    train=[s for s in specs if s.split=='train']; dev=[s for s in specs if s.split=='dev']; tests=[s for s in specs if s.split=='test']
    write_json(folder/'data_provenance.json',dict(kind='synthetic',dgp=asdict(truth_cal),teacher_seed=101,real_events=0,observability='All simulated decisions are observable only in fixture; real labels may be missing'))
    output=[];frozen=[]
    for backend in (OfflineFixtureBackend(),SimpleStatisticalBackend()):
        # One-step uses teacher history, recomputes each candidate backend's raw probabilities.
        backend_rows={}
        from .contracts import Observation
        for eid,rs in rows.items():
            backend_rows[eid]=[]
            for row in rs:
                d=deepcopy(row['features']);d['sources']=tuple(d['sources'])
                raw=backend.probabilities(Observation(**d))
                backend_rows[eid].append({**row,'raw_p':raw['yes']})
        train_rows=[r for s in train for r in backend_rows[s.event_id]]
        def macro_loss(c, events=train):
            return statistics.mean(trajectory_mae(metrics(simulate(s,backend,c,seed=11).records)['trajectory'],targets[s.event_id],30) for s in events)
        methods={'uncalibrated':SharedCalibrator()}
        for mode in ('local','macro','joint'):
            candidates=[]
            for reg in (0.0,.02):
                c,trials=fit_grid(train_rows,[s.event_id for s in train],macro_loss,mode,regularization=reg)
                dev_score=statistics.mean(probability_scores(backend_rows[s.event_id],c)['nll']+macro_loss(c,[s]) for s in dev)
                candidates.append((dev_score,c,reg,trials))
            score,c,reg,trials=min(candidates,key=lambda v:(v[0],sum(x*x for x in v[1].biases.values())))
            methods[mode]=c
            write_json(folder/'fits'/f'{backend.name}-{mode}.json',dict(train_events=[s.event_id for s in train],dev_events=[s.event_id for s in dev],mode=mode,regularization=reg,selected=asdict(c),trials=trials,dev_score=score,objective='mean stage NLL + population-normalized mean absolute occupancy/wait/attendance trajectory error + L2; weights 1/1; irrelevant term omitted'))
        # Freeze model specification before iterating over test outcomes.
        model_manifest={m:asdict(c) for m,c in methods.items()}
        frozen_hash=sha(model_manifest);frozen.append(dict(backend=backend.name,model_manifest=model_manifest,hash=frozen_hash))
        write_json(folder/'fits'/f'{backend.name}-frozen.json',frozen[-1])
        for name,c in methods.items():
            for s in tests:
                rollout_errors=[];attendance=[];tails=[]
                for seed in (21,22,23):
                    sim=simulate(s,backend,c,seed=seed)
                    sim.save(folder/'rollouts'/backend.name/name/s.event_id/f'seed-{seed}')
                    met=metrics(sim.records);rollout_errors.append(trajectory_mae(met['trajectory'],targets[s.event_id],30));attendance.append(met['counts'].get('attend_success',0));tails.append(sim.records[-1]['hash'])
                one=probability_scores(backend_rows[s.event_id],c)
                stages={stage:probability_scores([r for r in backend_rows[s.event_id] if r['stage']==stage],c) for stage in ('view','join','share','cancel','attend')}
                output.append(dict(backend=backend.name,method=name,event_id=s.event_id,scenario=s.scenario,population_regime='new_people_new_event' if s.event_id=='test-new-07' else 'same_people_new_event',provenance='synthetic',model_hash=frozen_hash,one_step=one,stage_scores=stages,free_rollout_normalized_mae=statistics.mean(rollout_errors),attendance_seed_range=[min(attendance),max(attendance)],interval_kind='min-max of 3 simulation seeds; NOT empirical CI',seeds=[21,22,23],tail_hashes=tails))
    write_json(folder/'evaluation.json',output)
    write_json(folder/'baseline_status.json',{
        'B0':{'status':'missing','reason':'Only frozen sampling module parity, no full legacy engine/population/services reproduced'},
        'B1':{'status':'tested_synthetic','backend':'simple_statistical','fitted_on_real_data':False},
        'B2':{'status':'missing','reason':'Jev/LLM plugin exists, but no API authorization or real model execution'},
        'B3_B4_Ours':{'status':'tested_synthetic','mapping':{'local':'B3','macro':'B4','joint':'Ours candidate'},'backends':['offline_fixture','simple_statistical'],'limitation':'Engineering stand-ins, not live-model evidence'}})
    return dict(rows=len(output),synthetic_events=len(specs),test_events=len(tests),real_events=0,external_calls=0)

def append_registry(batch,kind,summary):
    path=safe_path('experiments/registry.csv');exists=path.exists()
    with path.open('a',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['batch','kind','status','provenance','artifact','summary'])
        if not exists:writer.writeheader()
        writer.writerow(dict(batch=batch,kind=kind,status='tested_synthetic',provenance='synthetic',artifact=f'artifacts/{batch}',summary=json.dumps(summary,ensure_ascii=False)))
