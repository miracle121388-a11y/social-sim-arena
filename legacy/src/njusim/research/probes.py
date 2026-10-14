"""Explicit target expectations, simulation noise and content-addressed probe caches."""
from dataclasses import dataclass, asdict
import math
from ..io import sha

@dataclass(frozen=True)
class ProbeKey:
    candidate_fingerprint: str
    backend_fingerprint: str
    simulator_fingerprint: str
    population_fingerprint: str
    configuration_fingerprint: str
    target_schema: tuple[str, ...]
    scales: tuple[float, ...]
    seeds: tuple[int, ...]
    stream_version: str
    version: str = "probe-cache-v1"

    def __post_init__(self):
        if not all((self.candidate_fingerprint,self.backend_fingerprint,self.simulator_fingerprint,
                    self.population_fingerprint,self.configuration_fingerprint,self.stream_version)):
            raise ValueError("Incomplete cache provenance")
        if not self.target_schema or len(set(self.target_schema)) != len(self.target_schema) or len(self.scales) != len(self.target_schema):
            raise ValueError("Target schema and normalization must align")
        if any(not math.isfinite(s) or s <= 0 for s in self.scales):
            raise ValueError("Invalid predeclared target normalization")
        if len(self.seeds)<2 or len(set(self.seeds)) != len(self.seeds) or any(type(s) is not int for s in self.seeds):
            raise ValueError("Distinct simulation repeats required")

    @property
    def digest(self):
        return sha(asdict(self))

class ProbeCache:
    def __init__(self):
        self._entries = {}

    def put(self, key, draws):
        if key.digest in self._entries:
            raise ValueError("Immutable cache entry already exists")
        draws = tuple(tuple(float(x) for x in row) for row in draws)
        if len(draws) != len(key.seeds) or any(len(row)!=len(key.target_schema) or any(not math.isfinite(x) for x in row) for row in draws):
            raise ValueError("Expected one finite trajectory vector per seed")
        scaled = [tuple(x/s for x,s in zip(row,key.scales)) for row in draws]
        n = len(scaled)
        mean = tuple(math.fsum(row[j] for row in scaled)/n for j in range(len(key.scales)))
        variance = tuple(math.fsum((row[j]-mean[j])**2 for row in scaled)/(n-1) for j in range(len(mean)))
        value = (mean,variance,n)
        self._entries[key.digest] = value
        return value

    def get(self, key):
        return self._entries[key.digest]

def validate_partitions(train, dev, probes, test):
    """Groups map event IDs to canonical rule-composition fingerprints.

    This validates declared boundaries, not the origin of supplied configurations.
    """
    groups = [train,dev,probes,test]
    all_ids = [eid for group in groups for eid in group]
    if any(not group for group in groups) or len(all_ids)!=len(set(all_ids)):
        raise ValueError("Nonempty disjoint event IDs required")
    known = set(train.values()) | set(dev.values()) | set(probes.values())
    if known & set(test.values()):
        raise ValueError("Sealed test composition also appears in training/development/probes")

def normalized_budget_auc(budgets, event_errors):
    """Equal event weights, trapezoidal AUC divided by the declared budget range."""
    budgets = tuple(budgets)
    if len(budgets)<2 or budgets[0]!=0 or any(not math.isfinite(x) or x<0 for x in budgets):
        raise ValueError("Budget grid must start at zero")
    if any(b<=a for a,b in zip(budgets,budgets[1:])) or not event_errors:
        raise ValueError("Increasing common budget grid and independent events required")
    areas=[]
    for values in event_errors:
        if len(values)!=len(budgets) or any(not math.isfinite(x) or x<0 for x in values):
            raise ValueError("Each event needs a finite error at every budget")
        areas.append(math.fsum((b-a)*(x+y)/2 for a,b,x,y in zip(budgets,budgets[1:],values,values[1:]))/budgets[-1])
    return math.fsum(areas)/len(areas)
