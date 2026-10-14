from collections import Counter
from copy import deepcopy
import math
from .io import sha

def replay_trace(records):
    previous='0'*64;state=None
    for r in records:
        if r['prev_hash']!=previous or sha({k:v for k,v in r.items() if k!='hash'})!=r['hash']:raise ValueError('Corrupt trace')
        previous=r['hash']
        if r['kind'] in ('init','ready'):state=deepcopy(r['state'])
        elif r['kind']=='transition':
            if state!=r['transition']['old_state']:raise ValueError('Discontinuous state chain')
            state=deepcopy(r['transition']['new_state'])
    return state

def metrics(records):
    counts=Counter();attempts=Counter();trajectory=[]
    for r in records:
        if r['kind'] in ('message_sent','message_delivered','message_viewed'):counts[r['kind']]+=1
        if r['kind']=='attempt':attempts[r['attempt']['action']]+=1
        if r['kind']=='outcome':
            o=r['outcome'];counts[f"{o['action']}_{'success' if o['success'] else 'failure'}"]+=1
            counts['reason:'+o['reason']]+=1
        if r['kind']=='transition':
            s=r['transition']['new_state']
            trajectory.append(dict(time=r['time'],registered=sum(map(len,s['occupied'].values())),waiting=sum(map(len,s['queues'].values())),
                                   attended=counts['attend_success'],revenue=s['revenue'],budget_total=sum(a['budget'] for a in s['agents'].values())))
    return dict(provenance='derived',input_provenance='synthetic',counts=dict(counts),attempts=dict(attempts),trajectory=trajectory,source_tail_hash=records[-1]['hash'])

def probability_scores(rows,calibrator):
    usable=[r for r in rows if r['label'] is not None and r.get('at_risk',True) and not r.get('censored',False)]
    if not usable:return dict(n=0,brier=None,nll=None,reliability_bins=[])
    pairs=[(calibrator.apply(r['stage'],{'yes':r['raw_p'],'no':1-r['raw_p']},r['interest'])['yes'],r['label']) for r in usable]
    bins=[]
    for i in range(5):
        b=[(p,y) for p,y in pairs if i/5<=p and (p<(i+1)/5 or i==4)]
        bins.append(dict(lower=i/5,n=len(b),prediction=sum(p for p,y in b)/len(b) if b else None,frequency=sum(y for p,y in b)/len(b) if b else None))
    return dict(n=len(pairs),brier=sum((p-y)**2 for p,y in pairs)/len(pairs),nll=sum(-y*math.log(max(1e-12,p))-(1-y)*math.log(max(1e-12,1-p)) for p,y in pairs)/len(pairs),reliability_bins=bins)

def trajectory_mae(predicted,target,population):
    if [x['time'] for x in predicted]!=[x['time'] for x in target]:raise ValueError('Time alignment mismatch')
    return sum(abs(a[k]-b[k])/population for a,b in zip(predicted,target) for k in ('registered','waiting','attended'))/(3*len(target))
