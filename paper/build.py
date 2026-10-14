"""Build the multi-file paper with local TeX; keep all outputs in the workspace."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workspace import path, digest
import os
import re
import json
import shutil
import subprocess

root=path('')
paper=path('paper')
for folder in ['.cache/texlive/var','.cache/texlive/config','.tmp/paper-build','paper/qa']:
    path(folder).mkdir(parents=True,exist_ok=True)
env=os.environ.copy()
env.update(TEXMFVAR=str(path('.cache/texlive/var')),TEXMFCONFIG=str(path('.cache/texlive/config')),
           TEMP=str(path('.tmp/paper-build')),TMP=str(path('.tmp/paper-build')),
           SOURCE_DATE_EPOCH='1791936000',FORCE_SOURCE_DATE='1')
engine=shutil.which('pdflatex')
bib=shutil.which('bibtex')
if not engine or not bib:
    raise SystemExit('Install a local TeX distribution providing pdflatex and bibtex.')
before=digest('method.py')
# Reject existing links, including output files TeX will overwrite.
for p in paper.rglob('*'):
    path(p.relative_to(root))
for name in ['main.pdf','main.aux','main.bbl','main.blg','main.log','main.out']:
    path('paper/'+name)
commands=[[engine,'-no-shell-escape','-interaction=nonstopmode','-halt-on-error','main.tex'],
          [bib,'main'],
          [engine,'-no-shell-escape','-interaction=nonstopmode','-halt-on-error','main.tex'],
          [engine,'-no-shell-escape','-interaction=nonstopmode','-halt-on-error','main.tex']]
for i,cmd in enumerate(commands):
    result=subprocess.run(cmd,cwd=paper,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log=result.stdout.decode('utf-8',errors='replace')
    path(f'paper/qa/build-pass-{i+1}.txt').write_text(log,encoding='utf-8')
    if result.returncode:
        print(log[-6000:])
        raise SystemExit(result.returncode)
log=path('paper/main.log').read_text(encoding='utf-8',errors='replace')
issues=[line for line in log.splitlines() if re.search(r'Warning|Overfull|Underfull|undefined|Missing character',line)]
biblog=path('paper/main.blg').read_text(encoding='utf-8',errors='replace')
issues += [line for line in biblog.splitlines() if 'Warning--' in line or 'error message' in line]
assert before==digest('method.py')
report={'compiler':engine,'pdf_sha256':digest('paper/main.pdf'),'method_unchanged':True,
        'remaining_diagnostics':issues,'passes':len(commands),'pdf_bytes':path('paper/main.pdf').stat().st_size}
path('paper/qa/compilation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
if issues:
    raise SystemExit('PDF built, but diagnostics require review.')
