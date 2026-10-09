"""One discrete-event kernel for S1/S2/S3; no event-specific engine branches.

One logical minute is the fixed opportunity window. Reporting/driver chunk size
never creates new decision opportunities. All proposals precede central settlement.
"""
from copy import deepcopy
from dataclasses import asdict
from .contracts import AgentState, Observation, DecisionProposal, ActionAttempt, Outcome, TransitionRecord
from .backends import validate_distribution
from .calibration import SharedCalibrator
from .legacy import frozen_choice
from .io import sha, canonical, safe_path, write_json

def uniform(*key): return int(sha(key)[:16], 16)/2**64

class Simulator:
    def __init__(self, spec, personas, backend, calibrator=None, *, seed=7, stream='rep-7', initial_states=None):
        spec.validate()
        if len(personas)!=len({p.id for p in personas}):raise ValueError('Duplicate persona identity')
        if set(spec.target_ids) != {p.id for p in personas}: raise ValueError('Population mismatch')
        self.spec, self.backend = spec, backend
        self.calibrator = calibrator or SharedCalibrator()
        self.seed, self.stream = seed, stream
        self.people = {p.id:p for p in sorted(personas,key=lambda p:p.id)}
        if any(not set(p.contacts) <= set(self.people) for p in personas): raise ValueError('Unknown contact')
        self.states = {p:AgentState() for p in self.people}
        if initial_states:
            if set(initial_states) != set(self.people): raise ValueError('Initial state population mismatch')
            self.states = {p:AgentState(**deepcopy(v)) for p,v in initial_states.items()}
        self.activities = {a.id:a for a in spec.activities}
        self.occupied = {a.id:[] for a in spec.activities}
        self.queues = {a.id:[] for a in spec.activities}
        self.revenue, self.clock = 0, -1
        self.initial_money = sum(s.budget for s in self.states.values())
        self.pending, self.records, self.responses = [], [], {}
        self.receipts = {}
        self.emit('init', -1, spec=asdict(spec), personas=[asdict(p) for p in self.people.values()], seed=seed, stream=stream,
                  backend={'name':backend.name,'version':backend.version}, calibration=asdict(self.calibrator), state=self.snapshot())
        for a in spec.activities:
            for p in sorted(a.initial_informed): self.send(p,a.id,'official',0,1)
        self.emit('ready',-1,state=self.snapshot())
        self.check_invariants()

    def emit(self, kind, time, **payload):
        record=dict(id=f'r{len(self.records):06}',kind=kind,time=time,**deepcopy(payload),prev_hash=self.records[-1]['hash'] if self.records else '0'*64)
        record['hash']=sha(record); self.records.append(record); return record['id']

    def snapshot(self):
        return deepcopy(dict(agents={p:asdict(s) for p,s in self.states.items()}, occupied=self.occupied,
                             queues=self.queues, revenue=self.revenue, pending=self.pending))

    def send(self, recipient, activity, sender, sent, arrival):
        mid=sha([self.stream,recipient,activity,sender,sent])[:20]
        msg=dict(id=mid,recipient=recipient,activity=activity,source=sender,sent_at=sent,arrived_at=arrival,viewed_at=None,scope='recipient_only',comprehension=None)
        self.pending.append(msg)
        self.emit('message_sent',sent,message=msg)

    def observation(self, pid, aid, stage, t, message=None):
        s=self.states[pid]
        messages=[deepcopy(m) for m in s.inbox if m['activity']==aid and m['arrived_at']<=t and (m['viewed_at'] is not None or m is message)]
        if not messages: raise ValueError('Decision without received information')
        a=self.activities[aid]
        # Capacity and other agents' states are deliberately absent, even when full.
        visible=dict(id=aid,start=a.start,end=a.end,price=a.price,topic=a.topic) if aid in s.known else {'id':aid,'notification_preview':a.topic}
        own=dict(budget=s.budget,schedule=deepcopy(s.schedule),goal=s.goal,memory=deepcopy(s.memory),
                 registrations=list(s.registrations),waiting=list(s.waiting))
        return Observation(pid,t,aid,stage,tuple(messages),visible,own,self.people[pid].interest)

    def decide(self, pid, aid, stage, t, message=None):
        if stage not in self.spec.allowed_actions: return False, None
        obs=self.observation(pid,aid,stage,t,message)
        raw=validate_distribution(self.backend.probabilities(deepcopy(obs)))
        if set(raw) != {'yes','no'}: raise ValueError('Stage backend must cover yes/no')
        ref=sha(asdict(obs)); self.responses[ref]=raw
        calibrated=self.calibrator.apply(stage,raw,obs.interest)
        purpose=message['id'] if message else aid
        random_key=(self.stream,pid,t,stage,purpose)
        choice,receipt=frozen_choice(calibrated,seed=self.seed,agent_id=pid,path=[self.stream,stage,purpose],occasion=t)
        proposal=DecisionProposal(stage,raw,calibrated,choice,self.backend.name,self.backend.version,ref,random_key,receipt['draw'])
        rid=self.emit('decision',t,agent=pid,activity=aid,observation=asdict(obs),proposal=asdict(proposal))
        return choice=='yes',rid

    def attempt(self,pid,aid,action,t,decision_id):
        ident=f'a{len(self.records):06}'
        a=ActionAttempt(ident,pid,aid,action,t,decision_id)
        self.emit('attempt',t,attempt=asdict(a)); return a

    def outcome(self,attempt,success,reason,delta=0):
        out=Outcome(attempt.id,attempt.agent,attempt.activity,attempt.action,success,reason,delta)
        rid=self.emit('outcome',attempt.time,outcome=asdict(out))
        self.states[attempt.agent].memory.append(dict(time=attempt.time,activity=attempt.activity,action=attempt.action,success=success,reason=reason,evidence_id=rid))
        return out

    def conflict(self,pid,aid):
        a=self.activities[aid]
        return any(max(a.start,x['start'])<min(a.end,x['end']) for x in self.states[pid].schedule if x.get('activity')!=aid)

    def admit(self, attempt, allow_queue=True):
        pid,aid,t=attempt.agent,attempt.activity,attempt.time
        s=self.states[pid]; a=self.activities[aid]
        if aid in s.registrations: return self.outcome(attempt,False,'duplicate')
        if t>=a.start: return self.outcome(attempt,False,'closed')
        if 'conflict' in self.spec.mechanisms and self.conflict(pid,aid): return self.outcome(attempt,False,'schedule_conflict')
        if s.budget<a.price: return self.outcome(attempt,False,'budget')
        capacity=a.capacity if 'capacity' in self.spec.mechanisms else len(self.people)
        if len(self.occupied[aid])>=capacity:
            if allow_queue and 'waiting' in self.spec.mechanisms and pid not in self.queues[aid]:
                self.queues[aid].append(pid); s.waiting.append(aid)
            return self.outcome(attempt,False,'capacity_waiting' if aid in s.waiting else 'capacity')
        s.budget-=a.price; self.revenue+=a.price
        s.registrations.append(aid); self.occupied[aid].append(pid)
        s.schedule.append(dict(start=a.start,end=a.end,activity=aid))
        return self.outcome(attempt,True,'admitted',-a.price)

    def cancel(self,attempt):
        pid,aid=attempt.agent,attempt.activity;s=self.states[pid];delta=0
        if aid in s.waiting:
            s.waiting.remove(aid);self.queues[aid].remove(pid)
        elif aid in s.registrations:
            s.registrations.remove(aid);self.occupied[aid].remove(pid)
            s.schedule=[x for x in s.schedule if x.get('activity')!=aid]
            delta=self.activities[aid].price;s.budget+=delta;self.revenue-=delta
        else: return self.outcome(attempt,False,'not_registered_or_waiting')
        return self.outcome(attempt,True,'cancelled',delta)

    def check_invariants(self):
        if any(s.budget<0 for s in self.states.values()) or sum(s.budget for s in self.states.values())+self.revenue!=self.initial_money:
            raise AssertionError('Budget conservation violated')
        for aid,members in self.occupied.items():
            cap=self.activities[aid].capacity if 'capacity' in self.spec.mechanisms else len(self.people)
            assert len(members)<=cap and len(members)==len(set(members))
            assert set(members)=={p for p,s in self.states.items() if aid in s.registrations}
            assert set(self.queues[aid])=={p for p,s in self.states.items() if aid in s.waiting}
            assert len(self.queues[aid])==len(set(self.queues[aid]))
            assert not set(members)&set(self.queues[aid])
        for s in self.states.values():
            assert all(x['start']<x['end'] for x in s.schedule)

    def step(self,t):
        if t != self.clock+1: raise ValueError('Time must advance exactly once')
        self.clock=t; old=self.snapshot(); begin=len(self.records)
        for e in self.spec.external_events:
            if e['time']==t:
                for p in sorted(e['recipients']):self.send(p,e['activity'],'official',t,t+1)
        arriving=[m for m in self.pending if m['arrived_at']==t]
        self.pending=[m for m in self.pending if m['arrived_at']!=t]
        for m in sorted(arriving,key=lambda m:m['id']):
            self.states[m['recipient']].inbox.append(m)
            self.emit('message_delivered',t,message=m)
        proposals=[]
        for pid,s in self.states.items():
            for msg in s.inbox:
                marker='view:'+msg['id']
                if marker not in s.considered and msg['arrived_at']<=t:
                    s.considered.append(marker)
                    yes,rid=self.decide(pid,msg['activity'],'view',t,msg)
                    if yes:
                        msg['viewed_at']=t;s.known[msg['activity']]=dict(learned_at=t,source=msg['source'])
                        self.emit('message_viewed',t,agent=pid,message_id=msg['id'],activity=msg['activity'],decision_id=rid,comprehension='unobserved')
            for aid in sorted(s.known):
                a=self.activities[aid]
                if t<a.start and aid not in s.attempted and 'join:'+aid not in s.considered:
                    s.considered.append('join:'+aid)
                    yes,rid=self.decide(pid,aid,'join',t)
                    if yes:s.attempted.append(aid);proposals.append(self.attempt(pid,aid,'join',t,rid))
                if 'peer' in self.spec.mechanisms and t<a.start and 'share:'+aid not in s.considered:
                    s.considered.append('share:'+aid)
                    yes,rid=self.decide(pid,aid,'share',t)
                    if yes:proposals.append(self.attempt(pid,aid,'share',t,rid))
                # A single later reassessment, including waiting agents; no tick-based retries.
                if 'cancellation' in self.spec.mechanisms and t<a.start and t>=s.known[aid]['learned_at']+2 and aid in s.registrations+s.waiting and 'cancel:'+aid not in s.considered:
                    s.considered.append('cancel:'+aid)
                    yes,rid=self.decide(pid,aid,'cancel',t)
                    if yes:proposals.append(self.attempt(pid,aid,'cancel',t,rid))
                if t==a.start and aid in s.registrations:
                    yes,rid=self.decide(pid,aid,'attend',t)
                    if yes:proposals.append(self.attempt(pid,aid,'attend',t,rid))
        # All agents decided against the pre-settlement state. Cancellations release
        # resources first; old waiters have FIFO priority; simultaneous joins use a lottery.
        for a in sorted((a for a in proposals if a.action=='cancel'),key=lambda a:a.id):self.cancel(a)
        for aid in sorted(self.activities):
            capacity=self.activities[aid].capacity if 'capacity' in self.spec.mechanisms else len(self.people)
            while t<self.activities[aid].start and self.queues[aid] and len(self.occupied[aid])<capacity:
                pid=self.queues[aid].pop(0);self.states[pid].waiting.remove(aid)
                a=self.attempt(pid,aid,'promote',t,'environment:prior_waiting_consent');self.admit(a,False)
        ranked=sorted((a for a in proposals if a.action=='join'),key=lambda a:(uniform(self.seed,self.stream,t,'allocation',a.agent,a.activity),a.agent,a.activity))
        for a in ranked:self.admit(a)
        for a in (a for a in proposals if a.action=='share'):
            for peer in sorted(self.people[a.agent].contacts):self.send(peer,a.activity,a.agent,t,t+1)
            self.outcome(a,True,'sent_to_existing_contacts')
        for a in (a for a in proposals if a.action=='attend'):self.outcome(a,True,'attended')
        for aid,a in self.activities.items():
            if t==a.start:
                for pid in list(self.queues[aid]):
                    self.states[pid].waiting.remove(aid)
                    self.outcome(self.attempt(pid,aid,'expire',t,'environment:deadline'),False,'registration_closed')
                self.queues[aid]=[]
            if t==a.end:
                for pid in list(self.occupied[aid]):
                    self.states[pid].registrations.remove(aid)
                    self.outcome(self.attempt(pid,aid,'release',t,'environment:activity_end'),True,'completed_slot_release')
                self.occupied[aid]=[]
        self.check_invariants()
        record=TransitionRecord(t,old,self.snapshot(),tuple(r['id'] for r in self.records[begin:]))
        self.emit('transition',t,transition=asdict(record))

    def run(self, chunk_minutes=1):
        if type(chunk_minutes) is not int or chunk_minutes<1: raise ValueError('Invalid chunk size')
        # Chunking only schedules fixed logical boundaries; probabilities are unchanged.
        for start in range(self.clock+1,self.spec.horizon+1,chunk_minutes):
            for t in range(start,min(start+chunk_minutes,self.spec.horizon+1)):self.step(t)
        return self.records

    def save(self,path):
        folder=safe_path(path);folder.mkdir(parents=True,exist_ok=False)
        with (folder/'trace.jsonl').open('x',encoding='utf-8') as f:
            for r in self.records:f.write(canonical(r)+'\n')
        write_json(folder/'responses.json',self.responses)
        write_json(folder/'state.json',self.snapshot())
        from .metrics import metrics
        write_json(folder/'metrics.json',metrics(self.records))
