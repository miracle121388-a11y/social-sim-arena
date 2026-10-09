"""One-command offline study reproduction from the research root."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parents[2]/'scripts/verify_adapter.py'),run_name='__main__')
