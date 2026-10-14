import math
from dataclasses import dataclass, field
from .backends import validate_distribution

@dataclass(frozen=True)
class SharedCalibrator:
    biases: dict = field(default_factory=dict)
    interest_weight: float = 0.0
    version: str = 'shared-logit-v1'
    def apply(self, stage, probabilities, interest=0.5):
        validate_distribution(probabilities)
        # Joint softmax: zero support stays zero; mutually exclusive actions sum to one.
        scores = {k: math.log(v) + (self.biases.get(stage, 0.0) + self.interest_weight*(interest-.5) if k == 'yes' else 0.0)
                  for k,v in probabilities.items() if v > 0}
        mx = max(scores.values()); weights = {k: math.exp(v-mx) for k,v in scores.items()}
        total = sum(weights.values())
        return {k: weights.get(k, 0.0)/total for k in probabilities}

def usable_rows(rows, allowed_events):
    result = []
    for row in rows:
        if row['event_id'] not in allowed_events: raise ValueError('Event split leakage')
        if row.get('observed_at', row['time']) > row['time']: raise ValueError('Future feature leakage')
        if row['label'] is None or not row.get('at_risk', True) or row.get('censored', False): continue
        if row['label'] not in (0,1): raise ValueError('Invalid label')
        result.append(row)
    return result

def local_loss(rows, calibrator):
    if not rows: raise ValueError('No observed labels in risk set')
    losses = []
    for r in rows:
        p = calibrator.apply(r['stage'], {'yes':r['raw_p'],'no':1-r['raw_p']}, r['interest'])['yes']
        p = min(1-1e-12,max(1e-12,p)); y=r['label']
        losses.append(-y*math.log(p)-(1-y)*math.log(1-p))
    return sum(losses)/len(losses)

def fit_grid(rows, train_events, rollout_loss, mode, grid=(-1.0, 0.0, 1.0), regularization=.02):
    """Two shared parameters; deterministic finite search, no differentiability claim."""
    if mode not in ('local','macro','joint'): raise ValueError('Unknown objective')
    rows = usable_rows(rows, set(train_events))
    trials = []
    for join in grid:
        for cancel in grid:
            c=SharedCalibrator({'join':join,'cancel':cancel})
            loc=local_loss(rows,c) if mode != 'macro' else None
            macro=rollout_loss(c) if mode != 'local' else None
            reg=regularization*(join*join+cancel*cancel)
            objective=(loc or 0)+(macro or 0)+reg
            trials.append(dict(biases=c.biases, local_nll=loc, trajectory_mae=macro, penalty=reg, objective=objective))
    best=min(trials,key=lambda r:(r['objective'],sum(v*v for v in r['biases'].values())))
    return SharedCalibrator(best['biases']), trials
