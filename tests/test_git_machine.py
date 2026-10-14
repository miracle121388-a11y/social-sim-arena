"""Exercise real Git transitions with a tiny deterministic evaluator fixture.

The fixture is ONLY a controller test, never recorded as a research result.
All test repositories and temporary files stay under the research workspace.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid
from workspace import path


class GitStateMachine(unittest.TestCase):
    def test_keep_discard_crash_and_rejected_commit_retention(self):
        root=path('.tmp/git-machine-'+uuid.uuid4().hex[:8]);root.mkdir()
        for name in ['workspace.py','autoresearch.py']:
            shutil.copyfile(path(name),root/name)
        (root/'method.py').write_text('score = 0.4\n',encoding='utf-8')
        (root/'.gitignore').write_text('.autoresearch/\nresults/\n.cache/\n.tmp/\n__pycache__/\n',encoding='utf-8')
        (root/'infrastructure.lock.json').write_text('{}',encoding='utf-8')
        fixture='''import json, uuid
from workspace import path, digest, save_json
def verify_integrity(): pass
if __name__ == '__main__':
    import method
    tag=uuid.uuid4().hex
    save_json('results/'+tag+'.json',{'run_id':tag,'auc_error':method.score,
              'method_sha256':digest('method.py'),'runtime_s':0.01})
'''
        (root/'evaluate.py').write_text(fixture,encoding='utf-8')
        def cmd(*args,okay=True):
            p=subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=30)
            if okay:self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            return p
        def git(*args):return cmd('git',*args).stdout.strip()
        git('init','-b','codex/controller-test')
        git('config','user.name','Local Controller Test')
        git('config','user.email','test@example.invalid')
        git('add','.');git('commit','-m','test fixture')
        baseline=git('rev-parse','HEAD')
        cmd(sys.executable,'-B','autoresearch.py','init')
        # Real commit followed by metric improvement: keep.
        (root/'method.py').write_text('score = 0.3\n',encoding='utf-8')
        cmd(sys.executable,'-B','autoresearch.py','trial','--description','controller keep test')
        accepted=git('rev-parse','HEAD');self.assertNotEqual(accepted,baseline)
        # Equal score must rewind the branch and restore just method.py.
        (root/'method.py').write_text('score = 0.3\n# equal metric\n',encoding='utf-8')
        cmd(sys.executable,'-B','autoresearch.py','trial','--description','controller discard test')
        self.assertEqual(git('rev-parse','HEAD'),accepted)
        self.assertEqual((root/'method.py').read_text(),'score = 0.3\n')
        # Crashed candidates also rewind, retaining the original commit and log.
        (root/'method.py').write_text('raise RuntimeError("intentional controller fixture crash")\n',encoding='utf-8')
        cmd(sys.executable,'-B','autoresearch.py','trial','--description','controller crash test')
        self.assertEqual(git('rev-parse','HEAD'),accepted)
        self.assertFalse(git('status','--porcelain'))
        refs=git('for-each-ref','--format=%(refname)','refs/autoresearch/rejected').splitlines()
        self.assertEqual(len(refs),2)
        state=json.loads((root/'.autoresearch/state.json').read_text())
        self.assertEqual(state['trials'],3);self.assertEqual(state['best_score'],.3)
        (root/'method.py').write_text('score = 0.2\n',encoding='utf-8')
        stopped=cmd(sys.executable,'-B','autoresearch.py','trial',okay=False)
        self.assertNotEqual(stopped.returncode,0)


if __name__=='__main__':unittest.main()
