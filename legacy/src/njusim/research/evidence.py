"""Synthetic training evidence API. This is NOT a security boundary for real data."""
from dataclasses import dataclass, asdict
from ..io import sha

@dataclass(frozen=True)
class Query:
    id: str
    event_id: str
    stage: str
    cost: int
    source_ref: str
    opportunity_id: str
    split: str = "train"
    provenance: str = "synthetic"
    permitted: bool = True
    history_complete: bool = True
    at_risk: bool = True
    censored: bool = False
    directly_changes_target: bool = False

    def __post_init__(self):
        if not all((self.id,self.event_id,self.stage,self.source_ref,self.opportunity_id)):
            raise ValueError("Source and opportunity identity required")
        if type(self.cost) is not int or self.cost <= 0:
            raise ValueError("Positive integer evidence cost units required")
        for key in ("permitted","history_complete","at_risk","censored","directly_changes_target"):
            if type(getattr(self,key)) is not bool:
                raise ValueError("Boolean query metadata required")

@dataclass(frozen=True)
class Revealed:
    query_id: str
    label: int
    cost: int
    source_ref: str

class QueryPool:
    """Learner-visible metadata and paid observations; never hidden labels."""
    def __init__(self, queries, *, train_event_ids, budget):
        if type(budget) is not int or budget < 0:
            raise ValueError("Invalid integer budget")
        self.queries = tuple(queries)
        if len({q.id for q in self.queries}) != len(self.queries):
            raise ValueError("Duplicate query IDs")
        if len({q.opportunity_id for q in self.queries}) != len(self.queries):
            raise ValueError("Same opportunity cannot be sold under multiple IDs")
        self._by_id = {q.id:q for q in self.queries}
        self._train = frozenset(train_event_ids)
        self._budget = budget
        self._revealed = []

    @property
    def revealed(self):
        return tuple(self._revealed)

    @property
    def spent(self):
        return sum(r.cost for r in self._revealed)

    @property
    def history_token(self):
        return sha([asdict(r) for r in self.revealed])

    def check(self, query_id, history_token):
        if history_token != self.history_token:
            raise ValueError("Stale conditional query; recompute from revealed history")
        if query_id not in self._by_id:
            raise KeyError(query_id)
        q = self._by_id[query_id]
        if q.split != "train" or q.event_id not in self._train:
            raise PermissionError("Only training evidence can be queried")
        if q.provenance != "synthetic":
            raise PermissionError("Real or generated data needs a separate authorized ingestion workflow")
        if not q.permitted:
            raise PermissionError("Field access denied")
        if not q.history_complete or not q.at_risk or q.censored or q.directly_changes_target:
            raise ValueError("Query does not satisfy the first-version observation model")
        if query_id in {r.query_id for r in self.revealed}:
            raise ValueError("Repeated query")
        if self.spent+q.cost > self._budget:
            raise ValueError("Evidence budget exceeded")
        return q

    def reveal(self, query_id, *, history_token, read_label):
        q = self.check(query_id,history_token)
        # Pass the checked metadata, not a label store, into the learner-visible API.
        y = read_label(q.id)
        if type(y) is not int or y not in (0,1):
            raise ValueError("Missing/censored/nonbinary evidence cannot become a negative")
        record = Revealed(q.id,y,q.cost,q.source_ref)
        self._revealed.append(record)
        return record
