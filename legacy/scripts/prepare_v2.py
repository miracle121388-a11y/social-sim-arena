"""Offline V2 preparation check; use --batch with a never-used ID."""
import argparse, os, sys, csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
for k in ('TEMP','TMP','TMPDIR'):os.environ[k]=str(ROOT/'.tmp')
from njusim.io import safe_path, write_json, sha
from njusim.guard import install
install()
from njusim.research.preparation import run
parser=argparse.ArgumentParser()
parser.add_argument('--batch',required=True)
args=parser.parse_args()
if not args.batch or Path(args.batch).name!=args.batch or args.batch in ('.','..'):
    raise ValueError('Batch must be a simple name')
folder=safe_path('artifacts')/args.batch
folder=safe_path(folder);folder.mkdir(exist_ok=False)
try:
    result=run(folder)
    result['source_hashes']={str(p.relative_to(ROOT)):sha(p.read_text(encoding='utf-8')) for p in (ROOT/'src/njusim/research').glob('*.py')}
    write_json(folder/'summary.json',result)
    status='tested_synthetic'
except Exception as exc:
    result={'error':repr(exc),'status':'failed'}
    write_json(folder/'failure.json',result);status='failed'
finally:
    with safe_path('experiments/registry.csv').open('a',encoding='utf-8',newline='') as f:
        csv.writer(f,lineterminator='\n').writerow([args.batch,'v2_preparation',status,'synthetic',str(folder.relative_to(ROOT)),json.dumps(result)])
print(json.dumps(result))
if status=='failed':raise SystemExit(1)
