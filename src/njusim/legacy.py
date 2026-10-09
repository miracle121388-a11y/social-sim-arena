"""Load only the two licensed frozen modules copied INSIDE this repository."""
import importlib.util
import sys
import types
from .io import ROOT

def load_sampler():
    for name in ('echo_swm', 'echo_swm.core', 'echo_swm.concordia_backend'):
        if name not in sys.modules:
            package = types.ModuleType(name); package.__path__ = []
            sys.modules[name] = package
    for name, relative in [('echo_swm.core.ids', 'core/ids.py'), ('echo_swm.concordia_backend.choice_sampling', 'concordia_backend/choice_sampling.py')]:
        path = ROOT / 'legacy_snapshot/src/echo_swm' / relative
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module; spec.loader.exec_module(module)
    return sys.modules['echo_swm.concordia_backend.choice_sampling'].sample_choice

_sample = load_sampler()

def frozen_choice(probabilities, *, seed, agent_id, path, occasion):
    return _sample(probabilities, seed=seed, agent_id=agent_id, path=path, occasion=occasion)
