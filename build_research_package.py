"""Allowlisted zip builder; never packages the original repository or secrets."""
import argparse
import hashlib
import json
import zipfile
from workspace import path, digest
from reproduce import verify_package


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='dist/njusim-frozen-research.zip')
    args = parser.parse_args()
    verify_package()
    files = set('README.md PAPER_METHOD_AND_INSIGHTS.md PAPER_TABLES.tex CLOSURE_PROTOCOL.md SOCIALSIM_INTEGRATION.md '
                'RESEARCH_REPORT_60.md method.py prepare_and_cache.py evaluate.py workspace.py '
                'autoresearch.py program.md paper_artifacts.py closure_evaluate.py closure_artifacts.py '
                'supplemental_rules.py reproduce.py reproduce_all.sh build_research_package.py '
                'requirements.txt requirements.lock.txt infrastructure.lock.json frozen_method.json '
                'data/rollout_cache.pt data/cache_manifest.json .gitattributes'.split())
    for folder in ['tests', 'src/njusim/adapters', 'provenance/campaign60',
                   'provenance/closure/candidates', 'provenance/closure/paper', 'provenance/closure/golden-paper']:
        for p in path(folder).rglob('*'):
            if p.is_file() and p.suffix != '.pyc':
                files.add(p.relative_to(path('.')).as_posix())
    for name in ['evolution-audit.json', 'experiments.tsv', 'git-log-method.txt', 'arena-sources.json',
                 'golden-test.json', 'supplement.json', 'verification.json', 'tooling-notes.json']:
        files.add('provenance/closure/'+name)
    golden = json.loads(path('provenance/closure/golden-test.json').read_text(encoding='utf-8'))
    supplement = json.loads(path('provenance/closure/supplement.json').read_text(encoding='utf-8'))
    files.update(['results/'+golden['run_id']+'.json', 'results/'+supplement['run_id']+'.json'])
    verification = json.loads(path('provenance/closure/verification.json').read_text(encoding='utf-8'))
    receipt = verification['reproduce_receipt'].replace('\\', '/')
    files.add(receipt)
    for step in verification['reproduce_steps']:
        files.add(step['log'].replace('\\', '/'))
    # All 60 actual evaluator outputs; rejected sources remain in candidates/.
    for line in path('provenance/campaign60/trials.jsonl').read_text(encoding='utf-8').splitlines():
        files.add(json.loads(line)['result'])
    # Source documents from third parties are linked/hash-pinned, not redistributed.
    manifest = {'schema': 1, 'status': 'tested_synthetic',
                'method_sha256': digest('method.py'),
                'original_algorithm_commit': 'eb641c22eb197d038696894a5e6857d31002af78',
                'sha256': {name: digest(name) for name in sorted(files)},
                'exclusions': ['legacy', 'source repository', 'environments', 'keys', 'third-party full documents'],
                'platform': 'Windows Python 3.13; Git for Windows Bash or PowerShell'}
    destination = path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(files):
            archive.write(path(name), name)
        archive.writestr('PACKAGE_MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    sha = hashlib.sha256(destination.read_bytes()).hexdigest()
    with path(args.output+'.sha256').open('x', encoding='utf-8') as f:
        f.write(sha+'  '+destination.name+'\n')
    print(json.dumps({'package': str(destination), 'sha256': sha, 'files': len(files)+1,
                      'size_mb': destination.stat().st_size/1e6}))


if __name__ == '__main__':
    main()
