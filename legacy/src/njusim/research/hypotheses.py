"""Empirical compatibility sets, not confidence sets or real-world posteriors."""
from dataclasses import dataclass
import math
from ..io import sha

def normalized(weights):
    values = tuple(float(x) for x in weights)
    if not values or any(not math.isfinite(x) or x < 0 for x in values) or max(values) <= 0:
        raise ValueError("Weights must have finite positive total mass")
    scale = max(values)
    total = math.fsum(x / scale for x in values)
    return tuple((x / scale) / total for x in values)

@dataclass(frozen=True)
class Hypothesis:
    id: str
    mechanism: str
    parameters: tuple[tuple[str, float], ...]
    process_loss: float
    rollout_loss: float
    fit_event_ids: tuple[str, ...]
    source: str
    version: str = "1"

    def __post_init__(self):
        if not self.id or not self.mechanism or not self.source or not self.version:
            raise ValueError("Candidate identity and provenance required")
        keys = [k for k, _ in self.parameters]
        if not keys or len(keys) != len(set(keys)) or any(not k or not math.isfinite(v) for k, v in self.parameters):
            raise ValueError("Invalid candidate parameters")
        if any(not math.isfinite(x) or x < 0 for x in (self.process_loss, self.rollout_loss)):
            raise ValueError("Invalid training losses")
        if not self.fit_event_ids or len(set(self.fit_event_ids)) != len(self.fit_event_ids):
            raise ValueError("Unique fit events required")

    @property
    def fingerprint(self):
        return sha((self.mechanism, sorted(self.parameters), self.version))

@dataclass(frozen=True)
class HypothesisSet:
    candidates: tuple[Hypothesis, ...]
    weights: tuple[float, ...]
    weight_kind: str = "empirical"
    version: str = "compatibility-v1"

    def __post_init__(self):
        if not self.candidates or len(self.candidates) != len(self.weights):
            raise ValueError("Nonempty aligned candidates and weights required")
        if len({c.id for c in self.candidates}) != len(self.candidates):
            raise ValueError("Duplicate candidate ID")
        if len({c.fingerprint for c in self.candidates}) != len(self.candidates):
            raise ValueError("Duplicated mechanism is not candidate diversity")
        if self.weight_kind not in ("empirical", "finite_mixture"):
            raise ValueError("Unsupported weight interpretation")
        object.__setattr__(self, "weights", normalized(self.weights))

    @property
    def effective_size(self):
        return 1.0 / math.fsum(w*w for w in self.weights)

def compatible(candidates, *, train_event_ids, epsilon_process, epsilon_rollout):
    if any(not math.isfinite(x) or x < 0 for x in (epsilon_process, epsilon_rollout)):
        raise ValueError("Invalid predeclared thresholds")
    candidates = tuple(candidates)
    allowed = set(train_event_ids)
    if not allowed:
        raise ValueError("Empty training event set")
    for c in candidates:
        if set(c.fit_event_ids) != allowed:
            raise ValueError("Candidates must be assessed on the same training events")
    kept = tuple(c for c in candidates if c.process_loss <= epsilon_process and c.rollout_loss <= epsilon_rollout)
    if not kept:
        raise ValueError("Empty compatibility set; do not manufacture certainty")
    return HypothesisSet(kept, (1.0,) * len(kept))
