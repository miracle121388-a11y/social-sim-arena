"""Compile the full Chinese translation with XeLaTeX, preserving the English paper."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workspace import path,digest
import os,re,json,shutil,subprocess

for directory in ['.cache/texlive/var','.cache/texlive/config','.tmp/paper-build-zh','paper/qa/zh']:
    path(directory).mkdir(parents=True,exist_ok=True)
env=os.environ.copy()
env.update(TEXMFVAR=str(path('.cache/texlive/var')),TEXMFCONFIG=str(path('.cache/texlive/config')),
           TEMP=str(path('.tmp/paper-build-zh')),TMP=str(path('.tmp/paper-build-zh')),
           SOURCE_DATE_EPOCH='1791936000',FORCE_SOURCE_DATE='1')
engine=shutil.which('xelatex');bib=shutil.which('bibtex')
if not engine or not bib:raise SystemExit('XeLaTeX and BibTeX are required.')
before={n:digest(n) for n in ['method.py','paper/main.tex','paper/main.pdf','PAPER_TABLES.tex']}
for p in path('paper').rglob('*'):path(p.relative_to(path('')))
for suffix in ['pdf','aux','log','out','bbl','blg']:
    path('paper/main_zh.'+suffix)
commands=[[engine,'-no-shell-escape','-interaction=nonstopmode','-halt-on-error','main_zh.tex'],
          [bib,'main_zh'],
          [engine,'-no-shell-escape','-interaction=nonstopmode','-halt-on-error','main_zh.tex'],
          [engine,'-no-shell-escape','-interaction=nonstopmode','-halt-on-error','main_zh.tex']]
for i,cmd in enumerate(commands):
    result=subprocess.run(cmd,cwd=path('paper'),env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    out=result.stdout.decode('utf-8',errors='replace')
    path(f'paper/qa/zh/build-pass-{i+1}.txt').write_text(out,encoding='utf-8')
    if result.returncode:
        print(out[-6000:]);raise SystemExit(result.returncode)
log=path('paper/main_zh.log').read_text(encoding='utf-8',errors='replace')
issues=[line for line in log.splitlines() if re.search(r'Warning|Overfull|Underfull|undefined|Missing character',line)]
biblog=path('paper/main_zh.blg').read_text(encoding='utf-8',errors='replace')
issues += [line for line in biblog.splitlines() if 'Warning--' in line or 'error message' in line]
for n,h in before.items():assert digest(n)==h,n
report={'compiler':engine,'pdf_sha256':digest('paper/main_zh.pdf'),'preserved':before,
        'remaining_diagnostics':issues,'passes':4,'pdf_bytes':path('paper/main_zh.pdf').stat().st_size}
path('paper/qa/zh/compilation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
if issues:raise SystemExit('Compilation completed; inspect diagnostics.')
