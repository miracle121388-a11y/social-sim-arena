from dataclasses import dataclass, field, asdict
from datetime import datetime
import math

STAGES = ('view', 'join', 'share', 'cancel', 'attend')

@dataclass(frozen=True)
class Activity:
    id: str
    start: int
    end: int
    capacity: int
    price: int
    initial_informed: tuple[str, ...]
    topic: str = 'campus'
    def validate(self, horizon):
        if type(self.start) is not int or type(self.end) is not int: raise ValueError('Activity boundaries must be logical integer minutes')
        if not self.id or not 0 < self.start < self.end <= horizon: raise ValueError('Invalid activity window')
        if type(self.capacity) is not int or self.capacity < 0 or type(self.price) is not int or self.price < 0: raise ValueError('Invalid resource')

@dataclass(frozen=True)
class EventSpec:
    event_id: str
    scenario: str
    start_at: str
    horizon: int
    activities: tuple[Activity, ...]
    mechanisms: tuple[str, ...]
    target_ids: tuple[str, ...]
    external_events: tuple[dict, ...] = ()
    allowed_actions: tuple[str, ...] = ('view', 'join', 'share', 'cancel', 'attend')
    evaluation_targets: tuple[str, ...] = ('stage_brier', 'stage_nll', 'occupancy_trajectory_mae')
    provenance: str = 'synthetic'
    split: str = 'smoke'
    def validate(self):
        if datetime.fromisoformat(self.start_at).utcoffset() is None: raise ValueError('Timezone required')
        if self.provenance != 'synthetic': raise ValueError('Real data requires approved ingestion workflow')
        if type(self.horizon) is not int or self.horizon < 1: raise ValueError('Invalid horizon')
        if len(set(self.target_ids)) != len(self.target_ids): raise ValueError('Duplicate persona')
        if not self.target_ids or not self.activities: raise ValueError('Empty event/population')
        ids = [a.id for a in self.activities]
        if len(set(ids)) != len(ids): raise ValueError('Duplicate activity')
        if not set(self.mechanisms) <= {'notification', 'capacity', 'waiting', 'cancellation', 'peer', 'conflict'}: raise ValueError('Unknown mechanism')
        if not set(self.allowed_actions) <= set(STAGES): raise ValueError('Unknown action')
        for a in self.activities:
            a.validate(self.horizon)
            if not set(a.initial_informed) <= set(self.target_ids): raise ValueError('Unknown recipient')
        for e in self.external_events:
            if set(e) != {'time', 'kind', 'activity', 'recipients'} or e['kind'] != 'notification': raise ValueError('Unsupported external event')
            if not 0 <= e['time'] < self.horizon or e['activity'] not in ids or not set(e['recipients']) <= set(self.target_ids): raise ValueError('Invalid external event')
    @classmethod
    def from_dict(cls, d):
        data = dict(d)
        data['activities'] = tuple(Activity(**{**a, 'initial_informed': tuple(a['initial_informed'])}) for a in d['activities'])
        for k in ('mechanisms', 'target_ids', 'external_events', 'allowed_actions', 'evaluation_targets'):
            if k in data: data[k] = tuple(data[k])
        spec = cls(**data); spec.validate(); return spec

@dataclass(frozen=True)
class Persona:
    id: str
    interest: float
    contacts: tuple[str, ...]
    provenance: str = 'synthetic'
    def __post_init__(self):
        if not math.isfinite(self.interest) or not 0 <= self.interest <= 1: raise ValueError('Invalid interest')
        if self.provenance != 'synthetic': raise ValueError('Fixture personas must be synthetic')

@dataclass
class AgentState:
    budget: int = 20
    schedule: list = field(default_factory=list)
    goal: str = 'Choose locally known campus activities'
    known: dict = field(default_factory=dict)
    inbox: list = field(default_factory=list)
    memory: list = field(default_factory=list)
    registrations: list = field(default_factory=list)
    waiting: list = field(default_factory=list)
    attempted: list = field(default_factory=list)
    considered: list = field(default_factory=list)

@dataclass(frozen=True)
class Observation:
    agent_id: str
    time: int
    activity: str
    stage: str
    sources: tuple[dict, ...]
    visible_activity: dict
    own_state: dict
    interest: float
    window_minutes: int = 1

@dataclass(frozen=True)
class DecisionProposal:
    stage: str
    raw: dict
    calibrated: dict
    selected: str
    backend: str
    version: str
    response_ref: str
    random_key: tuple
    draw: float
    window_minutes: int = 1

@dataclass(frozen=True)
class ActionAttempt:
    id: str
    agent: str
    activity: str
    action: str
    time: int
    decision_id: str

@dataclass(frozen=True)
class Outcome:
    attempt_id: str
    agent: str
    activity: str
    action: str
    success: bool
    reason: str
    budget_delta: int = 0

@dataclass(frozen=True)
class TransitionRecord:
    time: int
    old_state: dict
    new_state: dict
    evidence_ids: tuple[str, ...]

def plain(obj): return asdict(obj)
