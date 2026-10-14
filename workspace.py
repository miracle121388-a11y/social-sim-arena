"""Fixed local paths and auditable writes; not an OS security sandbox."""
from pathlib import Path
import hashlib
import json
import os
import stat

ROOT = Path(__file__).resolve().parent


def path(name):
    p = ROOT / name
    if not p.resolve().is_relative_to(ROOT):
        raise ValueError('Path outside research workspace')
    for part in (p, *p.parents):
        if part.exists():
            s = part.lstat()
            if s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError(f'Link/junction rejected: {part}')
            if part.is_file() and s.st_nlink != 1:
                raise ValueError(f'Hard link rejected: {part}')
        if part == ROOT:
            break
    return p


def configure():
    for name in ('.tmp', '.cache', '.cache/matplotlib', 'results', 'data'):
        path(name).mkdir(parents=True, exist_ok=True)
    os.environ['TEMP'] = os.environ['TMP'] = str(path('.tmp'))
    os.environ['MPLCONFIGDIR'] = str(path('.cache/matplotlib'))
    os.environ['TORCH_HOME'] = str(path('.cache/torch'))
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


def digest(name):
    h = hashlib.sha256()
    with path(name).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save_json(name, value):
    with path(name).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


configure()
