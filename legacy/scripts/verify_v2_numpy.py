"""Use the already installed .venv-socioverse; offline, no installation."""
from pathlib import Path
import sys, os, json, random, math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
for key in ('TEMP','TMP','TMPDIR'):os.environ[key]=str(ROOT/'.tmp')
from njusim.io import safe_path,write_json
from njusim.guard import install
install()
from njusim.research.acquisition import composition_score,enumeration_score
from njusim.research.acquisition_numpy import composition_score_numpy
import numpy as np
output=safe_path(sys.argv[1])
if output.exists():raise FileExistsError(output)
try:
    rng=random.Random(611);errors=[]
    for i in range(1000):
        k=rng.randint(2,12);d=rng.randint(1,12)
        w=[rng.random() for _ in range(k)];p=[rng.random() for _ in range(k)]
        z=[[rng.uniform(-3,3) for _ in range(d)] for _ in range(k)];c=rng.uniform(.1,4)
        got=composition_score_numpy(w,p,z,c)
        ref=enumeration_score(w,p,z,c)
        assert math.isclose(got,ref,rel_tol=1e-9,abs_tol=1e-11),(i,got,ref)
        assert math.isclose(got,composition_score(w,p,z,c),rel_tol=1e-10,abs_tol=1e-12)
        errors.append(abs(got-ref))
    for p in ([0,0],[1,1],[.5,.5],[1e-300,2e-300],[1-1e-15,1-2e-15]):
        result=composition_score_numpy([1,1],p,[[0],[1]])
        assert math.isfinite(result) and result>=0
    result=dict(status='tested_synthetic',random_cases=1000,boundary_cases=5,max_absolute_error=max(errors),numpy=np.__version__,external_calls=0)
    write_json(output,result);print(json.dumps(result))
except Exception as exc:
    write_json(output,dict(status='failed',error=repr(exc)));raise
