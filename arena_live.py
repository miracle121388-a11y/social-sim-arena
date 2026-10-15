"""Bounded prospective preparation and explicit signed submission; no scheduler."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace import path, save_json, digest
import argparse, base64, hashlib, json, math, uuid
from datetime import datetime, timezone, timedelta
import urllib.request, urllib.error
import jsonschema
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from forecast import respond
from evaluate import verify_integrity

ORIGIN = 'https://social-simulation-arena.com'
REPO = 'https://raw.githubusercontent.com/Social-Atoms/social-sim-arena/'
ENTRANT = 'njusim-mace'
METHOD = 'c905e2295dfeb9cbf075bd51b5e7393a7875000cc3f9c90a23066e94a540cf81'

def read(name):
    return json.loads(path(name).read_text(encoding='utf8'))

def now():
    return datetime.now(timezone.utc)

def dt(s):
    value = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if value.tzinfo is None: raise ValueError('Timezone required')
    return value

def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def signing_bytes(meta, body):
    return canonical({'protocol':'ssa-signed-forecast-v1','audience':'ssa-production-v1',
        'method':'POST','path':'/api/v1/forecasts','entrant':meta['entrant'],
        'key_id':meta['key-id'],'request_id':meta['request-id'],
        'signed_at':meta['timestamp'],'body_sha256':hashlib.sha256(body).hexdigest()})

def initialize():
    key_path = path('.private/arena-ed25519.key')
    if key_path.exists():
        key = Ed25519PrivateKey.from_private_bytes(key_path.read_bytes())
    else:
        key = Ed25519PrivateKey.generate()
        with key_path.open('xb') as f:
            f.write(key.private_bytes(serialization.Encoding.Raw,
                serialization.PrivateFormat.Raw, serialization.NoEncryption()))
    pub = base64.b64encode(key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
    registration = {'entrant_id':ENTRANT, 'name':'NjuSim MACE Forecast',
        'type':'participant','github':'Ustinian5',
        'method':'Frozen statistical expert ensemble with budgeted historical calibration and CRPS-based weighting. Scalar public-opinion and consumer forecasts; no LLM calls or paid data.',
        'keys':[{'id':'k1','alg':'ed25519','public':pub}]}
    jsonschema.validate(registration, read('provenance/live/schema__entrant.schema.json'))
    save_json('provenance/live/registration.json', registration)
    print('Registration validated; private key stays under .private/')

def prepare():
    verify_integrity()
    if digest('method.py') != METHOD: raise ValueError('Frozen method changed')
    stamp = now()
    protocol = {'created_at':stamp.isoformat(), 'method_sha256':METHOD,
        'scope':'Published, open, scoreable scalar public-opinion/consumer rounds locking within seven days; nearest round per series.',
        'history':'Pinned official lock history, last 24 observations; observed before preparation; no corrected locks; persistence must match.',
        'evaluation':'Retain every selected round and failure. Score all accepted resolved submissions using official CRPS and per-round skill; report coverage and domain/week summaries. No tuning on these outcomes.',
        'max_rounds':20, 'paid_calls':0, 'submission':'Explicit submit command only; requires merged matching public key.'}
    save_json('provenance/live/protocol.json', protocol)
    data = read('provenance/live/snapshot-20261015.json')
    commit = read('provenance/live/upstream-tree.json')['sha']
    rows=[];seen=set()
    for r in sorted(data['rounds'], key=lambda x:(x['lock_at'],x['round_id'])):
        if not (r.get('status')=='open' and r.get('scoreable',False) and
                r.get('target_type')=='continuous_normal' and r.get('domain') in ('public-opinion','consumer') and
                dt(r['published_at'])<=stamp<dt(r['lock_at'])<=stamp+timedelta(days=7)): continue
        if r['series'] in seen: continue
        seen.add(r['series'])
        if len(rows)>=20: break
        rid=r['round_id'];row={'round_id':rid,'lock_at':r['lock_at'],'status':'prepared'}
        try:
            lock=fetch(REPO+commit+'/locks/'+rid+'.json')
            save_json('provenance/live/lock-'+rid+'.json', lock)
            if lock.get('corrected'): raise ValueError('Corrected lock')
            if dt(lock['observed_at'])>stamp: raise ValueError('Future snapshot')
            hist=lock['history'][-24:]
            if any(p['date']>=stamp.date().isoformat() for p in hist): raise ValueError('Not historical at preparation')
            req={'schema_version':'ssa-agent-api-v2','round':{
                **{k:r[k] for k in ('round_id','series','domain','lock_at','release_at','target_type')},
                'context':{'history':hist,'persistence':r['baselines']['persistence']}}}
            fc=respond(req)['forecast']
            if not all(math.isfinite(v) for v in fc.values()): raise ValueError('Nonfinite forecast')
            answer={'round_id':rid,'entrant':ENTRANT,'topline':fc}
            jsonschema.validate(answer,read('provenance/live/schema__forecast.schema.json'))
            dest='.private/'+rid+'-answer.json'
            save_json(dest,answer);save_json('.private/'+rid+'-input.json',req)
            row.update(answer_file=dest,answer_sha256=digest(dest),history_points=len(hist),
                domain=r['domain'],persistence=r['baselines']['persistence'])
        except Exception as e:
            row.update(status='failed',error=type(e).__name__+': '+str(e))
        rows.append(row)
    save_json('provenance/live/prepared.json',{'created_at':stamp.isoformat(),
        'commit':commit,'method_sha256':METHOD,'snapshot_sha256':digest('provenance/live/snapshot-20261015.json'),'rounds':rows})
    print(json.dumps(rows,indent=2))

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def submit(rid):
    manifest=read('provenance/live/prepared.json')
    rows=[r for r in manifest['rounds'] if r['round_id']==rid and r['status']=='prepared']
    if len(rows)!=1: raise ValueError('Round not prepared')
    row=rows[0]
    receipt='.private/'+rid+'-receipt.json'
    if path(receipt).exists(): print('Receipt already saved; no repeat POST');return
    if digest(row['answer_file'])!=row['answer_sha256']: raise ValueError('Answer changed')
    registration=fetch(REPO+'main/entrants/'+ENTRANT+'.json')
    local=read('provenance/live/registration.json')
    if registration.get('status','active')!='active' or registration.get('github')!=local['github'] or registration.get('keys')!=local['keys']:
        raise ValueError('Registration/key not active and merged')
    live=fetch(ORIGIN+'/data.json')
    current=next(r for r in live['rounds'] if r['round_id']==rid)
    if current.get('status')!='open' or not current.get('scoreable',False) or now()>=min(dt(row['lock_at']),dt(current['lock_at'])):
        raise ValueError('Round no longer eligible')
    raw=path(row['answer_file']).read_bytes()
    key=Ed25519PrivateKey.from_private_bytes(path('.private/arena-ed25519.key').read_bytes())
    reqfile='.private/'+rid+'-signed.json'
    if path(reqfile).exists():
        saved=read(reqfile);meta=saved['meta']
        if saved['body_sha256']!=hashlib.sha256(raw).hexdigest():raise ValueError('Retry body mismatch')
    else:
        meta={'entrant':ENTRANT,'key-id':'k1','request-id':str(uuid.uuid4()),'timestamp':now().isoformat().replace('+00:00','Z')}
        meta['signature']=base64.b64encode(key.sign(signing_bytes(meta,raw))).decode()
        save_json(reqfile,{'meta':meta,'body_sha256':hashlib.sha256(raw).hexdigest()})
    key.public_key().verify(base64.b64decode(meta['signature']),signing_bytes(meta,raw))
    req=urllib.request.Request(ORIGIN+'/api/v1/forecasts',data=raw,
        headers={'Content-Type':'application/json',**{'X-SSA-'+k:v for k,v in meta.items()}},method='POST')
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=30) as response:
            status=response.status;body=response.read().decode()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'Intake HTTP {e.code}: {e.read().decode()}; preserve signed request for audit') from None
    save_json(receipt,{'http_status':status,'response':body,'received_locally_at':now().isoformat()})
    print('Saved receipt for',rid,body)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['init','prepare','submit']);parser.add_argument('--round')
    args=parser.parse_args()
    if args.action=='init':initialize()
    elif args.action=='prepare':prepare()
    elif not args.round:parser.error('--round required')
    else:submit(args.round)
