# Arena v1 bounded AutoResearch protocol

Authorized by the user's 2026-10-15 request to execute the proposed optimization.
This protocol replaces the old synthetic five-gate search for this campaign only.
Previous sources and protocol are archived under provenance/arena_v1/previous.

## Frozen data and scope
Pinned public repository: e8d14d24f0bca7f05425afdbfd719eb38e17bed3.
Website snapshot: provenance/arena-data-20261015.json, generated 2026-10-14.
Only resolved scalar public-opinion and consumer rounds. Exclude missing locks,
flagged corrections, snapshot observations after lock, fewer than six history
points, history dates on/after lock, history/persistence mismatch, absent labels.
Exclusions depend on metadata/integrity, never forecast errors.
Train lock < 2026-08-25; dev < 2026-09-16; test >= 2026-09-16.
Already public outcomes and previously viewed leaderboard aggregates mean the
last split is a retrospective holdout, NOT a virgin/prospective test.

## Scientific objective and cost
Official normal CRPS, normalized by each round's pre-outcome persistence sd.
Primary: mean normalized CRPS, averaging within lock calendar week first.
Secondary: raw CRPS, mean official per-round skill, MAE, 80/95% interval coverage.
Maintain raw losses and denominators; never pool unrelated raw units as a claim.
Cost: number of rolling historical validation records evaluated over 24 fixed
experts. This is a cached computation budget, not paid information/web retrieval.
Forecast states exclude held-out outcomes. Only past historical calibration
targets can be revealed. CDF value assumes an expert-mixture binary model; after
proper-score updates and normal projection it is a heuristic, not exact VOI.
No claimed novel identity, first-vintage history or synthetic-to-real transfer.

## Finite search and decisions
24 method-only trials: 8 forecast/calibration priors, 8 acquisition policies,
8 robust updates/shrinkage/stopping candidates. All candidates are predeclared.
Stages 2 and 3 inherit the best dev configuration from the previous stage.
Incumbent starts with official persistence. KEEP iff primary dev loss improves
by > 1e-6, all outputs finite/positive sd, budgets respected, deterministic replay,
and no domain's normalized dev loss exceeds its persistence control by >50%.
No forced ablation ranking and no post-hoc selection thresholds.
No .git hard reset, no commits of unrelated user work. Each candidate source,
configuration, metrics and decision is append-only and hashed. Rejected sources
are retained for scientific reproducibility; only active method.py is restored.
Only method.py may change between infrastructure freeze and final evaluation.

## Freeze and verification
Lock adapter, evaluator, controller, tests, protocol, raw files and cache hashes.
After 24 trials freeze method and dev-selected baseline; evaluate test once,
including fixed strong baselines, ablations and 0/2/4/8/12 cost curves.
Seed 20261015; bootstrap 4000 whole calendar-week blocks; no individual
subgroup independence claim; few time blocks limit inference.
Post-freeze bug fixes must be disclosed; no test-guided method tuning.
Do not call paid models, register, deploy, publish or submit predictions.
Do not remove legacy, raw traces, failures, or provenance. Clean only audited
redundant generated outputs after a verified reproducibility archive exists.
