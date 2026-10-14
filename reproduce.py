"""Offline, append-only reproduction driver for the frozen research package."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

if os.name != 'nt':
    raise SystemExit('The sealed workspace.py is Windows-specific. Use Windows Python with Git Bash/PowerShell; Linux is not validated.')

from workspace import ROOT, digest, path, save_json

EXPECTED_METHOD = 'b8389adc234ee11e923d59084eaeb83b3821986c5f2f714c9ad5a84ed14650af'


def verify_package():
    if digest('method.py') != EXPECTED_METHOD:
        raise RuntimeError('Frozen method bytes differ')
    manifest = path('PACKAGE_MANIFEST.json')
    if manifest.exists():
        for name, expected in json.loads(manifest.read_text(encoding='utf-8'))['sha256'].items():
            if digest(name) != expected:
                raise RuntimeError('Package file changed: '+name)
    import evaluate
    evaluate.verify_integrity()


def ensure_local_git():
    # An unpacked package might sit inside another repository. Give it its own
    # local receipt commit rather than accidentally recording the parent's HEAD.
    if path('.git').exists():
        top = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=ROOT, text=True).strip())
        if top.resolve() != ROOT:
            raise RuntimeError('Git root does not match package root')
        return
    subprocess.run(['git', 'init', '-b', 'codex/reproduction'], cwd=ROOT, check=True)
    subprocess.run(['git', 'add', '--', 'method.py', 'infrastructure.lock.json'], cwd=ROOT, check=True)
    subprocess.run(['git', '-c', 'user.name=Research reproduction', '-c',
                    'user.email=reproduction@example.invalid', 'commit', '-m',
                    'Local receipt of frozen method; original provenance bundled separately'], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--golden-only', action='store_true', help='Skip independent-world supplement')
    args = parser.parse_args()
    verify_package()
    ensure_local_git()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    log_dir = path('results/reproduce-'+stamp)
    log_dir.mkdir()
    records = []
    def command(arguments):
        proc = subprocess.run([sys.executable, '-B', *arguments], cwd=ROOT, text=True,
                              encoding='utf-8', errors='replace', capture_output=True,
                              env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1'})
        log = log_dir/(str(len(records)+1)+'.log')
        log.write_text(proc.stdout+proc.stderr, encoding='utf-8')
        records.append({'command': arguments, 'returncode': proc.returncode, 'log': str(log.relative_to(ROOT))})
        print(proc.stdout, end='', flush=True)
        if proc.returncode:
            print(proc.stderr, file=sys.stderr)
            raise RuntimeError('Reproduction command failed: '+' '.join(arguments))
        return proc.stdout
    try:
        command(['-m', 'unittest', 'discover', '-s', 'tests', '-v'])
        command(['evaluate.py', '--split', 'dev', '--mode', 'fast_dev'])
        output = command(['evaluate.py', '--split', 'test', '--mode', 'full_paper_ablation'])
        golden_result = next(line.split('|')[1].strip() for line in output.splitlines() if line.startswith('RESULT |'))
        command(['paper_artifacts.py', '--result', golden_result])
        if not args.golden_only:
            output = command(['closure_evaluate.py', '--result', golden_result])
            supplement = next(line.split('|')[1].strip() for line in output.splitlines() if line.startswith('SUPPLEMENT |'))
            command(['closure_artifacts.py', '--result', supplement])
        verify_package()
        state = 'passed'
    except Exception:
        state = 'failed'
        raise
    finally:
        save_json(str((log_dir/'receipt.json').relative_to(ROOT)),
                  {'status': state, 'method_sha256': digest('method.py'), 'steps': records,
                   'original_algorithm_commit': 'eb641c22eb197d038696894a5e6857d31002af78'})
    print('REPRODUCED | '+str(log_dir))


if __name__ == '__main__':
    main()
