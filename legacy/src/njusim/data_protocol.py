"""Validated ingestion interface; no collection, scraping or contact code."""
from datetime import datetime

PROVENANCE={'synthetic','real_observed','model_generated','derived'}
STAGES={'delivered','view','join','share','cancel','attend'}

def validate_observed_rows(rows, *, authorized_real=False):
    seen=set(); validated=[]
    required={'event_id','participant_id','stage','opportunity_id','window_start','window_end','feature_as_of','label','observed','censored','provenance','evidence_id','consent_ref'}
    for row in rows:
        if set(row)!=required:raise ValueError('Observation schema mismatch')
        if row['provenance'] not in PROVENANCE or row['stage'] not in STAGES:raise ValueError('Invalid provenance/stage')
        if row['provenance']=='real_observed' and (not authorized_real or not row['consent_ref']):raise PermissionError('Real observations require explicit authorized workflow and consent provenance')
        times=[datetime.fromisoformat(row[k]) for k in ('window_start','window_end','feature_as_of')]
        if any(t.utcoffset() is None for t in times) or not times[2]<=times[0]<times[1]:raise ValueError('Invalid time window or future features')
        if row['label'] not in (None,0,1):raise ValueError('Invalid observed label')
        if not isinstance(row['observed'],bool) or not isinstance(row['censored'],bool):raise ValueError('Observation indicators must be booleans')
        if not row['observed'] and row['label'] is not None:raise ValueError('Missing must not become negative')
        if row['observed'] and row['label'] is None:raise ValueError('Observed label missing')
        identity=tuple(row[k] for k in ('event_id','participant_id','stage','opportunity_id'))
        if identity in seen:raise ValueError('Duplicate opportunity')
        seen.add(identity);validated.append(dict(row))
    return validated
