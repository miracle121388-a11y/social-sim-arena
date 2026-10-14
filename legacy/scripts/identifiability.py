import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT);sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'src'))
from njusim.guard import install
install()
from njusim.fixtures import scenario
from njusim.calibration import SharedCalibrator
from njusim.backends import OfflineFixtureBackend
from njusim.experiments import simulate
from njusim.metrics import metrics
from njusim.io import write_json
from itertools import combinations

rows=[]
for join in (-1.0,0.0,1.0):
    for cancel in (-1.0,0.0,1.0):
        cal=SharedCalibrator({'join':join,'cancel':cancel})
        training=simulate(scenario('S2','ident-train',capacity=3),OfflineFixtureBackend(),cal,seed=31)
        test=simulate(scenario('S3','ident-test'),OfflineFixtureBackend(),cal,seed=32)
        train=metrics(training.records);held=metrics(test.records)
        rows.append(dict(parameters=cal.biases,train_attended=train['counts'].get('attend_success',0),train_attempts=train['attempts'].get('join',0),heldout_attended=held['counts'].get('attend_success',0),heldout_join_attempts=held['attempts'].get('join',0)))
pairs=[{'left':a,'right':b} for a,b in combinations(rows,2) if a['train_attended']==b['train_attended'] and a['train_attempts']!=b['train_attempts']]
write_json('artifacts/identifiability.json',dict(provenance='synthetic',criterion='same single aggregate attendance but differing process attempts; not equality of full trajectories',grid=rows,ambiguous_pairs=pairs,interpretation='An aggregate alone does not identify the behavioral process; illustrative finite fixture only, not real mechanism recovery'))
print({'grid_points':len(rows),'ambiguous_pairs':len(pairs)})
