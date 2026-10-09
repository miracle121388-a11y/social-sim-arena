"""Read-only source audit. Never imports or executes source-project code."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'NJU-xianlinSWM'
EXCLUDE = {'.git', 'node_modules', '__pycache__', 'venv', 'site-packages', 'data',
           'artifacts', 'models', 'photos', 'output', 'tmp', 'vendor'}
EXTENSIONS = {'.py', '.ts', '.tsx', '.mjs', '.md', '.toml', '.yml', '.yaml', '.css', '.jinja2', '.txt'}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def capture():
    assert ROOT.parent == SOURCE.resolve().parent and not ROOT.is_relative_to(SOURCE.resolve())
    for p in (ROOT, SOURCE, *ROOT.parents):
        assert not p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, str(p)
    hashes, metadata, links, repos = {}, {}, [], []
    for base, dirs, files in os.walk(SOURCE, followlinks=False):
        for n in dirs[:]:
            p = Path(base) / n
            if p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                links.append(str(p.relative_to(SOURCE))); dirs.remove(n)
            elif n == '.git':
                repos.append(str(p.relative_to(SOURCE))); dirs.remove(n)
            elif n.startswith('.') or n in EXCLUDE:
                dirs.remove(n)
        for n in files:
            p = Path(base) / n
            rel = p.relative_to(SOURCE).as_posix()
            if p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                links.append(rel); continue
            st = p.stat()
            metadata[rel] = {'size': st.st_size, 'mtime_ns': st.st_mtime_ns}
            if p.suffix.lower() in EXTENSIONS and not any(w in rel.lower() for w in ('.env', 'secret', 'credential')) and st.st_size < 2_000_000:
                hashes[rel] = digest(p)
    env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}
    def git(*args):
        return subprocess.check_output(['git', '-c', 'core.fsmonitor=false', '-C', str(SOURCE), *args], env=env, text=True)
    controls = {}
    for rel in ('.git/HEAD', '.git/index', '.git/packed-refs'):
        if (SOURCE / rel).is_file(): controls[rel] = digest(SOURCE / rel)
    for p in (SOURCE / '.git/refs').rglob('*'):
        if p.is_file(): controls[p.relative_to(SOURCE).as_posix()] = digest(p)
    return dict(source_root=str(SOURCE.resolve()), research_root=str(ROOT), source_head=git('rev-parse', 'HEAD').strip(),
                git_status=git('status', '--porcelain=v1', '-uall'), controlled_hashes=hashes,
                file_metadata=metadata, git_control_hashes=controls, reparse_points=links, git_entries=repos,
                limitations='No OS ACL changed. Text hashes exclude secrets, data, DBs, assets, caches, dependencies, hidden subtrees and files >=2MB. Metadata not content proof. Nested Git/link search uses same exclusions. Git objects/config not read. No source imports/execution.')

if __name__ == '__main__':
    now = capture()
    initial = ROOT / 'provenance/source_manifest.json'
    if sys.argv[1:] == ['initial']:
        with initial.open('x', encoding='utf-8') as f: json.dump(now, f, ensure_ascii=False, indent=2)
        print(json.dumps({'controlled_files': len(now['controlled_hashes']), 'metadata_files': len(now['file_metadata']), 'links': now['reparse_points'], 'git_entries': now['git_entries']}))
    else:
        old = json.loads(initial.read_text(encoding='utf-8'))
        delta = {}
        for key in ('source_head', 'git_status', 'controlled_hashes', 'file_metadata', 'git_control_hashes', 'reparse_points', 'git_entries'):
            if now[key] != old[key]:
                delta[key] = ([p for p in set(old[key]) | set(now[key]) if old[key].get(p) != now[key].get(p)] if isinstance(now[key], dict) else 'changed')
        result = dict(unchanged_within_scope=not delta, differences=delta, controlled_file_count=len(now['controlled_hashes']), limitations=now['limitations'])
        path = ROOT / 'provenance/isolation_checks' / (sys.argv[1] if len(sys.argv)>1 else 'latest.json')
        assert path.resolve().is_relative_to(ROOT)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(bool(delta))
