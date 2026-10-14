"""Optional NumPy implementation; no change to the standard-library V1 environment."""
import numpy as np
from .acquisition import prepare

def composition_score_numpy(weights, probabilities, targets, cost=1.0):
    w,p,z,cost = prepare(weights, probabilities, targets, cost)
    w,p,z = np.asarray(w), np.asarray(p), np.asarray(z)
    if np.all(p == p[0]):
        return 0.0
    if w @ p > 0.5:
        p = 1-p
    pb = float(w @ p)
    if pb == 0 or pb == 1:
        return 0.0
    z = z-z[0]
    centered = z-w@z
    a = (w*(p-pb)) @ centered
    scaled = a / np.sqrt(pb) / np.sqrt(1-pb)
    return float(scaled @ scaled / cost)
