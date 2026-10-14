"""Offline SSA v2 response checks; not a forecaster, endpoint, or submission client.

Contract inspected at Social-Atoms/social-sim-arena commit
7002f435a89bd42ec0cc55d5e05dcfa1ad9c7f4c. No network or credentials.
"""
from datetime import datetime, timezone
import json
import math


def _distribution(value):
    if not isinstance(value, dict) or set(value) != {'mean', 'sd'}:
        raise ValueError('A normal forecast requires mean and sd only')
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
           for v in value.values()):
        raise ValueError('Forecast parameters must be finite numbers')
    if not 0 < value['sd'] <= 1e9:
        raise ValueError('sd must be positive and at most 1e9')


def response(request, forecast, *, now=None):
    """Validate supported shape against the supplied question; return JSON data.

    Caller supplies a domain-trained forecast. Never derive live forecasts from
    the synthetic campus cache. Network authentication/idempotency are outside
    this offline formatting helper; this is not a complete JSON Schema validator.
    """
    if request.get('schema_version') != 'ssa-agent-api-v2':
        raise ValueError('Unsupported request version')
    if not isinstance(request.get('request_id'), str) or not 8 <= len(request['request_id']) <= 160:
        raise ValueError('Invalid request_id')
    question = request['round']
    if any(k not in question for k in ['round_id', 'board_id', 'target_type', 'question', 'unit', 'lock_at', 'context']):
        raise ValueError('Incomplete round envelope')
    deadline = datetime.fromisoformat(question['lock_at'].replace('Z', '+00:00'))
    if deadline.tzinfo is None:
        raise ValueError('Deadline must include timezone')
    now = datetime.now(timezone.utc) if now is None else now
    if now.tzinfo is None or now >= deadline:
        raise ValueError('A timezone-aware time before the supplied deadline is required')
    kind = question['target_type']
    if kind == 'continuous_normal':
        _distribution(forecast)
    elif kind == 'profile_energy':
        cells = question.get('cells', [])
        if len(cells) < 2 or len(set(cells)) != len(cells):
            raise ValueError('Profile requires distinct declared cells')
        if set(forecast) != {'profile'} or set(forecast['profile']) != set(cells):
            raise ValueError('Profile must contain exactly the requested cells')
        for value in forecast['profile'].values():
            _distribution(value)
    elif kind == 'ranking_list':
        spec = question.get('ranking', {})
        ranking = forecast.get('ranking')
        if set(forecast) != {'ranking'} or not isinstance(ranking, list):
            raise ValueError('Ranking must be a list')
        if any(not isinstance(s, str) or not 1 <= len(s) <= 256 for s in ranking):
            raise ValueError('Invalid ranking item')
        if not 2 <= len(ranking) <= 50 or len(ranking) != spec.get('length') or len(set(ranking)) != len(ranking):
            raise ValueError('Ranking length/uniqueness mismatch')
        if spec.get('items') and set(ranking) != set(spec['items']):
            raise ValueError('Fixed-basket ranking must be a permutation of the given items')
    else:
        raise NotImplementedError('This offline helper supports scalar, profile and ranking only')
    # JSON round-trip detaches the return value and refuses NaN/Infinity.
    return json.loads(json.dumps({'schema_version': 'ssa-agent-api-v2', 'forecast': forecast}, allow_nan=False))


def normal_crps(mean, sd, observed):
    """Analytic normal CRPS for local unit checks, not an official arena score."""
    _distribution({'mean': mean, 'sd': sd})
    if isinstance(observed, bool) or not math.isfinite(observed):
        raise ValueError('Observed value must be finite')
    z = (observed-mean)/sd
    phi = math.exp(-z*z/2)/math.sqrt(2*math.pi)
    cdf = (1+math.erf(z/math.sqrt(2)))/2
    return sd*(z*(2*cdf-1)+2*phi-1/math.sqrt(math.pi))
