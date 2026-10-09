"""Process-local defense in depth for the offline runner; not an OS sandbox."""
import os
from pathlib import Path
import sys
from .io import ROOT, safe_path

def install():
    def writable(p):
        if isinstance(p,int): return  # stdout/stderr and already-open descriptors
        dest=safe_path(os.fsdecode(p))
        if dest.is_relative_to(ROOT/'legacy_snapshot'):raise PermissionError('Frozen snapshot is read-only')
    def audit(event,args):
        if event=='open':
            path,mode,flags=args
            if (mode and any(x in mode for x in ('w','a','+','x'))) or (flags and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
                writable(path)
        elif event in ('os.mkdir','os.remove','os.rmdir'):writable(args[0])
        elif event in ('os.rename','os.replace'):writable(args[0]);writable(args[1])
        elif event in ('os.symlink','os.link'):raise PermissionError('Links forbidden')
        elif event.startswith('socket.') or event in ('subprocess.Popen','os.system'):
            raise PermissionError('Offline runner forbids network and subprocesses')
    sys.addaudithook(audit)
