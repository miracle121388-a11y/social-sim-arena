import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from njusim.legacy import load_sampler, frozen_choice
from njusim.io import write_json

direct = load_sampler()
count = 0
for seed in range(20):
    for agent in range(30):
        for probs in ({'a': .2, 'b': .8}, {'a': .1, 'b': .6, 'c': .3}):
            args = dict(seed=seed, agent_id=f'syn-{agent:02}', path='parity', occasion=3)
            assert direct(probs, **args) == frozen_choice(probs, **args)
            count += 1
result = dict(cases=count, passed=True, scope='Frozen sampling module vs pass-through seam only; full B0 NOT reproduced')
write_json('artifacts/legacy_parity.json', result)
print(json.dumps(result))
