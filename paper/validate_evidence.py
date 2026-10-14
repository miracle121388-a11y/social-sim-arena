"""Check manuscript provenance and recompute reported activity intervals, without research runs."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workspace import path,digest
import csv
import hashlib
import json
import subprocess
import numpy as np

def read(name):
    return json.loads(path(name).read_text(encoding='utf-8'))

manifest=read('paper/artifact_manifest.json')
for name,expected in manifest['inputs'].items():
    assert digest(name)==expected,name
assert digest('method.py')==manifest['method_sha256']
locked=read('infrastructure.lock.json')
for name,expected in locked.items():
    assert digest(name)==expected,name
legacy=read('provenance/legacy-migration.json')['sha256']
for name,expected in legacy.items():
    assert digest('legacy/'+name)==expected,name

audit=read('provenance/closure/evolution-audit.json')
with path('experiments.tsv').open(encoding='utf-8',newline='') as stream:
    ledger=list(csv.DictReader(stream,delimiter='\t'))
for row in audit['rows']:
    content=subprocess.check_output(['git','show',row['commit']+':method.py'],cwd=path(''))
    assert hashlib.sha256(content).hexdigest()==row['method_sha256']
    matches=[r for r in ledger if r['run_id']==row['run_id']]
    expected='keep' if row['decision']=='KEEP' else 'discard'
    assert any(r['status'].lower()==expected for r in matches),(row['round'],matches)
    assert any(abs(float(r['auc_error'])-row['dev_auc'])<1e-12 for r in matches if r['auc_error'])

s=read('provenance/closure/supplement.json')
indices=np.random.default_rng(782).integers(s['worlds'],size=(2000,s['worlds']))
checked=0
for name,summary in s['summary'].items():
    # Match the fixed protocol: average query repetitions inside each world first.
    per_world=[]
    for world in s['raw_worlds']:
        rows=[r for r in world['strategies'] if r['name']==name]
        per_world.append(np.mean([r['event_auc'] for r in rows],axis=0))
    values=np.asarray(per_world)
    for metric,observations in [('event_auc',values),('macro_auc',values.mean(1))]:
        stat=summary[metric]
        np.testing.assert_allclose(observations.mean(0),stat['mean'],rtol=1e-12,atol=1e-14)
        low,high=np.quantile(observations[indices].mean(1),[.025,.975],axis=0)
        np.testing.assert_allclose(low,stat['ci95_low'],rtol=1e-12,atol=1e-14)
        np.testing.assert_allclose(high,stat['ci95_high'],rtol=1e-12,atol=1e-14)
        checked+=1
for name,v in s['timing'].items():
    ratios=[r['enumeration_ms']/r['covariance_ms'] for r in v['raw']]
    np.testing.assert_allclose(np.median(ratios),v['median_speedup'])

report={'method_unchanged':True,'locked_files_verified':len(locked),'legacy_files_byte_identical':len(legacy),
        'git_candidates_verified':len(audit['rows']),'ledger_decisions_verified':len(audit['rows']),
        'activity_and_macro_intervals_recomputed':checked,'timing_ratios_recomputed':len(s['timing']),
        'artifact_inputs_verified':True,'all_root_result_files_inventoried':manifest['all_result_files'],
        'scope':'No experiment rerun, no method change, no new real-data validation.'}
path('paper/qa/evidence-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
