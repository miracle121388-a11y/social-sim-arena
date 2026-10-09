"""Explicitly fabricated engineering fixtures; never real student records."""
from dataclasses import asdict
from .contracts import Persona, EventSpec, Activity

def population(n=30, prefix='syn'):
    ids=[f'{prefix}-{i:02}' for i in range(n)]
    return [Persona(p,(i%7+1)/8,tuple(ids[j%n] for j in (i+1,i+3))) for i,p in enumerate(ids)]

def scenario(name, event_id=None, split='smoke', n=30, prefix='syn', date='2026-10-01', capacity=None):
    ids=tuple(p.id for p in population(n,prefix)); event_id=event_id or name
    if name not in ('S1','S2','S3'): raise ValueError('Unknown fixture')
    initial=ids if name!='S3' else ids[:max(2,n//5)]
    activities=[Activity('A',7,9,capacity if capacity is not None else (n if name=='S1' else 5),2,initial)]
    mech=['notification','capacity']
    if name in ('S2','S3'):mech+=['waiting','cancellation']
    if name=='S3':
        mech+=['peer','conflict']
        activities.append(Activity('B',7,10,4,3,ids[2:max(4,n//4)]))
    return EventSpec(event_id,name,date+'T09:00:00+08:00',10,tuple(activities),tuple(mech),ids,split=split)

def stage_rows(sim):
    return [dict(event_id=sim.spec.event_id,agent_id=r['agent'],time=r['time'],observed_at=r['time'],stage=r['proposal']['stage'],
                 interest=r['observation']['interest'],raw_p=r['proposal']['raw']['yes'],label=int(r['proposal']['selected']=='yes'),
                 at_risk=True,censored=False,provenance='synthetic',evidence_id=r['id'],features=r['observation'])
            for r in sim.records if r['kind']=='decision']
