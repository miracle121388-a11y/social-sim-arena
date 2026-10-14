# Standard V3 V0 research entry

This task initializes one prespecified V0; it does not start a search loop.
Read provenance/v3/protocol.md and configs/standard_v3.json before evaluation.
The only future evolvable algorithm is method.py. prepare_and_cache.py,
evaluate.py, workspace.py, tests and protocol are fixed by infrastructure.v3.lock.json.

Run the default prepare_and_cache.py once to replace the archived V1 root cache.
A second generation refuses to overwrite V3. The default evaluate.py runs five
matched-prior selectors with cost budgets [0,2,4,8,12,16]. Invalid calibration
or ESS<15 returns auc_error=999 before loading target outcomes. Full development
ablations additionally include NoBatch, NoProbes, evaluator-created MAP, and a
separate independently parameterized activity bank. MAP is diagnostic only;
NoSharing necessarily changes prior dependence and has a finite-particle limit.

Test is sealed. It requires explicit final-test authorization and an immutable
provenance/v3/test_release.json matching the method hash. Do not create that
release automatically, tune on test, or require a predetermined ranking. V0
performance and all negative or indistinguishable ablations must be reported.

V1/V2 history and old loop controllers are historical. Their infrastructure locks
must not be applied to the V3 branch. Their exact working release is available
from branch exp/v2-non-collapsed / commit dac68e8 and dist/v2-before-v3.zip.
No registration, upload, real student data, external APIs or paid model calls.
