"""Fixed Git state machine: init -> commit candidate -> evaluate -> keep/discard.

An external coding agent proposes edits to method.py, as in Karpathy's paradigm.
This controller does not invent hypotheses or call a paid LLM. Local hashes are
tamper evidence, not protection against malicious Python with filesystem access.
"""
import argparse
import csv
import json
import math
import subprocess
import sys
import time
import uuid
from workspace import ROOT, path, digest, save_json


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def write_state(value):
    p=path('.autoresearch/state.json')
    p.write_text(json.dumps(value,indent=2),encoding='utf-8')


def check_clean(allow_method=False):
    changes=set(git('diff','HEAD','--name-only').splitlines())
    if changes - ({'method.py'} if allow_method else set()):
        raise RuntimeError('Unrelated tracked changes: '+repr(changes))
    if git('diff','--cached','--name-only'):
        raise RuntimeError('Index must be empty before starting a trial')
    if git('ls-files','--others','--exclude-standard'):
        raise RuntimeError('Untracked non-output files must be handled before a campaign')
    if not git('branch','--show-current').startswith('codex/'):
        raise RuntimeError('Use a dedicated codex/ research branch')


def evaluate(tag):
    log=path('.autoresearch/'+tag+'.log')
    before=set(path('results').glob('*.json'))
    started=time.perf_counter()
    with log.open('x',encoding='utf-8') as output:
        completed=subprocess.run([sys.executable,'-B','evaluate.py','--split','dev','--mode','fast_dev'],
                                 cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,timeout=30)
    if completed.returncode:
        raise RuntimeError(f'Evaluation failed; inspect {log.name}')
    new=set(path('results').glob('*.json'))-before
    if len(new)!=1:raise RuntimeError('Expected one new evaluation record')
    result=json.loads(new.pop().read_text(encoding='utf-8'))
    score=result['auc_error']
    if not math.isfinite(score):raise RuntimeError('Nonfinite metric')
    if result['runtime_s']>15:raise RuntimeError('fast_dev exceeded frozen 15-second budget')
    from evaluate import verify_integrity
    verify_integrity()
    if result['method_sha256']!=digest('method.py'):
        raise RuntimeError('Method hash changed during evaluation')
    return result,time.perf_counter()-started


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['freeze-infrastructure','init','trial','freeze-test','status'])
    parser.add_argument('--description',default='baseline v0')
    args=parser.parse_args()
    path('.autoresearch').mkdir(exist_ok=True)
    if args.action=='freeze-infrastructure':
        from evaluate import FIXED_FILES
        save_json('infrastructure.lock.json',{name:digest(name) for name in FIXED_FILES})
        print('Infrastructure frozen. Commit this lock with the baseline.');return
    from evaluate import verify_integrity
    verify_integrity()
    if not path('infrastructure.lock.json').exists():raise RuntimeError('Freeze infrastructure first')
    if args.action=='init':
        check_clean()
        if path('.autoresearch/state.json').exists():raise FileExistsError('Already initialized')
        result,wall=evaluate('baseline-'+uuid.uuid4().hex[:8])
        state={'best_commit':git('rev-parse','HEAD'),'best_score':result['auc_error'],
               'best_method_sha256':digest('method.py'),'baseline_result':result['run_id'],
               'trials':0,'max_trials':3,'consecutive_failures':0,'total_wall_s':wall,'max_wall_s':2700}
        write_state(state);print(json.dumps(state,indent=2));return
    state=json.loads(path('.autoresearch/state.json').read_text())
    if args.action=='status':print(json.dumps(state,indent=2));return
    if args.action=='freeze-test':
        check_clean()
        if digest('method.py')!=state['best_method_sha256'] or git('rev-parse','HEAD')!=state['best_commit']:
            raise RuntimeError('Current method is not accepted development winner')
        save_json('frozen_method.json',{'method_sha256':digest('method.py'),'commit':state['best_commit'],
                                     'development_score':state['best_score']})
        print('Test method frozen; no more development edits in this campaign.');return
    if path('frozen_method.json').exists():raise RuntimeError('Campaign frozen for test')
    check_clean(allow_method=True)
    if git('rev-parse','HEAD')!=state['best_commit']:raise RuntimeError('HEAD differs from accepted state')
    if state['trials']>=state['max_trials'] or state['consecutive_failures']>=2 or state['total_wall_s']>=state['max_wall_s']:
        raise RuntimeError('Campaign stop condition reached')
    if git('diff','HEAD','--name-only')!='method.py':raise RuntimeError('Edit only method.py before trial')
    base=state['best_commit'];tag='trial-'+uuid.uuid4().hex[:12]
    git('add','--','method.py');git('commit','-m',args.description)
    candidate=git('rev-parse','HEAD');score=None;error='';started=time.perf_counter()
    # Write recoverable intent before evaluation. A killed controller never loses
    # the base/candidate identity, and rejected commits remain reachable by refs.
    save_json('.autoresearch/'+tag+'-pending.json',{'base':base,'candidate':candidate})
    try:
        result,_=evaluate(tag);score=result['auc_error']
        status='keep' if score<state['best_score']-1e-8 else 'discard'
        state['consecutive_failures']=0
    except Exception as exc:
        status='crash';error=str(exc);state['consecutive_failures']+=1
    wall=time.perf_counter()-started
    row={'trial':tag,'commit':candidate,'base':base,'score':score,'status':status,'error':error,'wall_s':wall}
    save_json('.autoresearch/'+tag+'.json',row)
    if status=='keep':
        state.update(best_commit=candidate,best_score=score,best_method_sha256=digest('method.py'))
    else:
        git('update-ref','refs/autoresearch/rejected/'+tag,candidate)
        # Restore ONLY the permitted algorithm file, then rewind our own commit.
        # Refuse broad reset --hard, which could erase unrelated user edits.
        if set(git('diff','HEAD','--name-only').splitlines())-{'method.py'}:
            raise RuntimeError('Unexpected concurrent changes; leave pending record for recovery')
        git('restore','--source',base,'--staged','--worktree','--','method.py')
        git('reset','--soft',base)
    state['trials']+=1;state['total_wall_s']+=wall;write_state(state)
    print(json.dumps(row,indent=2))


if __name__=='__main__':main()
