"""Independent post-freeze audit of the complete campaign and paper evidence."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import csv
import hashlib
import json
import subprocess
import numpy as np
from workspace import path,digest,ROOT
from v2_evaluation import verify,ci,guards

verify()
read=lambda p:json.loads(path(p).read_text(encoding='utf-8'))
rows=list(csv.DictReader(path('experiments_v2.tsv').open(encoding='utf-8'),delimiter='\t'))
assert len(rows)==30
frozen=read('provenance/v2/frozen.json');previous=read('provenance/v2/baseline.json')['auc_error']
runtime=[];accept=[]
for row in rows:
    result=read(row['result']);runtime.append(result['runtime_s'])
    code=subprocess.check_output(['git','show',row['commit']+':method.py'],cwd=ROOT)
    assert hashlib.sha256(code).hexdigest()==row['method_sha256']==result['method_sha256']
    assert guards(result)==result['guards']
    keep=all(result['guards'].values()) and result['auc_error']<previous-1e-8
    assert (row['status']=='KEEP')==keep
    if keep:previous=result['auc_error'];accept.append(row['trial'])
    else:
        ref=subprocess.check_output(['git','rev-parse','refs/autoresearch-v2/rejected/'+row['trial']],cwd=ROOT,text=True).strip()
        assert ref==row['commit']
    f=result['strategies']['Full']
    for s in result['strategies'].values():
        assert abs(s['b0_error']-f['b0_error'])<1e-6
        assert abs(s['initial_brier']-f['initial_brier'])<1e-6
assert digest('method.py')==frozen['method_sha256']
assert frozen['keeps']==len(accept)
assert abs(frozen['best_dev_auc']-previous)<1e-10
checked=0
for filename in ['provenance/v2/test-current.json','provenance/v2/test-v1.json']:
    r=read(filename)
    for name,s in r['strategies'].items():
        curves=np.array(s['event_world_curves']);auc=np.trapezoid(curves,[0,2,4,8,12,16],axis=1)/16
        assert np.allclose(auc,np.array(s['event_world_auc']),atol=1e-7,rtol=0)
        assert abs(auc.mean()-s['auc'])<1e-7
        assert np.allclose(ci(auc.mean(1)),s['auc_ci95'],atol=1e-7,rtol=0)
        for e,a in enumerate(s['activity_results']):
            assert np.allclose(ci(auc[:,e]),a['auc_ci95'],atol=1e-7,rtol=0)
            assert np.allclose(ci(curves[:,0,e]-curves[:,-1,e]),a['b0_b16_difference_ci95'],atol=1e-7,rtol=0)
            checked+=1
    assert r['strategies']['Full']['selected_indices']==r['strategies']['ParamIG']['selected_indices']
snap=read('provenance/v2/v1_snapshot/manifest.json')
for name,h in snap.items():assert digest('provenance/v2/v1_snapshot/'+name)==h
report={'valid_trials':len(rows),'kept_trials':accept,'git_sources_verified':30,
        'activity_strategy_statistics_verified':checked,'v1_snapshot_files_verified':len(snap),
        'fast_dev_runtime_range_s':[min(runtime),max(runtime)],
        'method_sha256':digest('method.py'),'infrastructure_lock_verified':True,
        'PAPER_TABLES_sha256':digest('PAPER_TABLES.tex'),
        'v1_cache_sha256':digest('data/rollout_cache.pt')}
path('provenance/v2/validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
