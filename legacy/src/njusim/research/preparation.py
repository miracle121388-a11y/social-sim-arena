"""Small synthetic integration check against the unchanged V1 kernel, not a V2 benchmark."""
from dataclasses import asdict
from itertools import combinations, product
import math
from ..fixtures import scenario, population, stage_rows
from ..backends import OfflineFixtureBackend
from ..calibration import SharedCalibrator, local_loss
from ..experiments import simulate
from ..metrics import metrics, trajectory_mae
from ..io import ROOT, sha, write_json
from .hypotheses import Hypothesis, compatible
from .acquisition import composition_score, enumeration_score, update_weights, disagreement
from .probes import ProbeKey, ProbeCache
from .evidence import Query, QueryPool
from .evaluator import SyntheticOracle

def aligned(sim):
    rows=metrics(sim.records)['trajectory']
    result=[]
    for t in range(sim.spec.horizon):
        prior=[r for r in rows if r['time']<=t]
        row=prior[-1] if prior else dict(registered=0,waiting=0,attended=0)
        result.extend(row[k] for k in ('registered','waiting','attended'))
    return result

def run(folder):
    seeds=(11,12,13)
    n=12
    train=scenario('S2','v2-integration-train','train',n=n,capacity=2)
    probes=(scenario('S1','v2-integration-probe-open','probe',n=n),
            scenario('S2','v2-integration-probe-limited','probe',n=n,capacity=5))
    people=population(n)
    backend=OfflineFixtureBackend()
    plan=dict(kind='synthetic_preparation_not_benchmark',seeds=seeds,
              train=asdict(train),probes=[asdict(p) for p in probes],
              grid=[-1.0,0.0,1.0],epsilon_process=1.5,epsilon_rollout=.15,
              initial_evidence='first two initial-time view decisions from synthetic teacher seed 101',
              query_scope='remaining initial-time view opportunities only; conditional independence is a fixture assumption',
              budget_units=2,target='registered/waiting/attended at every logical minute',
              scale=n,truth='OfflineFixtureBackend with zero calibration biases',
              limitation='No sealed-test evaluation, no cross-domain validity, no real data or model calls')
    write_json(folder/'frozen_preparation_plan.json',plan)
    teacher=simulate(train,backend,seed=101,people=people)
    eligible=[r for r in stage_rows(teacher) if r['stage']=='view' and r['time']==1]
    if len(eligible)<4:raise ValueError('Insufficient complete initial opportunities')
    initial=eligible[:2]
    truth=[simulate(train,backend,seed=s,people=people) for s in seeds]
    candidates=[];train_vectors={};probe_vectors={};cache=ProbeCache();cache_records=[]
    engine_hash=sha({str(p.relative_to(ROOT)):sha(p.read_text(encoding='utf-8'))
                     for p in (ROOT/'src/njusim').glob('*.py') if p.name not in ('proposal_pdf.py','submission_pdf.py')})
    schema=tuple(f'{spec.event_id}/{t}/{k}' for spec in probes for t in range(spec.horizon)
                 for k in ('registered','waiting','attended'))
    for ix,(view,join) in enumerate(product(plan['grid'],repeat=2)):
        calibrator=SharedCalibrator({'view':view,'join':join})
        runs=[simulate(train,backend,calibrator,seed=s,people=people) for s in seeds]
        loss=math.fsum(trajectory_mae(metrics(a.records)['trajectory'],metrics(b.records)['trajectory'],n)
                       for a,b in zip(runs,truth))/len(seeds)
        candidate=Hypothesis(f'h{ix}','native-stage-residual',(('view',view),('join',join)),
                             local_loss(initial,calibrator),loss,(train.event_id,),'declared-3x3-grid')
        candidates.append(candidate)
        train_vectors[candidate.id]=tuple(math.fsum(aligned(a)[j] for a in runs)/len(runs)/n
                                         for j in range(3*train.horizon))
        draws=[];tails=[]
        for seed in seeds:
            vector=[];seed_tails=[]
            # One candidate fixed for each ENTIRE rollout, with the same seed stream for fair comparisons.
            for probe in probes:
                sim=simulate(probe,backend,calibrator,seed=seed,people=people)
                vector.extend(aligned(sim));seed_tails.append(sim.records[-1]['hash'])
            draws.append(vector);tails.append(seed_tails)
        key=ProbeKey(candidate.fingerprint,sha((backend.name,backend.version)),engine_hash,
                     sha([asdict(p) for p in people]),sha(plan['probes']),schema,(n,)*len(schema),seeds,'event-id:rep-seed-v1')
        mean,noise,repeats=cache.put(key,draws)
        probe_vectors[candidate.id]=mean
        cache_records.append(dict(candidate_id=candidate.id,key=asdict(key),key_hash=key.digest,
                                  expectation=mean,simulation_variance=noise,repeats=repeats,tail_hashes=tails))
    hs=compatible(candidates,train_event_ids=[train.event_id],epsilon_process=plan['epsilon_process'],epsilon_rollout=plan['epsilon_rollout'])
    if len(hs.candidates)<2:raise ValueError('No compatible alternatives found')
    pairs=[]
    for a,b in combinations(hs.candidates,2):
        historical=math.fsum(abs(x-y) for x,y in zip(train_vectors[a.id],train_vectors[b.id]))/len(train_vectors[a.id])
        future=math.fsum((x-y)**2 for x,y in zip(probe_vectors[a.id],probe_vectors[b.id]))
        if historical <= .08 and future > 1e-6:
            pairs.append(dict(left=a.id,right=b.id,historical_normalized_mae=historical,probe_squared_distance=future))
    if not pairs:raise ValueError('No constructed near-history/different-probe pair; do not assert success')
    queries=[Query(r['evidence_id'],train.event_id,'view',1,r['evidence_id'],r['evidence_id']) for r in eligible[2:]]
    oracle=SyntheticOracle({r['evidence_id']:r['label'] for r in eligible[2:]})
    pool=QueryPool(queries,train_event_ids=[train.event_id],budget=2)
    weights=hs.weights;targets=[probe_vectors[h.id] for h in hs.candidates];reveals=[]
    for _ in range(2):
        token=pool.history_token
        # The initial-time constant backend makes probabilities conditionally independent given theta.
        # Future adapters must recompute from pool.revealed, not reuse these probabilities blindly.
        options=[]
        for query in queries:
            if query.id in {r.query_id for r in pool.revealed}:continue
            p=[SharedCalibrator(dict(h.parameters)).apply('view',{'yes':.88,'no':.12})['yes'] for h in hs.candidates]
            score=composition_score(weights,p,targets,query.cost)
            reference=enumeration_score(weights,p,targets,query.cost)
            if not math.isclose(score,reference,rel_tol=1e-9,abs_tol=1e-11):
                raise AssertionError('Binary score identity failed')
            options.append((score,query.id,p,reference))
        score,qid,p,ref=max(options,key=lambda row:(row[0],row[1]))
        before=disagreement(weights,targets)
        reveal=pool.reveal(qid,history_token=token,read_label=oracle.read_label)
        weights=update_weights(weights,p,reveal.label)
        reveals.append(dict(reveal=asdict(reveal),history_token=token,expected_reduction_per_cost=score,
                            explicit_reference=ref,disagreement_before=before,
                            realized_disagreement_after=disagreement(weights,targets),
                            weights=weights,effective_candidates=1/sum(w*w for w in weights)))
    write_json(folder/'candidates.json',dict(candidates=[asdict(h) for h in candidates],
               retained=[h.id for h in hs.candidates],initial_weights=hs.weights,weight_kind=hs.weight_kind))
    write_json(folder/'probe_cache.json',cache_records)
    write_json(folder/'equifinality.json',dict(provenance='synthetic',pairs=pairs,
               criterion='Mean normalized full training trajectory distance <= 0.08; different probe expectations; constructed example only'))
    write_json(folder/'revealed_evidence.json',dict(initial=initial,paid=reveals,cost_units=pool.spent,
               note='Finite-mixture update for a synthetic conditional-independent initial opportunity model; not a real posterior'))
    return dict(status='tested_synthetic',candidates=len(candidates),retained=len(hs.candidates),ambiguous_pairs=len(pairs),
                native_rollouts=1+len(seeds)+len(candidates)*len(seeds)*(1+len(probes)),
                reveals=pool.spent,real_events=0,external_calls=0,full_v2_benchmark=False)
