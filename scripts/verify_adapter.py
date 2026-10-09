import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT);sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'vendor/socioverse2'),str(ROOT/'studies/nju_compositional_simulation')]
for key in ('TMP','TEMP','TMPDIR'):os.environ[key]=str(ROOT/'.tmp')
from njusim.io import write_json,safe_path
# Import native libraries before installing the Python audit hook. C extensions
# are not an OS sandbox; all DB/temp paths below are explicitly inside ROOT.
import duckdb
import pandas
from socioverse.schemas.study import StudySpec
from socioverse.schemas.simulation import SimulationConfig
from socioverse.schemas.population import PopulationBundle
from socioverse.schemas.environment import EnvironmentBundle
from njusim.guard import install
install()
from adapter import build_adapter
from njusim.fixtures import scenario,population
from njusim.experiments import simulate,verify_replay
from njusim.backends import OfflineFixtureBackend
from dataclasses import asdict
import json

batch=sys.argv[1] if len(sys.argv)>1 else 'adapter-v1'
folder=safe_path('artifacts')/batch;folder=safe_path(folder);folder.mkdir(exist_ok=False)
results=[]
for name in ('S1','S2','S3'):
    spec=scenario(name)
    direct=simulate(spec,OfflineFixtureBackend())
    outer,session=build_adapter(spec,population(),folder/name/'study.duckdb')
    history=outer.run()
    assert session.native.records==direct.records, 'Native microtrace parity failed'
    assert session.native.snapshot()==direct.snapshot()
    assert len(history.rows)==spec.horizon+1
    verify_replay(session.native)
    session.native.save(folder/name/'sidecar')
    con=duckdb.connect(str(folder/name/'study.duckdb'),read_only=True)
    rows=con.execute('select count(*) from panel').fetchone()[0];con.close()
    assert rows==30*(spec.horizon+1)
    try:outer.env.apply([])
    except ValueError:pass
    else:raise AssertionError('Double apply accepted')
    for kwargs in ({'interaction_rounds':2},{'warm_start':object()}):
        try:build_adapter(spec,population(),folder/name/'unused.duckdb',**kwargs)
        except ValueError:pass
        else:raise AssertionError('Unsupported replay accepted')
    results.append(dict(scenario=name,panel_rows=rows,official_steps=len(history.rows),native_records=len(direct.records),exact_trace_parity=True,duplicate_apply_rejected=True,unsupported_modes_rejected=True))
    write_json(folder/name/'official_metrics.json',history.model_dump())

study=safe_path('studies/nju_compositional_simulation')
env=EnvironmentBundle(study_id='nju_compositional_simulation',provider_ref='nju.env',provider_args={'event_spec':'environment/event_spec.json'})
pop=PopulationBundle(study_id='nju_compositional_simulation',provider_ref='nju.pop',materialized_count=30)
config=SimulationConfig(study_id='nju_compositional_simulation',n_steps=10,seed=7,decision_ref='nju.decision',collector_ref='nju.collector',interaction_rounds=1)
spec=StudySpec(study_id='nju_compositional_simulation',title='Calibrated Compositional Social Simulation',research_question='Can shared process and trajectory calibration transfer to independent events and unseen compositions?',hypothesis='Falsifiable; no assumed gain',n_steps=10,seed=7,time_unit='minute',step_meaning='One native logical minute, one outer round',metrics=['registered','waiting','attended'],legacy_simulator='njusim-contest native kernel (NOT original campus simulator)',provider_refs=['nju.env','nju.pop','nju.decision','nju.collector'],status='parity-tested-synthetic',resources_ref=None,run_note={'en':'Use scripts/verify_adapter.py; Path-C shared-session factory, not generic Path-B builder.'})
for rel,model in [('study.yaml',spec),('environment/environment.json',env),('population/population.json',pop),('simulation/simulation.json',config)]:write_json(study/rel,model.model_dump())
write_json(study/'environment/event_spec.json',asdict(scenario('S3')))
write_json(study/'trajectory/schema.json',dict(authoritative_replay='sidecar/trace.jsonl',panel='one agent per minute',microtrace_preserved=True,core_warm_start_supported=False))
write_json(folder/'adapter_validation.json',dict(upstream_commit='9c3ac774816511c121184ca11f539dc398ba1544',results=results,schemas_validated=True,full_original_baseline_reproduced=False))
print(json.dumps(results))
