"""Path-C wrapper of the NEW native research kernel, not of the old campus engine.

Pinned SocioVerse2 commit: 9c3ac774816511c121184ca11f539dc398ba1544.
Each official step invokes exactly one native minute. Native observations and
memory remain authoritative. The official panel is a projection; the sidecar is
the complete replay artifact. Core warm-start and micro-rounds >1 are unsupported.
"""
from dataclasses import asdict
from copy import deepcopy
from socioverse.abc.environment import EnvironmentProvider
from socioverse.abc.population import PopulationProvider
from socioverse.abc.decision import DecisionModel
from socioverse.abc.trajectory import MetricCollector
from socioverse.schemas.runtime import Action, Observation
from socioverse.schemas.population import Persona, PopulationBundle, InteractionStructure
from socioverse.schemas.environment import EnvironmentBundle
from socioverse.engine.loop import LongitudinalSimulator
from socioverse.engine.registry import register
from socioverse.io.duckdb_store import DuckDbTrajectoryStore
from njusim.kernel import Simulator
from njusim.backends import OfflineFixtureBackend
from njusim.metrics import metrics
from njusim.io import safe_path

class Session:
    def __init__(self,spec,people,backend=None,calibrator=None):
        self.spec,self.people,self.backend,self.calibrator=spec,people,backend or OfflineFixtureBackend(),calibrator
        self.native=None;self.pending_t=None;self.last_applied=0

@register('environment','nju.env')
class NjuEnvironment(EnvironmentProvider):
    def __init__(self,session):
        self.session=session;self.bundle=EnvironmentBundle(study_id='nju_compositional_simulation',provider_ref='nju.env')
    def reset(self,seed):
        s=self.session
        s.native=Simulator(s.spec,s.people,s.backend,s.calibrator,seed=seed,stream=f'{s.spec.event_id}:rep-{seed}')
        s.native.step(0);s.pending_t=None;s.last_applied=0
    def advance_to(self,t):
        if t!=self.session.native.clock+1 or self.session.pending_t is not None:raise ValueError('Duplicate/skipped official advancement')
        self.session.pending_t=t
        return []  # Native exogenous events are recorded in the complete sidecar.
    def observe_batch(self,agent_ids,t,round_idx=0):
        if round_idx!=0:raise ValueError('Only one outer round supported')
        return [Observation(agent_id=p,step=t,local_physical={'budget':self.session.native.states[p].budget},
                            local_information={'known':deepcopy(self.session.native.states[p].known)}) for p in agent_ids]
    def apply(self,actions):
        s=self.session
        if any(a.source=='replay' for a in actions):raise ValueError('Use native sidecar replay; official warm-start unsupported')
        if s.pending_t is None or s.last_applied==s.pending_t or s.native.clock!=s.pending_t:raise ValueError('Duplicate/missing native transition')
        if {a.agent_id for a in actions}!=set(s.native.people) or any(a.step!=s.pending_t for a in actions):raise ValueError('Action coverage mismatch')
        s.last_applied=s.pending_t;s.pending_t=None
    def agent_state(self,agent_id):
        s=self.session.native.states[agent_id]
        return {'budget':s.budget,'registered':len(s.registrations),'waiting':len(s.waiting),'known':len(s.known),'provenance':'synthetic'}
    def snapshot(self):return self.session.native.snapshot()

@register('population','nju.pop')
class NjuPopulation(PopulationProvider):
    def __init__(self,session):
        self.session=session
        edges=[(p.id,q) for p in session.people for q in p.contacts]
        self.bundle=PopulationBundle(study_id='nju_compositional_simulation',provider_ref='nju.pop',interaction=InteractionStructure(kind='explicit_network',edges=edges))
    def build(self,seed):
        return [Persona(agent_id=p.id,attributes={'interest':p.interest,'provenance':'synthetic'},group_key='synthetic-fixture') for p in self.session.people]
    def neighbors(self,agent_id):return list(next(p.contacts for p in self.session.people if p.id==agent_id))

@register('decision','nju.decision')
class NjuDecision(DecisionModel):
    def __init__(self,session):self.session=session
    def decide_batch(self,obs,memories):
        s=self.session
        if not obs or {o.step for o in obs}!={s.pending_t} or {o.agent_id for o in obs}!=set(s.native.people):raise ValueError('Invalid official batch')
        s.native.step(s.pending_t)
        # Explicit legacy seam: the encapsulated kernel executes its own local phases.
        # No other agent's observation is passed to its decision backend.
        return [Action(agent_id=o.agent_id,step=o.step,kind='native_tick',source='rule',payload={'sidecar_tail_hash':s.native.records[-1]['hash']}) for o in obs]

@register('collector','nju.collector')
class NjuCollector(MetricCollector):
    def collect(self,env,actions,t):
        row=metrics(env.session.native.records)['trajectory'][-1]
        return {k:row[k] for k in ('registered','waiting','attended','revenue','budget_total')}
    def columns(self):return ['registered','waiting','attended','revenue','budget_total']

def build_adapter(spec,people,db_path,*,seed=7,backend=None,calibrator=None,interaction_rounds=1,warm_start=None):
    if interaction_rounds!=1 or warm_start is not None:raise ValueError('Native sidecar required; unsupported Core branch/multi-round replay')
    path=safe_path(db_path)
    if path.exists():raise FileExistsError('Never overwrite an existing research database')
    session=Session(spec,people,backend,calibrator)
    env=NjuEnvironment(session)
    outer=LongitudinalSimulator(env=env,population=NjuPopulation(session),decision=NjuDecision(session),
        store=DuckDbTrajectoryStore(path,study_id='nju_compositional_simulation'),collector=NjuCollector(),n_steps=spec.horizon,seed=seed,
        interaction_rounds=1,study_id='nju_compositional_simulation')
    return outer,session
