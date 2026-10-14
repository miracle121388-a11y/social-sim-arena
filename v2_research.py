"""Finite, auditable Round-2 Git state machine. No external model service."""
import csv
import json
import re
import subprocess
import sys
import time
from workspace import path,digest,save_json,ROOT


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def evaluate(version='current',split='dev',mode='fast_dev'):
    cmd=[sys.executable,'-B','evaluate.py','--campaign','v2','--method-version',version,'--split',split,'--mode',mode]
    run=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
    if run.returncode:raise RuntimeError(run.stdout)
    match=re.search(r'^RESULT \| (.+)$',run.stdout,re.M)
    if not match:raise RuntimeError(run.stdout)
    filename=match.group(1).strip();obj=json.loads(path(filename).read_text())
    return filename,obj,run.stdout


def record(row):
    p=path('experiments_v2.tsv');exists=p.exists()
    with p.open('a',encoding='utf-8',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(row),delimiter='\t')
        if not exists:wr.writeheader()
        wr.writerow(row)
    # Append canonical minimal rows; existing V1 entries are never rewritten.
    with path('experiments.tsv').open('a',encoding='utf-8',newline='') as f:
        csv.writer(f,delimiter='\t').writerow([row['trial'],row['commit'],row['method_sha256'],'dev','fast_dev',row['auc'],row['runtime_s'],row['status'],row['result']])


def main():
    if git('branch','--show-current')!='exp/v2-non-collapsed':raise RuntimeError('Wrong research branch')
    if git('status','--porcelain','--untracked-files=no'):raise RuntimeError('Commit infrastructure before starting')
    if path('provenance/v2/frozen.json').exists():raise RuntimeError('Campaign is already frozen')
    if path('experiments_v2.tsv').exists():raise RuntimeError('Do not overwrite or restart a campaign')
    from v2_evaluation import verify
    verify()
    baseline_file,baseline,stdout=evaluate('v1')
    save_json('provenance/v2/baseline.json',{'result':baseline_file,**baseline})
    print('V1 BASELINE '+stdout,flush=True)
    best=baseline['auc_error'];kept=0;valid=0
    plan=json.loads(path('configs/v2_trials.json').read_text())
    v1=path('provenance/v2/v1_snapshot/method.py').read_text(encoding='utf-8')
    body=path('configs/v2_method_body.txt').read_text(encoding='utf-8')
    for trial in plan:
        base=git('rev-parse','HEAD');n=trial['round'];tag=f'V2-R{n:02d}'
        save_json('provenance/v2/'+tag+'-hypothesis.json',{'parent':base,**trial})
        path('method.py').write_text(v1+'\nV2_CONFIG = '+repr(trial['config'])+'\n'+body,encoding='utf-8',newline='\n')
        git('add','method.py');git('commit','-m',tag+': '+trial['hypothesis'])
        candidate=git('rev-parse','HEAD');mh=digest('method.py')
        filename='';result={};status='ERROR';reason='';started=time.perf_counter()
        try:
            filename,result,stdout=evaluate();valid+=1
            keep=result['eligible'] and result['auc_error']<best-1e-8
            status='KEEP' if keep else 'REVERT'
            reason='passed all guards and improved incumbent' if keep else 'guard failure or no AUC improvement'
            if keep:best=result['auc_error'];kept+=1
            print(tag+' '+status+' '+stdout,flush=True)
        except Exception as exc:
            reason=str(exc);print(tag+' ERROR '+reason,flush=True)
            save_json('provenance/v2/'+tag+'-error.json',{'error':reason})
        row={'trial':tag,'commit':candidate,'parent':base,'method_sha256':mh,'hypothesis':trial['hypothesis'],
             'status':status,'auc':result.get('auc_error',''),'ess':result.get('initial_ess',''),
             'runtime_s':result.get('runtime_s',time.perf_counter()-started),
             'guards':json.dumps(result.get('guards',{})),'result':filename,'reason':reason}
        record(row);save_json('provenance/v2/'+tag+'-decision.json',row)
        if status!='KEEP':
            git('update-ref','refs/autoresearch-v2/rejected/'+tag,candidate)
            git('restore','--source',base,'--staged','--worktree','--','method.py')
            git('reset','--soft',base)
        if status=='ERROR':raise RuntimeError('Infrastructure error recorded; stop for diagnosis without changing frozen criteria')
    if valid!=30:raise RuntimeError('Campaign has fewer than 30 valid experiments')
    verify()
    save_json('provenance/v2/frozen.json',{'method_sha256':digest('method.py'),'commit':git('rev-parse','HEAD'),
              'valid_trials':valid,'keeps':kept,'eligible_winner':kept>0,'best_dev_auc':best,
              'baseline_result':baseline_file,'infrastructure_sha256':digest('infrastructure.v2.lock.json')})
    print('FROZEN '+json.dumps(json.loads(path('provenance/v2/frozen.json').read_text())),flush=True)


if __name__=='__main__':main()
