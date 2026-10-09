"""Backends receive only an immutable, copied local observation, never the world."""
from dataclasses import asdict
import math
from typing import Protocol
from .io import sha

def validate_distribution(p):
    if not p or any(not math.isfinite(v) or not 0 <= v <= 1 for v in p.values()) or abs(sum(p.values())-1) > 1e-9:
        raise ValueError('Invalid probability distribution')
    return dict(p)

class DecisionBackend(Protocol):
    name: str
    version: str
    def probabilities(self, observation): ...

class OfflineFixtureBackend:
    name = 'offline_fixture'; version = '1'
    def probabilities(self, observation):
        p = {'view': .88, 'join': .76, 'share': .62, 'cancel': .22, 'attend': .91}[observation.stage]
        return {'yes': p, 'no': 1-p}

class SimpleStatisticalBackend:
    name = 'simple_statistical'; version = '1-unfitted-synthetic'
    def probabilities(self, observation):
        intercept = {'view': 1.0, 'join': -.25, 'share': -.6, 'cancel': -1.6, 'attend': 1.7}[observation.stage]
        p = 1 / (1 + math.exp(-(intercept + 1.3 * (observation.interest-.5))))
        return {'yes': p, 'no': 1-p}

class ResponseCacheBackend:
    name = 'response_cache'; version = '1'
    def __init__(self, responses, original_name, original_version):
        self.responses = responses; self.name = original_name; self.version = original_version
    def probabilities(self, observation):
        key = sha(asdict(observation))
        if key not in self.responses: raise ValueError('Missing frozen response; live fallback forbidden')
        return validate_distribution(self.responses[key])

class JevBackend:
    """Dependency-injected official SDK seam. No keys, transport, or network by default.

    Call shape checked against source jev.py and TypeSafe official Choice docs.
    An explicitly authorized caller must construct the SDK client and Choice type.
    This plugin was tested with a fake client; live model behavior is unvalidated.
    """
    name = 'jev'; version = 'jev-1.13.0/typesafe-sdk-0.7.1'
    def __init__(self, client=None, choice_type=None):
        self.client, self.choice_type = client, choice_type
    def probabilities(self, observation):
        if self.client is None or self.choice_type is None: raise RuntimeError('Live Jev disabled: authorized client and budget required')
        question = self.choice_type(instructions=f'Probability of {observation.stage} within this one opportunity.', criteria={'yes': 'take action', 'no': 'do not take action'})
        result = self.client.system_one(state=asdict(observation), questions={'decision': question}, model='jev-1.13.0')
        answer = result.answers['decision']
        if result.model != 'jev-1.13.0': raise ValueError('Unexpected Jev model')
        return validate_distribution(answer.probabilities)

class StructuredLLMBackend:
    name = 'structured_llm'; version = 'injected-v1'
    def __init__(self, authorized_transport=None): self.transport = authorized_transport
    def probabilities(self, observation):
        if self.transport is None: raise RuntimeError('Live LLM disabled: authorized transport and budget required')
        return validate_distribution(self.transport(asdict(observation)))
