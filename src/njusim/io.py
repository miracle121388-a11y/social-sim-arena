import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def safe_path(path):
    candidate = Path(path)
    if not candidate.is_absolute(): candidate = ROOT / candidate
    resolved = candidate.resolve()
    if not resolved.is_relative_to(ROOT): raise ValueError('Path outside research root')
    for p in (candidate, *candidate.parents):
        if p.exists() and (p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())):
            raise ValueError('Links/junctions forbidden')
        if p == ROOT: break
    if resolved.exists() and resolved.is_file() and resolved.stat().st_nlink > 1:
        raise ValueError('Hard-linked output forbidden')
    return resolved

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)

def sha(value): return hashlib.sha256(canonical(value).encode()).hexdigest()

def write_json(path, value):
    p = safe_path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

def read_json(path): return json.loads(safe_path(path).read_text(encoding='utf-8'))
