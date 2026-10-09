"""Entrypoint: python -I -B run.py smoke|pilot|all|test --batch NAME."""
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'src'))
for variable,relative in [('TMP', '.tmp'),('TEMP','.tmp'),('TMPDIR','.tmp'),('XDG_CACHE_HOME','.cache'),('PIP_CACHE_DIR','.cache/pip')]:
    os.environ[variable]=str(ROOT/relative)
os.environ['PYTHONDONTWRITEBYTECODE']='1'

def main():
    import argparse
    import datetime
    import json
    import platform
    import unittest
    from njusim.io import safe_path, write_json, read_json, sha
    from njusim.guard import install
    install()
    from njusim.experiments import smoke,research_pilot,append_registry
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['smoke','pilot','all','test','simulate','replay'])
    parser.add_argument('--batch',default=datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%S'))
    parser.add_argument('--config',default='configs/S3.json')
    parser.add_argument('--population',default='data/fixtures/personas.json')
    parser.add_argument('--backend',choices=['offline','statistical'],default='offline')
    parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--trace')
    args=parser.parse_args()
    if args.command=='test':
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        write_json('artifacts/tests-latest.json',dict(tests=result.testsRun,failures=[str(t) for t,_ in result.failures],errors=[str(t) for t,_ in result.errors],skipped=result.skipped,passed=result.wasSuccessful()))
        return 0 if result.wasSuccessful() else 1
    if args.command=='replay':
        from njusim.metrics import replay_trace,metrics
        if not args.trace:parser.error('--trace required')
        records=[json.loads(line) for line in safe_path(args.trace).read_text(encoding='utf-8').splitlines()]
        state=replay_trace(records)
        print(json.dumps({'verified':True,'records':len(records),'state_hash':sha(state),'metrics':metrics(records)},ensure_ascii=False))
        return 0
    folder=safe_path('artifacts')/args.batch
    folder=safe_path(folder);folder.mkdir(exist_ok=False)
    summary={}
    try:
        if args.command in ('smoke','all'):summary['smoke']=smoke(folder/'smoke')
        if args.command in ('pilot','all'):summary['pilot']=research_pilot(folder/'pilot')
        if args.command=='simulate':
            from njusim.contracts import EventSpec,Persona
            from njusim.kernel import Simulator
            from njusim.backends import OfflineFixtureBackend,SimpleStatisticalBackend
            from njusim.experiments import verify_replay
            event=EventSpec.from_dict(read_json(args.config))
            people=[Persona(**{**p,'contacts':tuple(p['contacts'])}) for p in read_json(args.population)]
            backend=OfflineFixtureBackend() if args.backend=='offline' else SimpleStatisticalBackend()
            sim=Simulator(event,people,backend,seed=args.seed,stream=f'{event.event_id}:rep-{args.seed}')
            sim.run();sim.save(folder/'simulation');summary['simulation']=verify_replay(sim)
        sources={str(p.relative_to(ROOT)):sha(p.read_text(encoding='utf-8')) for p in (ROOT/'src').rglob('*.py')}
        write_json(folder/'manifest.json',dict(batch=args.batch,python=platform.python_version(),dependencies='Python standard library only; copied legacy sampler has no third-party dependencies',source_hashes=sources,external_calls=0,cost_usd=0,summary=summary))
        append_registry(args.batch,args.command,summary)
        print(json.dumps({'batch':str(folder),'status':'tested_synthetic','summary':summary},ensure_ascii=False))
    except Exception as e:
        write_json(folder/'failure.json',dict(type=type(e).__name__,message=str(e),status='failed'))
        raise
    return 0

if __name__=='__main__':raise SystemExit(main())
