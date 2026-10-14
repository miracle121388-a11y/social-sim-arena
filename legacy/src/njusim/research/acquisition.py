"""Binary finite-mixture scores; z is a fixed candidate-conditional expectation.

Queries must not directly change the target state. Conditional probabilities
must be recomputed after reveals; this module does not infer missing histories.
"""
import math
from .hypotheses import normalized

def prepare(weights, probabilities, targets, cost=1.0):
    w = normalized(weights)
    p = tuple(float(x) for x in probabilities)
    z = tuple(tuple(float(x) for x in row) for row in targets)
    if len(p) != len(w) or len(z) != len(w) or not z or not z[0]:
        raise ValueError("Candidate axes must align")
    if any(not math.isfinite(x) or not 0 <= x <= 1 for x in p):
        raise ValueError("Invalid Bernoulli probability")
    if any(len(row) != len(z[0]) or any(not math.isfinite(x) for x in row) for row in z):
        raise ValueError("Invalid target matrix")
    if not math.isfinite(cost) or cost <= 0:
        raise ValueError("Cost must be finite and positive")
    return w, p, z, float(cost)

def mean_target(weights, targets):
    # Translation around one target reduces loss of precision for large offsets.
    return tuple(targets[0][j] + math.fsum(w*(row[j]-targets[0][j]) for w,row in zip(weights,targets))
                 for j in range(len(targets[0])))

def disagreement(weights, targets):
    w, _, z, _ = prepare(weights, [0.5]*len(weights), targets)
    mu = mean_target(w, z)
    return math.fsum(wk*math.fsum((x-m)**2 for x,m in zip(row,mu)) for wk,row in zip(w,z))

def update_weights(weights, probabilities, label):
    if type(label) is not int or label not in (0,1):
        raise ValueError("Expected an observed binary label")
    w, p, _, _ = prepare(weights, probabilities, [[0]]*len(weights))
    likelihood = p if label else tuple(1-x for x in p)
    mass = tuple(a*b for a,b in zip(w,likelihood))
    if math.fsum(mass) == 0:
        raise ValueError("Evidence impossible under every active candidate; model mismatch")
    return normalized(mass)

def composition_score(weights, probabilities, targets, cost=1.0):
    w,p,z,cost = prepare(weights, probabilities, targets, cost)
    if all(x == p[0] for x in p):
        return 0.0
    if math.fsum(a*b for a,b in zip(w,p)) > 0.5:
        p = tuple(1-x for x in p)  # stable rare-outcome calculation near one
    pb = math.fsum(a*b for a,b in zip(w,p))
    if pb == 0 or pb == 1:
        return 0.0
    mu = mean_target(w,z)
    covariance = [math.fsum(wk*(pk-pb)*(row[j]-mu[j]) for wk,pk,row in zip(w,p,z))
                  for j in range(len(mu))]
    root = math.sqrt(pb)*math.sqrt(1-pb)
    return math.fsum((a/root)**2 for a in covariance)/cost

def enumeration_score(weights, probabilities, targets, cost=1.0):
    """Independent, explicit two-outcome reference; cancellation near zero expected."""
    w,p,z,cost = prepare(weights, probabilities, targets, cost)
    pb = math.fsum(a*b for a,b in zip(w,p))
    before = disagreement(w,z)
    after = 0.0
    for y, mass in ((1,pb),(0,1-pb)):
        if mass > 0:
            after += mass*disagreement(update_weights(w,p,y),z)
    return (before-after)/cost

def binary_entropy(p):
    if not 0 <= p <= 1:
        raise ValueError("Invalid probability")
    return -math.fsum(x*math.log(x) for x in (p,1-p) if x > 0)

def query_entropy(weights, probabilities):
    w,p,_,_ = prepare(weights, probabilities, [[0]]*len(weights))
    return binary_entropy(math.fsum(a*b for a,b in zip(w,p)))

def candidate_information_gain(weights, probabilities):
    w,p,_,_ = prepare(weights, probabilities, [[0]]*len(weights))
    return max(0.0, query_entropy(w,p)-math.fsum(a*binary_entropy(b) for a,b in zip(w,p)))
